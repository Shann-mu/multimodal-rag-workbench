"""
@desc: llm模型初始化
@character: utf-8
@file: llm.py
@time: 2026/1/23 18:28
@auther: sunscreen
@desc: 
"""
"""LLM 模型初始化核心逻辑"""
from fastapi import HTTPException
from langchain.chat_models import init_chat_model
from app.core.config import (
    CHAT_MODEL_NAME,
    CHAT_MODEL_PROVIDER,
    CHAT_MODEL_BASE_URL,
    CHAT_MODEL_API_KEY,
)


def get_chat_model():
    try:
        model = init_chat_model(
            model=CHAT_MODEL_NAME,
            model_provider=CHAT_MODEL_PROVIDER,
            base_url=CHAT_MODEL_BASE_URL,
            api_key=CHAT_MODEL_API_KEY,
        )
        return model
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型初始化失败：{str(e)}")