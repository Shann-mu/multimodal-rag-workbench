# 多模态 RAG 工作台

基于 FastAPI + LangChain 的后端与 React + Vite 的前端，提供多模态对话、知识库管理与 RAG 检索能力。

## ✨ 核心特性

- 多模态对话（文本/图片/音频）
- 知识库创建与文档上传
- 基于向量检索的 RAG 增强回答
- 用户注册登录与会话历史
- 向量入库与检索的异步处理

## 🛠️ 技术栈

### 前端

- React 19 + TypeScript
- Vite
- Ant Design + Tailwind CSS
- Axios

### 后端

- FastAPI
- SQLAlchemy 2.0（异步）
- LangChain
- pgvector
- python-multipart
- python-jose

### 数据库

- PostgreSQL 14+（需启用 pgvector 扩展）

## 📁 项目结构

```
.
├─ backend/                后端服务（FastAPI）
│  ├─ app/                 业务代码（路由/服务/模型）
│  ├─ main.py              应用入口
│  └─ requirement.txt      后端依赖
└─ frontend/               前端应用（Vite + React）
   ├─ src/                 前端源码（组件/状态/接口）
   └─ package.json         前端依赖与脚本
```

## 🚀 快速开始

### 前置条件

1. Python 3.10+
2. Node.js 18+
3. PostgreSQL 14+（建议提前安装 pgvector 扩展，后端启动时会尝试自动创建）
4. Git

### 1. 克隆项目

```bash
git clone https://github.com/你的用户名/多模态RAG工作台.git
cd 多模态RAG工作台
```

### 2. 后端部署

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirement.txt
```

### 3. 配置环境变量

在仓库根目录或 backend/ 目录创建 .env，确保下列环境变量已配置。

### 4. 启动后端服务

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API 文档：http://localhost:8000/docs

### 5. 前端部署

```bash
cd ../frontend
npm install
npm run dev
```

- 前端访问地址：http://localhost:5173

## ⚙️ 环境变量说明

建议在仓库根目录或 backend/ 目录创建 .env，后端会自动加载。

### 后端（.env）

| 变量名 | 必填 | 说明 | 示例 |
| --- | --- | --- | --- |
| DATABASE_URL | ✅ | PostgreSQL 连接串（需启用 pgvector） | postgresql+asyncpg://user:password@localhost:5432/rag_db |
| JWT_SECRET_KEY | ✅ | JWT 密钥 | 32位以上随机字符串 |
| JWT_ALGORITHM | ❌ | JWT 算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | ❌ | 令牌有效期（分钟） | 1440 |
| CHAT_MODEL_NAME | ❌ | 对话模型名称 | Qwen/Qwen3-Omni-30B-A3B-Instruct |
| CHAT_MODEL_PROVIDER | ❌ | 模型提供商 | openai |
| CHAT_MODEL_BASE_URL | ❌ | 模型 API Base URL | https://api.siliconflow.cn/v1/ |
| CHAT_MODEL_API_KEY | ✅ | 模型 API Key | sk-xxx |
| RAG_TOP_K | ❌ | RAG 检索返回条数 | 5 |
| EMBEDDING_MODEL_NAME | ❌ | 向量模型名称 | text-embedding-3-small |
| EMBEDDING_BASE_URL | ❌ | 向量模型 Base URL | https://api.siliconflow.cn/v1/ |
| EMBEDDING_API_KEY | ✅ | 向量模型 API Key | sk-xxx |
| EMBEDDING_DIM | ✅ | 向量维度 | 1536 |
| OCR_PROVIDER | ❌ | OCR 提供商 | none |
| OCR_TEXT_MIN_CHARS | ❌ | OCR 最短字符数阈值 | 80 |
| OCR_MAX_PAGES | ❌ | OCR 最大页数 | 50 |
| BAIDU_OCR_API_KEY | ❌ | 百度 OCR API Key | xxxx |
| BAIDU_OCR_SECRET_KEY | ❌ | 百度 OCR Secret Key | xxxx |

## 🧰 常用脚本

前端：

```bash
npm run dev
npm run build
npm run lint
```

## 📌 备注

- 上传文档会暂存于 backend/temp/，请确保该目录可写

