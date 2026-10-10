"""FastAPI 应用入口。"""

import io
from contextlib import asynccontextmanager

import qrcode
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .api import checkins, draws, events, exports, participants, prizes, stats, ws
from .config import settings
from .database import get_db, init_db
from .models import Event
from .services import event_service
from .api.deps import get_event_or_404


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库。"""

    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="活动签到抽奖助手后端 API：活动管理、名单导入、扫码签到、大屏抽奖、数据导出。",
    version="0.1.0",
    lifespan=lifespan,
)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(events.router)
app.include_router(participants.router)
app.include_router(checkins.router)
app.include_router(prizes.router)
app.include_router(draws.router)
app.include_router(stats.router)
app.include_router(exports.router)
app.include_router(ws.router)


@app.get("/api/health", tags=["系统"], summary="健康检查")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}


@app.get(
    "/api/events/{event_id}/qrcode",
    tags=["签到"],
    summary="生成签到二维码",
    response_class=Response,
)
def get_checkin_qrcode(
    event: Event = Depends(get_event_or_404),
) -> Response:
    """生成指向签到页面的二维码 PNG 图片。"""

    url = f"{settings.checkin_base_url}/{event.checkin_token}"
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return Response(content=buffer.getvalue(), media_type="image/png")


@app.get(
    "/api/events/{event_id}/checkin-url",
    tags=["签到"],
    summary="获取签到链接",
)
def get_checkin_url(event: Event = Depends(get_event_or_404)) -> dict:
    """返回签到页面 URL 与令牌。"""

    return {
        "token": event.checkin_token,
        "url": f"{settings.checkin_base_url}/{event.checkin_token}",
    }
