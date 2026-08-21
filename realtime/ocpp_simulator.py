"""
realtime/ocpp_simulator.py  —  OCPP 1.6J charger event stream simulator.

Simulates realistic EV charging sessions using a non-homogeneous Poisson
process (thinning method) matching the NREL 2022 diurnal demand curve.

Run standalone:
  python -m realtime.ocpp_simulator
"""

import asyncio
import json
import logging
import math
import os
import random
import uuid
from datetime import datetime, timezone

import websockets

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ocpp.simulator")

OCPP_WS_URL = os.environ.get("OCPP_WS_URL", "ws://localhost:9000")

STATIONS = [
    {"id": "ST001", "ports": 8,  "kw": 150, "zip": "94102", "name": "Mission DC Fast"},
    {"id": "ST002", "ports": 12, "kw": 250, "zip": "94103", "name": "SoMa Supercharge"},
    {"id": "ST003", "ports": 6,  "kw": 22,  "zip": "94107", "name": "Civic Level 2"},
    {"id": "ST004", "ports": 4,  "kw": 100, "zip": "94110", "name": "Castro EV Hub"},
    {"id": "ST005", "ports": 6,  "kw": 150, "zip": "94107", "name": "Dogpatch Rapid"},
    {"id": "ST006", "ports": 3,  "kw": 22,  "zip": "94114", "name": "Potrero L2"},
]

_ARRIVAL_RATE_BY_HOUR = {
     0: 0.5,  1: 0.3,  2: 0.2,  3: 0.2,  4: 0.3,  5: 0.7,
     6: 1.7,  7: 3.3,  8: 4.9,  9: 4.7, 10: 4.3, 11: 4.1,
    12: 4.5, 13: 4.3, 14: 3.9, 15: 3.6, 16: 4.3, 17: 5.3,
    18: 5.5, 19: 5.1, 20: 4.2, 21: 3.1, 22: 1.8, 23: 0.9,
}
_MAX_RATE = max(_ARRIVAL_RATE_BY_HOUR.values())


def _session_duration_minutes(power_kw: float) -> float:
    mean_min = max(15, 90 - power_kw * 0.4)
    return max(5.0, min(180.0, random.expovariate(1 / mean_min)))


class ChargerSimulator:
    def __init__(self, station: dict):
        self.station_id = station["id"]
        self.num_ports  = station["ports"]
        self.power_kw   = station["kw"]
        self._call_id   = 0

    def _next_call_id(self) -> str:
        self._call_id += 1
        return f"{self.station_id}-{self._call_id}"

    async def _send(self, ws, action: str, payload: dict) -> dict:
        call_id = self._next_call_id()
        await ws.send(json.dumps([2, call_id, action, payload]))
        raw  = await ws.recv()
        resp = json.loads(raw)
        return resp[2] if resp[0] == 3 else {}

    async def run(self) -> None:
        url = f"{OCPP_WS_URL}/{self.station_id}"
        while True:
            try:
                async with websockets.connect(
                    url, subprotocols=["ocpp1.6"],
                    ping_interval=25, ping_timeout=10,
                ) as ws:
                    logger.info("[%s] Connected", self.station_id)
                    await self._boot(ws)
                    await self._run_session_loop(ws)
            except (websockets.exceptions.ConnectionClosed, OSError) as e:
                logger.warning("[%s] Disconnected: %s — retrying in 5s", self.station_id, e)
                await asyncio.sleep(5)

    async def _boot(self, ws) -> None:
        await self._send(ws, "BootNotification", {
            "chargePointVendor": "EVAdvisorSim",
            "chargePointModel":  f"Sim-{self.power_kw}kW",
            "firmwareVersion":   "1.0.0",
        })
        for port in range(1, self.num_ports + 1):
            await self._send(ws, "StatusNotification", {
                "connectorId": port, "status": "Available",
                "errorCode": "NoError",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    async def _run_session_loop(self, ws) -> None:
        tasks = [
            asyncio.create_task(self._port_loop(ws, p))
            for p in range(1, self.num_ports + 1)
        ]
        await asyncio.gather(*tasks)

    async def _port_loop(self, ws, port_id: int) -> None:
        while True:
            inter_arrival = random.expovariate(_MAX_RATE)
            await asyncio.sleep(inter_arrival * 60)
            hour = datetime.now(timezone.utc).hour
            if random.random() > _ARRIVAL_RATE_BY_HOUR.get(hour, 1.0) / _MAX_RATE:
                continue
            await self._simulate_session(ws, port_id)

    async def _simulate_session(self, ws, port_id: int) -> None:
        duration_min = _session_duration_minutes(self.power_kw)
        meter_start  = random.randint(0, 50_000)
        meter_end    = meter_start + int(self.power_kw * (duration_min / 60) * 0.92 * 1000)
        start_time   = datetime.now(timezone.utc).isoformat()
        try:
            await self._send(ws, "StatusNotification", {
                "connectorId": port_id, "status": "Preparing",
                "errorCode": "NoError", "timestamp": start_time,
            })
            result = await self._send(ws, "StartTransaction", {
                "connectorId": port_id, "idTag": f"TAG-{random.randint(1000,9999)}",
                "meterStart": meter_start, "timestamp": start_time,
            })
            tx_id = result.get("transactionId", str(uuid.uuid4()))
            await self._send(ws, "StatusNotification", {
                "connectorId": port_id, "status": "Charging",
                "errorCode": "NoError", "timestamp": start_time,
            })
            await asyncio.sleep(duration_min * 6)   # 1s = 10 sim-minutes
            end_time = datetime.now(timezone.utc).isoformat()
            await self._send(ws, "StopTransaction", {
                "transactionId": tx_id, "connectorId": port_id,
                "meterStop": meter_end, "meterStart": meter_start,
                "startTime": start_time, "timestamp": end_time,
                "reason": "EVDisconnected",
            })
            await self._send(ws, "StatusNotification", {
                "connectorId": port_id, "status": "Available",
                "errorCode": "NoError", "timestamp": end_time,
            })
        except websockets.exceptions.ConnectionClosed:
            raise


async def main():
    ids_env = os.environ.get("OCPP_SIMULATE_STATIONS", "")
    ids     = {s.strip() for s in ids_env.split(",") if s.strip()} if ids_env else set()
    targets = [s for s in STATIONS if not ids or s["id"] in ids]
    if not targets:
        logger.warning("No stations to simulate")
        return
    logger.info("Simulating: %s", [s["id"] for s in targets])
    tasks = []
    for i, s in enumerate(targets):
        await asyncio.sleep(i * 0.5)
        tasks.append(asyncio.create_task(ChargerSimulator(s).run()))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
