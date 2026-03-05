"""
@desc: 聊天历史记录接口
@character: utf-8
@file: history.py
@time: 2026/3/3 15:26
@auther: sunscreen
@desc: 
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import ChatMessage, ChatSession, User
from app.models.history_schemas import ChatMessageOut, ChatSessionCreate, ChatSessionOut

router = APIRouter(prefix="/api/chat", tags=["history"])

@router.get("/sessions",response_model=list[ChatSessionOut])
async def list_session(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 数据库查询，只查看当前登录用户的会话
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list(result.scalars().all())

@router.post("/sessions", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
        payload: ChatSessionCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    # 实例化数据库会话对象
    session = ChatSession(
        user_id = current_user.id,
        title = payload.title,
        mode = payload.mode,
        is_default = payload.is_default,
    )
    # 入库并刷新
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

@router.get("/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
async def list_message(
        session_id: int,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    # 校验会话归属
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 查询该会话的消息
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )

    # 返回结果
    return list(result.scalars().all())
















