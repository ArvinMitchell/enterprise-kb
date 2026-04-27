# 🧠 Enterprise Knowledge Base

> AI 驱动的企业级 RAG 知识库系统，支持文档上传、语义检索与智能问答。

## ✨ 功能特性

- 📄 **文档管理** — 拖拽上传 PDF/TXT 文件，自动分块与向量化
- 🔍 **语义检索** — 基于 BGE-M3 嵌入模型 + pgvector 向量数据库
- 💬 **智能问答** — DeepSeek V4 Flash 大模型驱动的 RAG 对话
- 🎨 **现代 UI** — Next.js 构建的精美前端界面

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Next.js 16, React, TypeScript |
| **后端** | FastAPI, Python |
| **嵌入模型** | Ollama + BGE-M3 (本地部署) |
| **大语言模型** | DeepSeek V4 Flash API |
| **向量数据库** | PostgreSQL + pgvector |
| **容器化** | Docker Compose |

## 🚀 快速开始

### 前置要求

- Python 3.9+
- Node.js 18+
- PostgreSQL (with pgvector extension)
- [Ollama](https://ollama.ai/) (本地嵌入模型)
- DeepSeek API Key

### 1. 克隆项目

```bash
git clone https://github.com/<your-username>/enterprise-kb.git
cd enterprise-kb
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 DeepSeek API Key
```

### 3. 启动数据库

```bash
docker-compose up -d
```

### 4. 启动后端

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 开始使用 🎉

## 📁 项目结构

```
enterprise-kb/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── database.py          # 数据库连接
│   ├── models.py            # SQLAlchemy 模型
│   ├── routers/             # API 路由
│   │   ├── documents.py     # 文档上传接口
│   │   └── chat.py          # 聊天接口
│   └── services/            # 业务逻辑
│       ├── document_processor.py  # 文档处理 & 向量化
│       └── chat_service.py        # RAG 对话
├── frontend/                # Next.js 前端
│   └── src/
│       ├── app/             # 页面
│       └── components/      # 组件
├── uploads/                 # 上传文件存储
├── docker-compose.yml       # PostgreSQL + pgvector
├── .env.example             # 环境变量模板
└── README.md
```

## 📝 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | (必填) |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |

## 📄 License

MIT
