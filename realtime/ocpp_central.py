"""
realtime/ocpp_central.py  —  OCPP 1.6J WebSocket Central System.

v2.2.1 fix
----------
BUG 12 FIXED: asyncio.get_event_loop() is deprecated in Python 3.10+
  and raises DeprecationWarning in 3.12. Inside an async context the
  correct call is asyncio.get_running_loop().
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ocpp.central")

HOST       = "0.0.0.0"
PORT       = int(os.environ.get("OCPP_PORT", 9000))
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
DATASET    = os.environ.get("BIGQUERY_DATASET", "ev_advisor_core")

_bq_client = None


def _get_bq():
    global _bq_client
    if _bq_client is not None:
        return _bq_client
    try:
        from google.cloud import bigquery
        if PROJECT_ID:
            _bq_client = bigquery.Client(project=PROJECT_ID)
            logger.info("BigQuery client initialised (project=%s)", PROJECT_ID)
    except Exception as e:
        logger.warning("BigQuery unavailable: %s — events logged only", e)
    return _bq_client


def _bq_insert(table: str, rows: list) -> None:
    """Blocking BQ insert — called from executor thread."""
    client = _get_bq()
    if not client:
        return
    try:
        errors = client.insert_rows_json(f"{PROJECT_ID}.{DATASET}.{table}", rows)
        if errors:
            logger.warning("BQ insert errors on %s: %s", table, errors)
    except Exception as e:
        logger.warning("BQ insert failed on %s: %s", table, e)


# ── BUG 12 FIX: use get_running_loop() inside async context ──────────────────
def _fire_and_forget(table: str, rows: list) -> None:
    """Schedule a non-blocking BQ insert without blocking the WebSocket loop."""
    try:
        loop = asyncio.get_running_loop()          # ← FIXED (was get_event_loop)
        loop.run_in_executor(None, _bq_insert, table, rows)
    except RuntimeError:
        # No running loop (e.g. called from a test context) — skip silently
        pass


# ── OCPP message handlers ─────────────────────────────────────────────────────

async def handle_boot_notification(station_id: str, payload: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    logger.info("[%s] BootNotification: model=%s", station_id,
                payload.get("chargePointModel", "?"))
    _fire_and_forget("charger_events", [{
        "event_id":   str(uuid.uuid4()),
        "station_id": station_id,
        "port_id":    "0",
        "event_type": "BootNotification",
        "status":     "Online",
        "error_code": None,
        "timestamp":  now,
    }])
    return {"currentTime": now, "interval": 30, "status": "Accepted"}


async def handle_heartbeat(station_id: str) -> dict:
    logger.debug("[%s] Heartbeat", station_id)
    return {"currentTime": datetime.now(timezone.utc).isoformat()}


async def handle_status_notification(station_id: str, payload: dict) -> dict:
    connector_id = str(payload.get("connectorId", "1"))
    status       = payload.get("status", "Available")
    error_code   = payload.get("errorCode", "NoError")
    now          = datetime.now(timezone.utc).isoformat()
    logger.info("[%s] Port %s → %s (err=%s)", station_id, connector_id, status, error_code)

    _fire_and_forget("charger_events", [{
        "event_id":   str(uuid.uuid4()),
        "station_id": station_id,
        "port_id":    connector_id,
        "event_type": "StatusNotification",
        "status":     status,
        "error_code": error_code if error_code != "NoError" else None,
        "timestamp":  now,
    }])
    _fire_and_forget("live_port_status", [{
        "station_id":    station_id,
        "port_id":       connector_id,
        "status":        status,
        "last_updated":  now,
        "session_id":    None,
        "session_start": None,
    }])
    return {}


async def handle_start_transaction(station_id: str, payload: dict) -> dict:
    connector_id = str(payload.get("connectorId", "1"))
    session_id   = str(uuid.uuid4())
    now          = datetime.now(timezone.utc).isoformat()
    logger.info("[%s] StartTransaction port=%s session=%s",
                station_id, connector_id, session_id[:8])

    _fire_and_forget("charger_events", [{
        "event_id":   str(uuid.uuid4()),
        "station_id": station_id,
        "port_id":    connector_id,
        "event_type": "StartTransaction",
        "status":     "Charging",
        "error_code": None,
        "timestamp":  now,
    }])
    _fire_and_forget("live_port_status", [{
        "station_id":    station_id,
        "port_id":       connector_id,
        "status":        "Charging",
        "last_updated":  now,
        "session_id":    session_id,
        "session_start": now,
    }])
    return {"transactionId": session_id, "idTagInfo": {"status": "Accepted"}}


async def handle_stop_transaction(station_id: str, payload: dict) -> dict:
    session_id   = str(payload.get("transactionId", str(uuid.uuid4())))
    meter_stop   = payload.get("meterStop", 0)
    meter_start  = payload.get("meterStart", 0)
    energy_kwh   = round((meter_stop - meter_start) / 1000, 3)
    connector_id = str(payload.get("connectorId", "1"))
    start_ts     = str(payload.get("startTime", ""))
    now          = datetime.now(timezone.utc).isoformat()
    logger.info("[%s] StopTransaction session=%s energy=%.2f kWh",
                station_id, session_id[:8], energy_kwh)

    # Compute duration safely
    try:
        start_dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00"))
        end_dt   = datetime.fromisoformat(now.replace("Z", "+00:00"))
        dur_min  = max(0, round((end_dt - start_dt).total_seconds() / 60))
    except (ValueError, TypeError):
        dur_min = 0

    _fire_and_forget("session_history", [{
        "session_id":       session_id,
        "station_id":       station_id,
        "port_id":          connector_id,
        "start_time":       start_ts or now,
        "end_time":         now,
        "energy_kwh":       energy_kwh,
        "duration_minutes": dur_min,
    }])
    _fire_and_forget("live_port_status", [{
        "station_id":    station_id,
        "port_id":       connector_id,
        "status":        "Available",
        "last_updated":  now,
        "session_id":    None,
        "session_start": None,
    }])
    return {"idTagInfo": {"status": "Accepted"}}


# ── Message dispatcher ────────────────────────────────────────────────────────

HANDLERS = {
    "BootNotification":   handle_boot_notification,
    "Heartbeat":          lambda sid, _: handle_heartbeat(sid),
    "StatusNotification": handle_status_notification,
    "StartTransaction":   handle_start_transaction,
    "StopTransaction":    handle_stop_transaction,
}


async def charger_handler(websocket: WebSocketServerProtocol, path: str) -> None:
    station_id = path.strip("/").split("/")[-1] or "UNKNOWN"
    logger.info("Charger connected: %s (path=%s)", station_id, path)

    try:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("[%s] Bad JSON: %s", station_id, raw[:80])
                continue

            if not isinstance(msg, list) or len(msg) < 3 or msg[0] != 2:
                continue

            unique_id = msg[1]
            action    = msg[2]
            payload   = msg[3] if len(msg) > 3 else {}
            handler   = HANDLERS.get(action)

            if handler:
                try:
                    result   = await handler(station_id, payload)
                    response = json.dumps([3, unique_id, result])
                except Exception as e:
                    logger.exception("[%s] Handler error for %s: %s",
                                     station_id, action, e)
                    response = json.dumps(
                        [4, unique_id, "InternalError", str(e), {}]
                    )
            else:
                logger.warning("[%s] Unknown action: %s", station_id, action)
                response = json.dumps(
                    [4, unique_id, "NotImplemented", action, {}]
                )

            await websocket.send(response)

    except websockets.exceptions.ConnectionClosedOK:
        logger.info("Charger disconnected cleanly: %s", station_id)
    except websockets.exceptions.ConnectionClosedError as e:
        logger.warning("Charger connection error [%s]: %s", station_id, e)
    except Exception as e:
        logger.exception("Unexpected error for charger %s: %s", station_id, e)


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    logger.info("OCPP Central System starting on ws://%s:%d", HOST, PORT)
    logger.info("BigQuery dataset: %s", DATASET)
    async with websockets.serve(
        charger_handler,
        HOST,
        PORT,
        subprotocols=["ocpp1.6"],
        ping_interval=30,
        ping_timeout=10,
    ):
        logger.info("OCPP Central System ready — waiting for charger connections")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())