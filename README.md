# 活动签到抽奖助手

一套后端、多端复用的活动签到抽奖系统。支持活动创建、Excel 名单导入、扫码签到、大屏抽奖、扫码领奖和数据导出，可同时用于 Web 浏览器和 Windows 桌面端。

## 功能特性

### 活动与名单

- **活动管理**：创建、编辑、删除活动，设置名称、时间、地点、说明；状态按开始/结束时间自动推算（草稿 / 进行中 / 已结束）
- **名单导入**：支持 Excel(.xlsx/.xls) 和 CSV，自动识别中英文表头，重复检测与格式校验
- **手动维护**：可单个添加参与者、手动签到、取消签到、删除参与者

### 签到

- **扫码签到**：生成签到二维码，参与者手机扫码即可签到，无需安装 App
- **防重复**：同一手机号重复扫码不会重复签到

### 抽奖

- **奖项可配置**：每个奖项独立配置名称、数量、排序权重、奖品描述、抽奖玩法、是否需要现场扫码领奖
- **多种抽奖玩法**：滚动名单、轮盘转盘、砸金蛋、九宫格，由奖项的 `draw_mode` 驱动
- **大屏抽奖**：单人/多人抽奖、真实候选人姓名滚动、中奖者卡片展示
- **结果持久化**：抽奖结果由后端随机生成并落库，前端仅负责动画展示

### 领奖

- **扫码领奖**：中奖者扫码进入领奖页，输入手机号（完整或后 4 位）核销领奖
- **领取状态**：`待领取` / `已领取` 两态流转，免领奖项中奖即终态
- **主办方兜底**：后台可查看领奖二维码、手动核销（手机没电/二维码丢失）、撤销领奖

### 数据

- **实时同步**：WebSocket 实时推送签到人数、抽奖结果、领奖状态到大屏
- **数据看板**：总人数、已签到、未签到、签到率、各奖项中奖情况、待领取/已领取/免领统计
- **数据导出**：导出签到明细和中奖名单 Excel（中奖名单含领取状态与领取时间）

## 技术架构

```
┌─────────────────────────────────────────────────┐
│  前端展示层  React 18 + TypeScript + Vite        │
│  管理后台 · 签到 H5 · 领奖 H5 · 抽奖大屏 · 桌面端  │
└───────────────────────┬─────────────────────────┘
                        │ HTTP REST API / WebSocket
┌───────────────────────┴─────────────────────────┐
│  后端服务层  Python + FastAPI + SQLAlchemy 2.x   │
│  活动管理 · 签到校验 · 抽奖逻辑 · 领奖核销 · Excel │
└───────────────────────┬─────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────┐
│  数据存储层  SQLite（单机） / PostgreSQL（在线）  │
└─────────────────────────────────────────────────┘
```

前端路由使用 `HashRouter`，因此签到/领奖/大屏链接形如
`http://<host>/#/checkin/<token>`、`http://<host>/#/claim/<eventId>/<recordId>/<code>`。
后端 SPA fallback 会把任意非 `/api/` 路径返回 `index.html`，由
[main.tsx](frontend/src/main.tsx) 把路径式 URL 重写为 hash 式 URL。

## 目录结构

```
LotteryAssistant/
├── backend/                  # Python + FastAPI 后端
│   ├── app/
│   │   ├── api/              # API 路由（events/participants/checkins/prizes/draws/stats/exports/ws）
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── schemas/          # Pydantic 数据模型
│   │   ├── services/         # 业务逻辑（含 claim_service 领奖核销）
│   │   ├── config.py         # 配置
│   │   ├── database.py       # 数据库连接 + 轻量迁移
│   │   └── main.py           # 应用入口（含 SPA fallback）
│   ├── build_sidecar.py      # PyInstaller 打包脚本
│   ├── run_server.py         # 桌面端 sidecar 入口
│   ├── sample_participants.csv
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # React + TypeScript 前端
│   ├── src/
│   │   ├── api/              # API 客户端（http.ts / index.ts）
│   │   ├── components/
│   │   │   ├── AdminLayout.tsx
│   │   │   └── lottery/PlayModes.tsx   # 4 种抽奖玩法动画
│   │   ├── pages/
│   │   │   ├── events/       # 活动列表 / 活动详情（名单·奖项·中奖领奖）
│   │   │   ├── checkin/      # 手机签到页
│   │   │   ├── claim/        # 扫码领奖页
│   │   │   ├── lottery/      # 抽奖大屏
│   │   │   └── dashboard/    # 数据看板
│   │   ├── types/            # TypeScript 类型
│   │   └── main.tsx
│   ├── nginx.conf
│   └── package.json
├── desktop/                  # Tauri 2 Windows 桌面封装
│   ├── src-tauri/            # Rust 主进程（拉起 sidecar、保存下载文件）
│   └── package.json
├── .github/workflows/        # ci.yml / release.yml
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
2. 进入活动详情，导入参与者名单（Excel/CSV）或手动添加
3. 在「奖项配置」中新增奖项，设置数量、**抽奖玩法**、**是否需要现场扫码领奖**
4. 点击「签到二维码」，让参与者扫码签到
5. 点击「打开抽奖大屏」，选择奖项开始抽奖（动画按奖项配置的玩法呈现）
6. 中奖者扫码领奖；主办方在「中奖与领奖」中查看状态、手动核销或撤销
7. 在「数据看板」查看统计并导出数据

## 名单文件格式

支持 `.xlsx`、`.xls`、`.csv`，表头支持中英文：

| 姓名 | 手机号 | 部门 | 备注 |
| ---- | ------ | ---- | ---- |
| 张三 | 13800000001 | 技术部 | |
| 李四 | 13800000002 | 市场部 | |

也支持英文表头：`name`、`phone`、`department`、`remark`。
仓库内提供了示例文件 [sample_participants.csv](backend/sample_participants.csv)。

## 抽奖玩法

在奖项配置中选择，决定抽奖大屏的动画呈现方式：

| 值 | 玩法 | 说明 |
| ---- | ---- | ---- |
| `roll` | 滚动名单 | 默认玩法，大号姓名快速滚动 |
| `wheel` | 轮盘转盘 | 转盘旋转，中心实时显示候选人 |
| `egg` | 砸金蛋 | 九宫格金蛋抖动，点击「砸金蛋」开始 |
| `grid` | 九宫格 | 九宫格高亮跑马灯 + 候选人姓名 |

## 领奖机制

每个奖项可独立设置「是否需要现场扫码领奖」：

- **需要扫码**（`claim_required = true`）：中奖后状态为 `待领取`，生成领奖二维码；
  中奖者扫码进入领奖页，输入手机号（完整或后 4 位）核销后变为 `已领取`
- **免领**（`claim_required = false`）：中奖即终态，不生成二维码、不记录领取时间

领奖码由 HMAC-SHA256 基于 `(record_id + 密钥)` 生成，**不落库、不可伪造**，
URL 形如 `/claim/<event_id>/<record_id>/<code>`。

主办方兜底手段（活动详情 →「中奖与领奖」）：

- 查看/展示领奖二维码（供中奖者现场扫码）
- **手动核销**：中奖者手机没电或二维码丢失时直接核销
- **撤销领奖**：误操作后恢复为待领取
- 按领取状态筛选记录（全部 / 仅待领取 / 仅已领取 / 仅免领奖项）

## 核心业务规则

- 同一参与者重复扫码不会重复签到
- 默认仅已签到者可参与抽奖
- 默认同一参与者不能重复中奖（可在抽奖时开启「允许重复中奖」）
- 抽奖结果由后端随机生成并持久化，前端仅负责动画展示
- 抽奖名额受奖项数量限制，剩余名额为 0 时不可再抽
- Excel 导入会校验必填字段、重复数据和异常格式
- 不同活动的数据严格隔离

## Docker 部署

```bash
docker compose up -d --build
```

- 前端：http://localhost
- 后端：http://localhost:8000

`docker-compose.yml` 中后端使用 `sqlite:///./data/lottery.db`（挂载到 `./backend/data`），
前端由 nginx 托管静态资源并反向代理 `/api/` 与 `/ws/` 到后端容器。

> 部署到局域网时，需把 `CHECKIN_BASE_URL` 改为手机可访问的地址，
> 否则签到/领奖二维码会指向 `localhost` 导致手机扫码打不开。

## Windows 桌面端打包

桌面端基于 **Tauri 2**，打包为原生 `.exe` 安装包（NSIS）。

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
- **后端端口**：默认 `8000`，可通过环境变量 `LOTTERY_PORT` 覆盖
- **监听地址**：默认 `0.0.0.0`（局域网可达，便于手机扫码），可用 `LOTTERY_HOST` 覆盖
- **二维码地址**：桌面端启动时自动探测局域网 IP，生成 `http://<局域网IP>:<端口>/checkin`；
  可用 `LOTTERY_PUBLIC_HOST` 或 `CHECKIN_BASE_URL` 强制覆盖
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
>
> 桌面端 WebView 使用 `tauri://` 协议，无法直接加载 `blob:` 下载与 `<img src="/api/...">`，
> 因此导出文件走 Rust 端 `save_download` 落盘，二维码改为 axios 取 PNG 后转 `data:` URL 内嵌。

## GitHub Actions 流水线

仓库内置两条流水线：

| 流水线 | 文件 | 触发条件 | 作用 |
|--------|------|----------|------|
| **CI** | [.github/workflows/ci.yml](.github/workflows/ci.yml) | push / PR 到 `main` | 后端依赖安装 + 导入检查、前端依赖安装 + 类型检查与构建 |
| **Release** | [.github/workflows/release.yml](.github/workflows/release.yml) | 推送 `v*` 标签，或手动触发 | 构建前端 → 打包 sidecar → 构建安装包 → 上传 Release |

> CI 目前只做「能否导入 / 能否构建」的冒烟级检查，尚未接入单元测试与 Rust fmt/clippy。

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
4. 创建 GitHub Release 并附带 `release/` 下的 `*.exe` / `*.msi`

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
# 后端（导入检查）
cd backend && .venv/Scripts/python.exe -c "from app.main import app; print(len(app.routes))"

# 前端（类型检查 + 构建）
cd frontend && npm run build
```

## 环境变量

后端支持通过 `.env` 文件或环境变量配置（参考 [backend/.env.example](backend/.env.example)）：

| 变量 | 说明 | 默认值 |
| ---- | ---- | ------ |
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./lottery.db` |
| `DEBUG` | 调试模式 | `true` |
| `CHECKIN_BASE_URL` | 签到页地址前缀（二维码指向） | `http://172.31.20.69:5173/checkin` |
| `CLAIM_BASE_URL` | 领奖页地址前缀（留空则由 `CHECKIN_BASE_URL` 推导） | 空 |
| `CLAIM_SECRET` | 领奖码签名密钥（留空则用 `app_name` 派生） | 空 |
| `CORS_ORIGINS` | 允许的跨域来源 | 见 `config.py` |

桌面端 sidecar 额外支持：

| 变量 | 说明 | 默认值 |
| ---- | ---- | ------ |
| `LOTTERY_HOST` | 后端监听地址 | `0.0.0.0` |
| `LOTTERY_PORT` | 后端监听端口 | `8000` |
| `LOTTERY_PUBLIC_HOST` | 二维码使用的公网/局域网 host | 自动探测局域网 IP |
| `FRONTEND_DIST` | 前端静态资源目录 | `frontend/dist` |

前端可通过 `VITE_API_BASE_URL` 指定后端地址（留空则同源，Tauri 下默认 `http://127.0.0.1:8000`）。

> 正式环境建议显式配置随机的 `CLAIM_SECRET`，避免领奖码可被推导伪造。

## 数据库表

| 表名 | 主要字段 | 作用 |
| ---- | -------- | ---- |
| `events` | id、name、start_time、end_time、status、checkin_token | 活动信息 |
| `participants` | id、event_id、name、phone、department、remark | 参与者名单 |
| `checkins` | id、event_id、participant_id、checked_in_at、method | 签到记录 |
| `prizes` | id、event_id、name、quantity、sort_order、claim_required、draw_mode | 奖项配置 |
| `draw_records` | id、event_id、prize_id、participant_id、drawn_at、claim_status、claimed_at | 中奖记录 |

> `database.py` 内置轻量迁移：启动时会为已存在的旧库自动补齐新增列
> （`prizes.claim_required` / `prizes.draw_mode` / `draw_records.claim_status` /
> `draw_records.claimed_at`）与索引，无需手动改库。

## 主要 API

### 活动与名单

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | `/api/events` | 活动列表 |
| POST | `/api/events` | 创建活动 |
| GET | `/api/events/{id}` | 活动详情（含统计） |
| PUT | `/api/events/{id}` | 更新活动 / 切换状态 |
| DELETE | `/api/events/{id}` | 删除活动 |
| GET | `/api/events/{id}/participants` | 参与者列表 |
| POST | `/api/events/{id}/participants` | 添加单个参与者 |
| POST | `/api/events/{id}/participants/import` | 导入 Excel/CSV 名单 |
| DELETE | `/api/events/{id}/participants/{pid}` | 删除参与者 |

### 签到

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | `/api/events/{id}/qrcode` | 签到二维码 PNG |
| GET | `/api/events/{id}/checkin-url` | 签到链接与令牌 |
| GET | `/api/checkin/{token}` | 扫码后获取活动信息 |
| POST | `/api/checkin/{token}` | 提交签到 |
| POST | `/api/checkin/{id}/manual/{pid}` | 主办方手动签到 |
| DELETE | `/api/checkin/{id}/manual/{pid}` | 取消签到 |

### 奖项与抽奖

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | `/api/events/{id}/prizes` | 奖项列表（含已抽取数） |
| POST | `/api/events/{id}/prizes` | 创建奖项 |
| PUT | `/api/events/{id}/prizes/{prize_id}` | 更新奖项 |
| DELETE | `/api/events/{id}/prizes/{prize_id}` | 删除奖项 |
| POST | `/api/events/{id}/draws` | 执行抽奖 |
| GET | `/api/events/{id}/draws` | 中奖记录（含领取状态） |
| DELETE | `/api/events/{id}/draws` | 重置抽奖记录（可按奖项） |

### 领奖

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | `/api/events/{id}/draws/claim-stats` | 待领取 / 已领取 / 免领统计 |
| GET | `/api/events/{id}/draws/records/{rid}/claim-qrcode` | 领奖二维码 PNG |
| GET | `/api/events/{id}/draws/records/{rid}/claim-preview` | 预览领奖凭证（不核销） |
| POST | `/api/events/{id}/draws/records/{rid}/claim` | 扫码核销领奖 |
| POST | `/api/events/{id}/draws/records/{rid}/manual-claim` | 主办方手动核销 |
| DELETE | `/api/events/{id}/draws/records/{rid}/claim` | 撤销领奖 |

### 统计、导出与实时

| 方法 | 路径 | 说明 |
| ---- | ---- | ---- |
| GET | `/api/events/{id}/stats` | 数据看板统计 |
| GET | `/api/events/{id}/export/checkins` | 导出签到明细 |
| GET | `/api/events/{id}/export/draws` | 导出中奖名单 |
| GET | `/api/health` | 健康检查 |
| WS | `/ws/events/{id}` | 实时推送（checkin / draw / draw_reset / claim） |

完整交互式文档：http://localhost:8000/docs

## 许可证

Apache License 2.0
