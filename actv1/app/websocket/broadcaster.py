from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class LiveBroadcaster:
    def __init__(self, max_buffer: int = 200) -> None:
        self._connections: set[WebSocket] = set()
        self._buffer: deque[dict[str, Any]] = deque(maxlen=max_buffer)

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    @property
    def recent_events(self) -> list[dict[str, Any]]:
        return list(self._buffer)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        for event in self._buffer:
            await websocket.send_json(event)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event: dict[str, Any]) -> None:
        self._buffer.append(event)
        stale: list[WebSocket] = []
        for websocket in self._connections:
            try:
                await websocket.send_json(event)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)

    def publish(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "type": event_type,
            "payload": payload,
            "published_at": datetime.now(timezone.utc).isoformat(),
        }
        self._buffer.append(event)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return event

        loop.create_task(self.broadcast(event))
        return event


broadcaster = LiveBroadcaster()
