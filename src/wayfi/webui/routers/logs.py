"""Log streaming API routes via Server-Sent Events."""

from __future__ import annotations

import asyncio
import logging
from collections import deque

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["logs"])

# Ring buffer for recent log messages
_log_buffer: deque[str] = deque(maxlen=500)


class BufferHandler(logging.Handler):
    """Logging handler that writes to the shared ring buffer."""

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        _log_buffer.append(msg)


def setup_log_buffer() -> None:
    """Attach the buffer handler to the wayfi logger."""
    handler = BufferHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    logging.getLogger("wayfi").addHandler(handler)


@router.get("/logs")
async def get_logs(limit: int = 100) -> dict:
    """Get recent log messages."""
    messages = list(_log_buffer)[-limit:]
    return {"logs": messages, "total": len(_log_buffer)}


@router.get("/logs/stream")
async def stream_logs() -> StreamingResponse:
    """Stream logs via Server-Sent Events."""

    async def event_generator():
        last_index = len(_log_buffer)
        while True:
            current = len(_log_buffer)
            if current > last_index:
                new_messages = list(_log_buffer)[last_index:current]
                for msg in new_messages:
                    yield f"data: {msg}\n\n"
                last_index = current
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
