"""管理后台访问控制（默认拒绝）。

设计取舍
--------
采用「默认拒绝 + 显式白名单」：所有 ``/api/`` 请求和 ``/ws/`` 实时通道都必须携带
管理口令，只有下面列出的公开路径例外。这样新增接口时默认就是受保护的，
不必记得给每个路由补依赖；审计时也只需看这一份白名单。

公开路径（参与者 / 中奖者侧，扫码即用，无需口令）
    - ``GET  /api/health``                                    健康检查
    - ``GET  /api/checkin/{token}``                           扫码后查看活动信息
    - ``POST /api/checkin/{token}``                           提交签到
    - ``GET  /api/events/{eid}/draws/records/{rid}/claim-preview``  中奖者预览领奖凭证
    - ``POST /api/events/{eid}/draws/records/{rid}/claim``    中奖者扫码核销领奖

其余全部需要口令，包括：活动增删改、名单导入、奖项配置、执行抽奖、重置记录、
手动核销领奖、撤销领奖、统计与导出、二维码生成，以及大屏用的 ``/ws/`` 实时推送。

口令来源
--------
1. 环境变量 / ``.env`` 中的 ``ADMIN_TOKEN``（推荐，可固定、可分发给主办方）；
2. 留空时启动自动生成随机口令并打印到控制台，仅存于内存，进程重启后失效。

``claim_token`` 仍由 HMAC 派生、与本模块无关：中奖者领奖走的是「领奖码」而非
「管理口令」，两者互不替代。
"""

from __future__ import annotations

import hmac
import re
import secrets

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from ..config import settings

#: 前端通过该请求头携带管理口令。
ADMIN_TOKEN_HEADER = "X-Admin-Token"

#: WebSocket 无法自定义请求头，改用查询参数 ``?token=`` 传递。
ADMIN_TOKEN_QUERY = "token"

#: 进程内缓存的自动生成口令（仅当未配置 ADMIN_TOKEN 时使用）。
_generated_token: str | None = None

#: 公开路径白名单：(HTTP 方法, 路径正则)。路径为 Starlette 的原始 path，不含查询串。
PUBLIC_API_ROUTES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("GET", re.compile(r"^/api/health/?$")),
    ("GET", re.compile(r"^/api/checkin/[^/]+/?$")),
    ("POST", re.compile(r"^/api/checkin/[^/]+/?$")),
    ("GET", re.compile(r"^/api/events/\d+/draws/records/\d+/claim-preview/?$")),
    ("POST", re.compile(r"^/api/events/\d+/draws/records/\d+/claim/?$")),
)


def _banner(token: str) -> str:
    return (
        "\n"
        + "=" * 68 + "\n"
        "  管理后台口令（本次运行有效，进程重启后会重新生成）\n"
        f"    {token}\n"
        "  打开管理后台时在解锁页输入该口令即可；签到与领奖页面无需口令。\n"
        + "=" * 68
    )


def get_admin_token() -> str:
    """返回当前生效的管理口令，必要时生成并打印。"""

    global _generated_token

    configured = settings.admin_token.strip()
    if configured:
        return configured

    if _generated_token is None:
        _generated_token = secrets.token_urlsafe(24)
        print(_banner(_generated_token), flush=True)
    return _generated_token


def is_token_generated() -> bool:
    """当前口令是否为自动生成（而非来自 ``ADMIN_TOKEN`` 配置）。"""

    return not settings.admin_token.strip()


def verify_token(candidate: str | None) -> bool:
    """校验口令，使用常量时间比较避免时序侧信道。"""

    if not candidate:
        return False
    return hmac.compare_digest(candidate.strip(), get_admin_token())


def is_public_api(method: str, path: str) -> bool:
    """判断该请求是否命中公开路径白名单。"""

    return any(
        allowed_method == method and pattern.match(path)
        for allowed_method, pattern in PUBLIC_API_ROUTES
    )


def _unauthorized(detail: str) -> JSONResponse:
    """构造 401 响应。沿用 FastAPI 的 detail 结构，前端 extractError 可直接取用。"""

    return JSONResponse(
        status_code=401,
        content={"detail": detail},
        headers={"WWW-Authenticate": ADMIN_TOKEN_HEADER},
    )


def _header_value(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key == name:
            return value.decode("latin-1")
    return None


def _query_token(scope: Scope) -> str | None:
    from urllib.parse import parse_qs

    raw = scope.get("query_string", b"")
    values = parse_qs(raw.decode("latin-1")).get(ADMIN_TOKEN_QUERY)
    return values[0] if values else None


class AdminAuthMiddleware:
    """纯 ASGI 中间件，同时拦截 HTTP 与 WebSocket。

    之所以不用 ``BaseHTTPMiddleware``：它对 WebSocket scope 支持不完整，
    而大屏的实时通道恰好需要一起保护。
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        scope_type = scope["type"]

        if scope_type == "websocket":
            await self._handle_websocket(scope, receive, send)
        elif scope_type == "http":
            await self._handle_http(scope, receive, send)
        else:  # lifespan 等，直接透传
            await self.app(scope, receive, send)

    async def _handle_http(self, scope: Scope, receive: Receive, send: Send) -> None:
        path: str = scope.get("path", "")
        if not path.startswith("/api/"):
            await self.app(scope, receive, send)
            return

        # CORS 预检不含自定义请求头，交给 CORSMiddleware 处理，否则浏览器会直接失败
        if scope.get("method") == "OPTIONS":
            await self.app(scope, receive, send)
            return

        if is_public_api(scope.get("method", "GET"), path):
            await self.app(scope, receive, send)
            return

        token = _header_value(scope, ADMIN_TOKEN_HEADER.lower().encode("latin-1"))
        if token is None:
            token = _query_token(scope)

        if not verify_token(token):
            response = _unauthorized(
                "管理口令缺失或不正确，请在解锁页输入口令"
                if token
                else "需要管理口令，请在解锁页输入口令"
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    async def _handle_websocket(self, scope: Scope, receive: Receive, send: Send) -> None:
        token = _query_token(scope)
        if token is None:
            token = _header_value(scope, ADMIN_TOKEN_HEADER.lower().encode("latin-1"))

        if not verify_token(token):
            await send({"type": "websocket.close", "code": 1008})
            return

        await self.app(scope, receive, send)
