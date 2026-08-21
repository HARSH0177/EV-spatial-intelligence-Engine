"""
utils/async_bq.py  —  Improvement 2: Async-safe BigQuery wrapper.

Problem
-------
The BigQuery Python client is synchronous.  Calling `.result()` directly
inside an `async def` blocks the FastAPI event loop, stalling every other
in-flight request during the entire query duration.

Solution
--------
All BQ calls go through `run_bq_async()`, which offloads the blocking work
to a dedicated ThreadPoolExecutor.  The event loop regains control while the
thread pool thread waits for BigQuery.

Design choices
--------------
- One module-level ThreadPoolExecutor shared across the app.
  Size is controlled by BQ_EXECUTOR_WORKERS env var (default 4).
- `run_bq_async` wraps any callable; callers pass a lambda.
- Per-call timeout (default 30 s) prevents one slow query from holding
  an executor thread forever.
- On timeout or exception, `run_bq_async` raises — callers must catch
  and degrade gracefully (not crash the full request).

Interview talking point
-----------------------
"FastAPI runs on a single-threaded async event loop.  A blocking I/O call
(like BQ `.result()`) on that loop is equivalent to calling `time.sleep()`
— every concurrent request stalls until it returns.  We fix this with
run_in_executor, which delegates the blocking call to a thread pool so the
event loop stays free."
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Callable, TypeVar

from config import cfg

logger   = logging.getLogger(__name__)
T        = TypeVar("T")

# One shared executor for all BQ calls in the process
_bq_pool = ThreadPoolExecutor(
    max_workers=cfg.bq_executor_workers,
    thread_name_prefix="bq-worker",
)

_DEFAULT_TIMEOUT_SEC = 30.0


async def run_bq_async(
    fn:      Callable[[], T],
    timeout: float = _DEFAULT_TIMEOUT_SEC,
    label:   str   = "bq_query",
) -> T:
    """
    Run a synchronous BigQuery callable on the thread pool without blocking
    the asyncio event loop.

    Parameters
    ----------
    fn      : zero-argument callable wrapping the blocking BQ work,
              e.g. `lambda: client.query(sql, cfg).result()`
    timeout : max seconds to wait before raising asyncio.TimeoutError
    label   : human-readable name used in log messages

    Raises
    ------
    asyncio.TimeoutError  if the query exceeds `timeout` seconds
    Exception             re-raises any exception from the BQ call
    """
    loop = asyncio.get_event_loop()

    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(_bq_pool, fn),
            timeout=timeout,
        )
        return result

    except asyncio.TimeoutError:
        logger.warning("[%s] BigQuery timeout after %.1fs", label, timeout)
        raise

    except Exception as exc:
        logger.warning("[%s] BigQuery error: %s", label, exc)
        raise
