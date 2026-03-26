# playwright_compat.py
# ---------------------------------------------------------
# Windows + uvicorn compatibility layer for Playwright.
#
# Problem: Playwright spawns Chromium via asyncio.create_subprocess_exec,
# which requires ProactorEventLoop on Windows. But uvicorn's worker
# creates a SelectorEventLoop before we can override the policy.
#
# Solution: Run all Playwright operations in a dedicated thread
# with its own ProactorEventLoop. Events are bridged back to the
# caller via a thread-safe queue.
# ---------------------------------------------------------

import asyncio
import sys
import queue
from threading import Thread
from typing import Any, Callable, Coroutine


def _make_loop() -> asyncio.AbstractEventLoop:
    """Create a ProactorEventLoop on Windows, default elsewhere."""
    if sys.platform == "win32":
        return asyncio.ProactorEventLoop()
    return asyncio.new_event_loop()


async def run_playwright_async(coro: Coroutine) -> Any:
    """
    Run a Playwright coroutine from uvicorn's event loop.
    Offloads to a separate thread with ProactorEventLoop.
    """
    result_holder: dict = {}

    def _thread_target():
        loop = _make_loop()
        asyncio.set_event_loop(loop)
        try:
            result_holder["value"] = loop.run_until_complete(coro)
        except Exception as e:
            result_holder["error"] = e
        finally:
            loop.close()

    main_loop = asyncio.get_event_loop()
    await main_loop.run_in_executor(None, lambda: _run_thread(_thread_target))

    if "error" in result_holder:
        raise result_holder["error"]
    return result_holder["value"]


def run_playwright_with_events(
    coro_factory: Callable[[Callable[[dict], None]], Coroutine],
    event_queue: queue.Queue,
) -> None:
    """
    Run a Playwright coroutine in a ProactorEventLoop thread.
    The coroutine receives an on_event callback that puts dicts
    into the thread-safe event_queue.

    Args:
        coro_factory: async fn(on_event) -> result
        event_queue: thread-safe queue for SSE events
    """

    def on_event(event: dict) -> None:
        event_queue.put(event)

    def _thread_target():
        loop = _make_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro_factory(on_event))
        except Exception as e:
            event_queue.put({"type": "error", "message": str(e)})
        finally:
            event_queue.put({"type": "_done"})
            loop.close()

    thread = Thread(target=_thread_target, daemon=True)
    thread.start()


def _run_thread(target):
    thread = Thread(target=target, daemon=True)
    thread.start()
    thread.join()
