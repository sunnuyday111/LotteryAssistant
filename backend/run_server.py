"""桌面端 sidecar 入口：以独立进程方式启动 FastAPI 后端。

被 PyInstaller 打包为单文件可执行程序，由 Tauri 桌面端在启动时拉起。
与 `uvicorn app.main:app` 的区别：
- 数据库固定放在用户数据目录（可写），而非当前工作目录
- 前端静态资源路径通过环境变量 FRONTEND_DIST 注入
- 端口可通过环境变量 LOTTERY_PORT 覆盖（默认 8000）
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _user_data_dir() -> Path:
    """返回可写的用户数据目录（存放 SQLite 数据库）。"""

    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    path = Path(base) / "LotteryAssistant"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resource_dir() -> Path:
    """返回打包后的资源目录（PyInstaller 解压目录或源码目录）。"""

    if getattr(sys, "frozen", False):
        # PyInstaller 单文件模式：资源解压在 sys._MEIPASS
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def main() -> None:
    data_dir = _user_data_dir()
    resource_dir = _resource_dir()

    # 数据库放到用户数据目录，避免写入安装目录（可能无权限）
    os.environ.setdefault(
        "DATABASE_URL", f"sqlite:///{(data_dir / 'lottery.db').as_posix()}"
    )

    # 前端静态资源：优先使用打包进 sidecar 的 dist，其次使用同目录 dist
    if "FRONTEND_DIST" not in os.environ:
        bundled = resource_dir / "frontend_dist"
        if bundled.exists():
            os.environ["FRONTEND_DIST"] = str(bundled)

    # 确保能 import app 包
    if str(resource_dir) not in sys.path:
        sys.path.insert(0, str(resource_dir))

    import uvicorn

    from app.main import app

    # 桌面端默认监听 0.0.0.0（局域网可达，手机扫码）
    host = os.environ.get("LOTTERY_HOST", "0.0.0.0")
    port = int(os.environ.get("LOTTERY_PORT", "8000"))

    # 二维码 base URL：
    # - 桌面端默认使用 http://<局域网IP>:8000，确保手机扫码能访问
    # - 通过 CHECKIN_BASE_URL 可强制覆盖
    if "CHECKIN_BASE_URL" not in os.environ:
        public_host = os.environ.get("LOTTERY_PUBLIC_HOST")
        if public_host:
            os.environ["CHECKIN_BASE_URL"] = f"http://{public_host}:{port}/checkin"
        elif sys.platform == "win32":
            # 桌面端：默认用局域网 IP 段，确保手机可扫
            ip = _local_ip() or "127.0.0.1"
            os.environ["CHECKIN_BASE_URL"] = f"http://{ip}:{port}/checkin"
        else:
            os.environ["CHECKIN_BASE_URL"] = f"http://127.0.0.1:{port}/checkin"

    uvicorn.run(app, host=host, port=port, log_level="info")


def _local_ip() -> str | None:
    """探测局域网 IP（不依赖外部库）。"""

    import socket as _socket

    try:
        with _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return None


if __name__ == "__main__":
    main()
