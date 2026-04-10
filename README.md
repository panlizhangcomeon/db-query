# db-query

多数据库 AI 查询工具：管理 MySQL 连接、浏览库表结构、执行受控 SELECT 查询，并支持自然语言生成 SQL（依赖配置的 LLM）。

## 技术栈

- **后端**：Python 3.10+、FastAPI、SQLGlot、aiomysql、SQLite（元数据）
- **前端**：React、Vite、Refine、Ant Design

## 默认端口


| 服务     | 端口       |
| ------ | -------- |
| 后端 API | **8002** |
| 前端开发   | **5174** |


前端通过 Vite 将 `/api` 代理到 `http://127.0.0.1:8002`，浏览器访问前端即可调用接口。

## 一键启动 / 停止

在项目根目录执行（需可执行权限，首次可 `chmod +x scripts/*.sh`）：

```bash
./scripts/start.sh
```

```bash
./scripts/stop.sh
```

启动脚本会：

- 检查 8002、5174 是否已被占用
- 在 `backend` 下用虚拟环境或系统 `python3` 启动 uvicorn
- 若前端无 `node_modules` 会自动执行 `npm install`
- 将日志写入 `logs/backend.log` 与 `logs/frontend.log`

一键脚本支持用环境变量改端口：**改后端端口时**，请同步修改 `frontend/vite.config.ts` 里 `proxy['/api'].target`，否则前端代理仍指向 8002。

```bash
BACKEND_PORT=8002 FRONTEND_PORT=5174 ./scripts/start.sh
```

`FRONTEND_PORT` 会传给 Vite CLI；默认端口仍以仓库内 `vite.config.ts` 为准（当前为 5174）。

## 手动启动

**后端**（在 `backend` 目录，需已安装依赖并配置 `.env`）：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn src.main:app --host 127.0.0.1 --port 8002
```

**前端**：

```bash
cd frontend
npm install
npm run dev
```

浏览器打开：`http://127.0.0.1:5174`

## 环境变量（后端）

在 `backend/.env` 中配置，例如：

- `OPENAI_API_KEY`：LLM API 密钥（自然语言查询需要）
- `OPENAI_API_BASE_URL`：API 地址（可选，兼容 OpenAI 协议的服务）
- `OPENAI_MODEL`：模型名称

元数据默认存放在用户目录下 `~/.db_query/db_query.db`。

## 项目结构（概要）

```text
db-query/
  backend/src/     # FastAPI 应用与业务逻辑
  frontend/src/    # React 界面
  scripts/         # start.sh / stop.sh
  logs/            # 一键启动时生成的日志（可加入 .gitignore）
  specs/           # 功能说明文档
```

## 健康检查

后端就绪后可访问：`http://127.0.0.1:8002/health`