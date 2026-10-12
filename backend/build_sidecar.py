"""把后端打包为 Tauri sidecar 可执行文件。

用法（在 backend 目录下，激活虚拟环境后）：
    python build_sidecar.py

产物：
    backend/dist/lottery-backend-x86_64-pc-windows-msvc.exe

Tauri 要求 sidecar 文件名带目标三元组后缀，脚本会自动重命名。
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
BUILD = HERE / "build"
FRONTEND_DIST = HERE.parent / "frontend" / "dist"

# Tauri sidecar 目标三元组（Windows x64）
TARGET_TRIPLE = "x86_64-pc-windows-msvc"
SIDECAR_NAME = f"lottery-backend-{TARGET_TRIPLE}"


def run(cmd: list[str]) -> None:
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=HERE)


def main() -> None:
    if not FRONTEND_DIST.exists():
        print(f"[warn] 未找到前端构建产物：{FRONTEND_DIST}")
        print("       请先在 frontend 目录执行 npm run build")

    # 清理旧产物
    for d in (DIST, BUILD):
        if d.exists():
            shutil.rmtree(d)

    # 把前端 dist 复制到 backend 下，随 sidecar 一起打包
    bundled_frontend = HERE / "frontend_dist"
    if bundled_frontend.exists():
        shutil.rmtree(bundled_frontend)
    if FRONTEND_DIST.exists():
        shutil.copytree(FRONTEND_DIST, bundled_frontend)

    # --add-data 分隔符：Windows 用 ;，其他平台用 :
    sep = ";" if sys.platform == "win32" else ":"

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        "lottery-backend",
        # 把 app 包与前端资源一起打包
        f"--add-data={HERE / 'app'}{sep}app",
        f"--add-data={bundled_frontend}{sep}frontend_dist",
        # 隐式依赖（uvicorn / pydantic / sqlalchemy 动态导入）
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=websockets",
        "--hidden-import=sqlalchemy.dialects.sqlite",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=qrcode",
        "--collect-submodules=app",
        "run_server.py",
    ]
    run(args)

    # 重命名为 Tauri sidecar 约定名
    exe_suffix = ".exe" if sys.platform == "win32" else ""
    src = DIST / f"lottery-backend{exe_suffix}"
    dst = DIST / f"{SIDECAR_NAME}{exe_suffix}"
    if src.exists():
        src.replace(dst)
        print(f"\n[ok] sidecar 已生成：{dst}")
    else:
        print(f"\n[error] 未找到产物：{src}")
        sys.exit(1)

    # 复制到 Tauri binaries 目录
    binaries_dir = HERE.parent / "desktop" / "src-tauri" / "binaries"
    binaries_dir.mkdir(parents=True, exist_ok=True)
    target = binaries_dir / dst.name
    shutil.copy2(dst, target)
    print(f"[ok] 已复制到：{target}")


if __name__ == "__main__":
    main()
