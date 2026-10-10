"""WebSocket API：大屏实时数据推送。"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services import ws_manager

router = APIRouter(tags=["实时通信"])


@router.websocket("/ws/events/{event_id}")
async def event_ws(websocket: WebSocket, event_id: int) -> None:
    """大屏订阅指定活动的实时事件。

    推送消息类型：
    - checkin：有人签到
    - draw：抽奖结果
    - draw_reset：抽奖记录被重置
    """

    manager = ws_manager.manager
    await manager.connect(event_id, websocket)
    try:
        # 发送欢迎消息，确认连接成功
        await websocket.send_json(
            {"type": "connected", "event_id": event_id}
        )
        while True:
            # 保持连接，接收心跳或客户端消息（当前忽略内容）
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(event_id, websocket)
