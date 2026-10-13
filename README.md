# 活动签到抽奖助手

一套后端、多端复用的活动签到抽奖系统。支持活动创建、Excel 名单导入、扫码签到、大屏抽奖和数据导出，可同时用于 Web 浏览器和 Windows 桌面端。

## 功能特性

- **活动管理**：创建、编辑、删除活动，设置名称、时间、地点、说明
- **名单导入**：支持 Excel(.xlsx/.xls) 和 CSV，自动识别中英文表头，重复检测
- **扫码签到**：生成签到二维码，参与者手机扫码即可签到，无需安装 App
- **大屏抽奖**：单人/多人抽奖、奖项配置、滚动动画、中奖展示
- **实时同步**：WebSocket 实时推送签到人数与抽奖结果到大屏
- **数据看板**：总人数、已签到、未签到、签到率、各奖项中奖情况
- **数据导出**：导出签到明细和中奖名单 Excel

## 技术架构

```
┌─────────────────────────────────────────────────┐
│  前端展示层  React + TypeScript + Vite           │
│  管理后台 · 签到 H5 · 抽奖大屏 · Windows 桌面端    │
└───────────────────────┬─────────────────────────┘
                        │ HTTP REST API / WebSocket
┌───────────────────────┴─────────────────────────┐
│  后端服务层  Python + FastAPI + SQLAlchemy 2.x   │
│  活动管理 · 签到校验 · 抽奖逻辑 · Excel · 权限    │
└───────────────────────┬─────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────┐
│  数据存储层  SQLite（单机） / PostgreSQL（在线）  │
└─────────────────────────────────────────────────┘
```

## 目录结构

```
LotteryAssistant/
├── backend/                  # Python + FastAPI 后端
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── schemas/          # Pydantic 数据模型
│   │   ├── services/         # 业务逻辑
│   │   ├── config.py         # 配置
│   │   ├── database.py       # 数据库连接
│   │   └── main.py           # 应用入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React + TypeScript 前端
│   ├── src/
│   │   ├── api/              # API 客户端
│   │   ├── components/       # 通用组件
│   │   ├── pages/
│   │   │   ├── events/       # 活动管理
│   │   │   ├── checkin/      # 手机签到页
│   │   │   ├── lottery/      # 抽奖大屏
│   │   │   └── dashboard/    # 数据看板
│   │   ├── types/            # TypeScript 类型
│   │   └── main.tsx
│   └── package.json
├── desktop/                  # Tauri Windows 桌面封装
│   └── src-tauri/
├── docker-compose.yml
└── README.md
```

## 快速开始

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务（默认 http://localhost:8000）
uvicorn app.main:app --reload --host 0.0.0.0
```

API 文档：http://localhost:8000/docs

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

### 3. 使用流程

1. 在「活动管理」中新建活动
2. 进入活动详情，导入参与者名单（Excel/CSV）
3. 配置奖项（一等奖、二等奖等）
4. 点击「签到二维码」，让参与者扫码签到
5. 打开「抽奖大屏」，选择奖项开始抽奖
6. 在「数据看板」查看统计并导出数据

## 名单文件格式

支持 `.xlsx`、`.xls`、`.csv`，表头支持中英文：

| 姓名 | 手机号 | 部门 | 备注 |
| ---- | ------ | ---- | ---- |
| 张三 | 13800000001 | 技术部 | |
| 李四 | 13800000002 | 市场部 | |

也支持英文表头：`name`、`phone`、`department`、`remark`。

## 核心业务规则

- 同一参与者重复扫码不会重复签到
- 默认仅已签到者可参与抽奖
- 默认同一参与者不能重复中奖（可在抽奖时开启「允许重复中奖」）
- 抽奖结果由后端随机生成并持久化，前端仅负责动画展示
- Excel 导入会校验必填字段、重复数据和异常格式
- 不同活动的数据严格隔离

## Docker 部署

```bash
docker compose up -d --build
```

- 前端：http://localhost
- 后端：http://localhost:8000

## Windows 桌面端打包

桌面端基于 **Tauri 2**，打包为原生 `.exe` / `.msi` 安装包。

### 前置条件

1. **Rust 工具链**（必需）
   - 下载并运行 [rustup-init.exe](https://win.rustup.rs/x86_64)
   - 安装时选择 `x86_64-pc-windows-msvc` 工具链
   - 安装完成后**重开终端**，验证：`rustc --version`、`cargo --version`
2. **Visual Studio C++ 生成工具**（MSVC 链接器，必需）
   - 安装 [Visual Studio 2022 生成工具](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   - 勾选「使用 C++ 的桌面开发」工作负载（含 Windows SDK）
3. **Node.js 18+**（前端构建）
4. **WebView2 Runtime**：Windows 10/11 通常已内置；Win10 早期版本需安装 [WebView2](https://developer.microsoft.com/microsoft-edge/webview2/)

### 打包步骤（含内置后端，开箱即用）

桌面端会把 **FastAPI 后端打包为 sidecar 可执行文件**，随安装包一起分发。
用户安装后**无需单独启动后端**，双击 exe 即可使用（后端由桌面端自动拉起）。

```bash
# 1. 构建前端静态资源
cd frontend
npm install
npm run build

# 2. 打包后端为 sidecar（PyInstaller）
cd ../backend
.venv/Scripts/python.exe -m pip install pyinstaller
.venv/Scripts/python.exe build_sidecar.py
# 产物：desktop/src-tauri/binaries/lottery-backend-x86_64-pc-windows-msvc.exe

# 3. 打包桌面端（会自动嵌入 sidecar）
cd ../desktop
npm install
npm run build
```

也可以一步到位（在 `desktop` 目录）：

```bash
npm run build:all   # 先打包 sidecar，再打包 Tauri 应用
```

首次编译 Rust 耗时较长（约 5–15 分钟）。

### 产物位置

```
desktop/src-tauri/target/release/bundle/
└── nsis/活动签到抽奖助手_0.1.0_x64-setup.exe   # NSIS 安装包（含内置后端）
```

### 运行时数据

- **数据库**：`%APPDATA%\LotteryAssistant\lottery.db`（SQLite，自动创建）
- **后端端口**：默认 `127.0.0.1:8000`，可通过环境变量 `LOTTERY_PORT` 覆盖
- 桌面端启动时自动拉起后端进程，退出时自动关闭

### 常用命令

| 命令 | 说明 |
|------|------|
| `npm run dev` | 开发模式（热重载，需手动启动后端） |
| `npm run build:sidecar` | 仅打包后端 sidecar |
| `npm run build:all` | 打包 sidecar + 桌面端安装包 |
| `npm run build` | 仅打包桌面端（需先有 sidecar） |
| `npm run tauri icon <图片>` | 由一张 1024×1024 PNG 重新生成全套图标 |

### 图标

图标已生成于 `desktop/src-tauri/icons/`。如需替换，准备一张 1024×1024 的 PNG，执行：

```bash
cd desktop
npm run tauri icon path/to/logo.png
```

> 说明：开发模式（`npm run dev`）下后端不会自动拉起，需手动执行
> `cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000`。

## GitHub Actions 流水线

仓库内置两条流水线：

| 流水线 | 文件 | 触发条件 | 作用 |
|--------|------|----------|------|
| **CI** | [.github/workflows/ci.yml](.github/workflows/ci.yml) | push / PR 到 `main` | 后端导入检查 + 冒烟测试、前端类型检查与构建、Rust fmt/clippy |
| **Release** | [.github/workflows/release.yml](.github/workflows/release.yml) | 推送 `v*` 标签，或手动触发 | 构建前端 → 打包 sidecar → 构建安装包 → 上传 Release |

### 发布新版本

```bash
git add .
git commit -m "chore: release v0.1.0"
git tag v0.1.0
git push origin main --tags
```

流水线会自动完成：

1. `npm ci && npm run build`（前端）
2. `pip install -r requirements.txt pyinstaller` → `python build_sidecar.py`（后端单文件）
3. `cargo tauri build`（把 sidecar 嵌入主 EXE 并生成 NSIS 安装包）
4. 创建 GitHub Release 并附带 `*.exe` / `*.msi`

### 手动触发发布

GitHub 仓库 → **Actions** → **构建并发布桌面端** → **Run workflow**，
可勾选 `publish_release` 决定是否创建 Release。

### Commit 规范（决定 Release 变更列表分类）

Release 会读取两个标签之间的 commit message，按 [Conventional Commits](https://www.conventionalcommits.org/) 自动分到不同分组：

| 前缀 | Release 分组 |
|------|-------------|
| `feat:` | ✨ 新功能 |
| `fix:` | 🐛 问题修复 |
| `perf:` | ⚡ 性能优化 |
| `refactor:` / `style:` | ♻️ 重构 |
| `docs:` | 📚 文档 |
| `chore:` / `build:` / `ci:` / `test:` | 🔧 构建 / 杂项 |
| 其他 | 📦 其他 |

支持带 scope，例：`feat(backend): 支持自定义奖项权重`，Release 中会显示为 `- [backend] 支持自定义奖项权重 (feat)`。

```bash
git commit -m "feat(export): 支持导出中奖名单"
git commit -m "fix(tauri): 修复桌面端大屏白屏"
git commit -m "perf(api): 抽奖接口增加缓存"
```

> 注意：changelog 只统计**非合并 commit**（`--no-merges`），所以请不要用 merge commit 承载功能改动，
> 推荐 squash merge 或直接 push 提交。

### 本地验证 CI 配置

```bash
# 后端
cd backend && .venv/Scripts/python.exe smoke_test.py

# 前端
cd frontend && npm run build

# Rust
cd desktop/src-tauri && cargo fmt --all -- --check
```

## 环境变量

后端支持通过 `.env` 文件或环境变量配置（参考 `backend/.env.example`）：

| 变量 | 说明 | 默认值 |
| ---- | ---- | ------ |
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./lottery.db` |
| `DEBUG` | 调试模式 | `true` |
| `CHECKIN_BASE_URL` | 签到页地址前缀 | `http://localhost:5173/checkin` |

前端可通过 `VITE_API_BASE_URL` 指定后端地址。

## 数据库表

| 表名 | 主要字段 | 作用 |
| ---- | -------- | ---- |
| `events` | id、name、start_time、status、checkin_token | 活动信息 |
| `participants` | id、event_id、name、phone | 参与者名单 |
| `checkins` | id、event_id、participant_id、checked_in_at | 签到记录 |
| `prizes` | id、event_id、name、quantity | 奖项配置 |
| `draw_records` | id、event_id、prize_id、participant_id、drawn_at | 中奖记录 |

## 主要 API

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | `/api/events` | 活动列表 |
| POST | `/api/events` | 创建活动 |
| GET | `/api/events/{id}` | 活动详情 |
| POST | `/api/events/{id}/participants/import` | 导入名单 |
| GET | `/api/events/{id}/qrcode` | 签到二维码 |
| POST | `/api/checkin/{token}` | 提交签到 |
| POST | `/api/events/{id}/draws` | 执行抽奖 |
| GET | `/api/events/{id}/stats` | 数据统计 |
| GET | `/api/events/{id}/export/checkins` | 导出签到明细 |
| GET | `/api/events/{id}/export/draws` | 导出中奖名单 |
| WS | `/ws/events/{id}` | 实时推送 |

## 许可证

Apache License 2.0
