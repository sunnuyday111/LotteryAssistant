"""WebSocket 连接管理器。

按活动 ID 分组管理连接，用于向大屏实时推送签到人数、抽奖结果等事件。
"""

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """管理 WebSocket 连接，支持按活动分组广播。"""

    def __init__(self) -> None:
        # event_id -> set[WebSocket]
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, event_id: int, websocket: WebSocket) -> None:
        """接受连接并加入指定活动分组。"""

        await websocket.accept()
        async with self._lock:
            self._connections[event_id].add(websocket)

    async def disconnect(self, event_id: int, websocket: WebSocket) -> None:
        """断开连接并从分组移除。"""

        async with self._lock:
            self._connections[event_id].discard(websocket)
            if not self._connections[event_id]:
                self._connections.pop(event_id, None)

    async def broadcast(self, event_id: int, message: dict[str, Any]) -> None:
        """向指定活动的所有连接广播消息。"""

        async with self._lock:
            targets = list(self._connections.get(event_id, set()))

        if not targets:
            return

        payload = json.dumps(message, ensure_ascii=False, default=str)
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:  # noqa: BLE001 - 连接可能已断开
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections[event_id].discard(ws)

    def connection_count(self, event_id: int) -> int:
        """返回指定活动的连接数。"""

        return len(self._connections.get(event_id, set()))


# 全局单例
manager = ConnectionManager()
