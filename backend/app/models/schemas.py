"""
@desc: 数据结构定义(pydantic模型)
@character: utf-8
@file: schemas.py
@time: 2026/1/23 18:28
@auther: sunscreen
@desc: 
"""
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    type: str = Field(description="内容类型：text，image，audio")
    content: str = Field(description="内容数据")

class MessageRequest(BaseModel):
    content_blocks: List[ContentBlock] = Field(default=[], description="内容块")
    history: List[Dict[str, Any]] = Field(default=[], description="对话历史")
    pdf_chunks: List[Dict[str, Any]] = Field(default=[], description="PDF分块")

class MessageResponse(BaseModel):
    content: str
    timestamp: str
    role: str
    references: List[Dict[str, Any]] # PDF的引用
