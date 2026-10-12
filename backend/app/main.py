"""FastAPI 应用入口。"""

import io
import os
import socket
from contextlib import asynccontextmanager
from pathlib import Path

import qrcode
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .api import checkins, draws, events, exports, participants, prizes, stats, ws
from .config import settings
from .database import get_db, init_db
from .models import Event
from .services import event_service
from .api.deps import get_event_or_404


def _resolve_checkin_base_url() -> str:
    """根据运行环境返回签到二维码应该使用的 base URL。

    优先级：
      1. 环境变量 CHECKIN_BASE_URL 显式覆盖
      2. LOTTERY_PUBLIC_HOST 环境变量指定的公网/局域网 host
      4. 用户在 settings.checkin_base_url 中配置的地址
    """

    override = os.environ.get("CHECKIN_BASE_URL")
    if override:
        return override.rstrip("/")
    return settings.checkin_base_url.rstrip("/")


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

    url = f"{_resolve_checkin_base_url()}/{event.checkin_token}"
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

    base = _resolve_checkin_base_url()
    return {
        "token": event.checkin_token,
        "url": f"{base}/{event.checkin_token}",
    }


# ---------- 前端静态资源（SPA fallback） ----------
# 仅当 frontend_dist 目录存在时启用：方便桌面端直接用系统浏览器打开大屏
# 默认查找路径：
#   1. 环境变量 FRONTEND_DIST 指向的目录
#   2. backend/../frontend/dist（开发与本地构建）
FRONTEND_DIST = (
    os.environ.get("FRONTEND_DIST")
    or str(Path(__file__).resolve().parent.parent.parent / "frontend" / "dist")
)
INDEX_HTML = Path(FRONTEND_DIST) / "index.html"
ASSETS_DIR = Path(FRONTEND_DIST) / "assets"

if INDEX_HTML.exists():
    if ASSETS_DIR.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(ASSETS_DIR)),
            name="frontend-assets",
        )

    @app.get("/", include_in_schema=False)
    async def spa_root() -> FileResponse:
        return FileResponse(str(INDEX_HTML))

    @app.get("/index.html", include_in_schema=False)
    async def spa_index() -> FileResponse:
        return FileResponse(str(INDEX_HTML))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        # 仅处理非 /api/ 路径，避免拦截 API
        if full_path.startswith("api/") or full_path.startswith("api"):
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not Found")
        # 如果请求的是带扩展名的静态资源（js/css/png 等），返回 404 而不是 index.html
        # 防止 relative base 把 /checkin/<token>/assets/index.js 误返回 HTML
        if "." in full_path.rsplit("/", 1)[-1]:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(str(INDEX_HTML))
