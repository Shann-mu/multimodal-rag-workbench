"""
@desc: 规范聊天会话
@character: utf-8
@file: history_schemas.py
@time: 2026/3/3 15:20
@auther: sunscreen
@desc: 
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

class ChatSessionCreate(BaseModel):
    title: str = Field(default="默认会话", max_length=200)
    mode: str = Field(default="multimodal", max_length=50)
    is_default: bool = False

class ChatSessionOut(BaseModel):
    id: int
    title: str
    mode: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    content_blocks: Optional[Any] = None
    references: Optional[List[Any]] = None
    created_at: datetime









