"""
@desc: 知识库管理接口
@character: utf-8
@file: main.py
@time: 2026/1/23 18:32
@auther: sunscreen
@desc: 
"""

"""FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.api.endpoints.chat import router as chat_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.history import router as history_router
from app.api.endpoints.kb import router as kb_router
from app.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

# 初始化 FastAPI 实例
app = FastAPI(
    title="多模态 RAG 工作台 API",
    description="基于 LangChain 1.0 的智能对话 API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(kb_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True  # 开发模式热重载
    )