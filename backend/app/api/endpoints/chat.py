"""
@desc: 聊天接口
@character: utf-8
@file: chat.py
@time: 2026/1/23 18:27
@auther: sunscreen
@desc: 
"""
import json
from typing import Optional

"""聊天接口端点（流式/同步）"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from starlette.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, SystemMessage
from app.api.deps import get_db, get_current_user
from app.core.config import RAG_TOP_K
from app.db.models import ChatMessage, ChatSession, User, KnowledgeBase
from app.models.schemas import MessageRequest, MessageResponse
from app.services.chat_service import (
    convert_history_to_messages,
    create_multimodal_message,
    generate_streaming_response,
    build_rag_context_message,
)
from app.services.rag_service import RagService

router = APIRouter(prefix="/api/chat", tags=["chat"])

async def _get_or_create_default_session(db: AsyncSession, user_id: int) -> ChatSession:
    """为指定用户查找或创建默认的聊天会话，有则返回，无则创建"""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.user_id == user_id, # 条件1：匹配指定用户id
            ChatSession.is_default.is_(True) # 条件2： 匹配默认会话
        ).limit(1)
    )
    session = result.scalar_one_or_none()

    # 如果没有默认会话，就创建一个
    if session is None:
        session = ChatSession(
            user_id = user_id,
            title = "默认会话",
            mode = "multimodal",
            is_default = True
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
    return session


async def _load_session_history(db: AsyncSession, session_id: int, limit: int = 50) -> list[dict]:
    """从数据库中加载聊天会话的历史消息"""
    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.session_id == session_id
        ).order_by(
            ChatMessage.created_at.asc()
        ).limit(limit)
    )
    # 查询结果为ChatMessage对象列表
    rows = result.scalars().all()
    # 初始化空列表用于村塾格式化后的消息数据
    history_data: list[dict] = []
    # 遍历消息对象，格式为统一的字典结构
    for row in rows:
        history_data.append(
            {
                "role": row.role,
                "content": row.content,
                "content_blocks": row.content_blocks or [],
            }
        )
    return history_data


def _extract_text_from_blocks(content_blocks_data: list[dict]) -> str:
    """处理多模态消息中的纯文本内容提取"""
    parts: list[str] = []
    for block in content_blocks_data:
        if block.get("type") == "text":
            parts.append(block.get("content", ""))
    return "\n".join([p for p in parts if p]).strip()

async def _get_or_create_default_kb(db: AsyncSession, user_id: int) -> KnowledgeBase:
    """为指定用户查找或创建默认的知识库，有则返回，无则创建"""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.user_id == user_id, # 匹配指定用户id
            KnowledgeBase.is_default.is_(True) # 匹配默认知识库
        ).limit(1)
    )
    kb = result.scalar_one_or_none()

    # 如果没有默认知识库，就创建一个
    if kb is None:
        kb = KnowledgeBase(
            user_id = user_id,
            name = "默认知识库",
            description = "",
            is_default = True
        )
        db.add(kb)
        await db.commit()
        await db.refresh(kb)
    return kb

@router.post("/stream")
async def chat_stream(
        image_file: Optional[UploadFile] = File(default=None),
        audio_file: UploadFile | None = File(None),
        pdf_file: UploadFile | None = File(None),
        kb_id: int | None = Form(default=None),
        document_ids: str | None = Form(default="[]"),
        content_blocks: str = Form(default="[]"),
        history: str = Form(default="[]"),
        session_id: int |None = Form(default=None),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """流式聊天接口（支持多模态）"""
    try:
        try:
            content_blocks_data = json.loads(content_blocks)
            # history_data = json.loads(history)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"JSON解析错误{str(e)}")

        if session_id is None:
            session = await _get_or_create_default_session(db, current_user.id)
        else:
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == session_id,
                                          ChatSession.user_id == current_user.id)
            )
            session = result.scalar_one_or_none()
            if session is None:
                raise HTTPException(status_code=404, detail="会话不存在")
        history_data = await _load_session_history(db, session.id)

        request_data = MessageRequest(content_blocks=content_blocks_data, history=history_data)

        # 解析前端传入的document_ids
        doc_ids: list[int] = []
        try:
            # 解析JSON字符串为列表，无值则默认空列表
            parsed = json.loads(document_ids or "[]")
            # 确保解析结果是列表，无值则默认空列表
            if isinstance(parsed, list):
                doc_ids = [int(x) for x in parsed]
        except Exception:
            # 解析失败则置为空列表
            doc_ids = []

        # 确定要使用的知识库(kb)
        kb: KnowledgeBase | None = None
        if kb_id is not None:
            # 前端指定了知识库id 验证该知识库是否属于当前用户
            result = await db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.id == kb_id,
                    KnowledgeBase.user_id == current_user.id
                )
            )
            kb = result.scalar_one_or_none()
            if kb is None:
                raise HTTPException(status_code=404, detail="知识库不存在")
        elif pdf_file is not None:
            # 前端未指定知识库，但上传了PDF 创建用户的默认知识库
            kb = await _get_or_create_default_kb(db, current_user.id)

        # 初始化rag服务
        rag = RagService()

        # 如果有PDF文件且已经确定知识库 处理pdf并入库
        if pdf_file is not None and kb is not None:
            # 读取pdf文件的字节内容
            pdf_bytes = await pdf_file.read()
            # 调用rag服务的ingest_pdf方法： 将pdf解析、分块、生成向量后入库到指定知识库
            await rag.ingest_pdf(
                db=db,
                kb_id=kb.id,
                filename=pdf_file.filename or "document.pdf",
                file_content=pdf_bytes
            )

        user_text = _extract_text_from_blocks(content_blocks_data)
        db.add(
            ChatMessage(
                session_id=session.id,
                role="user",
                content=user_text,
                content_blocks=content_blocks_data,
            )
        )
        await db.commit()

        messages = convert_history_to_messages(request_data.history)

        rag_chunks: list[dict] = []
        rag_context_text: str | None = None

        if kb is not None and user_text:
            rag_chunks = await rag.retrieve(
                db=db,
                user_id=current_user.id,
                kb_id=kb.id,
                query=user_text,
                top_k=RAG_TOP_K,
                document_ids=doc_ids or None,
            )

            if rag_chunks:
                ctx = build_rag_context_message(rag_chunks)
                rag_context_text = ctx.content

                if messages and isinstance(messages[0], SystemMessage):
                    messages[0] = SystemMessage(content=f"{messages[0].content}\n\n{ctx.content}")
                else:
                    messages.insert(0, ctx)

        current_message = create_multimodal_message(request_data, image_file=image_file, audio_file=audio_file)
        if rag_context_text:
            if isinstance(current_message.content, list):
                patched: list[dict] = []
                inserted = False
                for item in current_message.content:
                    if (
                        not inserted
                        and isinstance(item, dict)
                        and item.get("type") == "text"
                    ):
                        new_item = dict(item)
                        new_item["text"] = f"{new_item.get('text', '')}\n\n{rag_context_text}"
                        patched.append(new_item)
                        inserted = True
                    else:
                        patched.append(item)

                if not inserted:
                    patched.append({"type": "text", "text": rag_context_text})

                current_message = HumanMessage(content=patched)
            else:
                current_message = HumanMessage(content=f"{current_message.content}\n\n{rag_context_text}")

        messages.append(current_message)

        async def _stream_with_persist():
            """流式返回聊天响应，并在响应完全结束后持久化保存到数据库中"""
            yield f"data: {json.dumps({'type':'session','session_id':session.id}, ensure_ascii=False)}\n\n"

            # 初始变量： 存储完整的助手回复和引用信息
            assistant_full: str | None = None # 完整的助手回复文本
            assistant_refs: list | None = None # 助手回复的引用信息
            # 调用流式生成响应的函数，逐块获取AI回复
            async for chunk in generate_streaming_response(
                messages, # 聊天历史消息
                rag_chunks =rag_chunks if rag_chunks else None,
            ):
                # 把当前chunk推送给客户端实现流式输出
                yield chunk
                # 解析chunk，提取完整的回复内容
                if isinstance(chunk, str) and chunk.startswith("data: "):
                    # 去掉SSE格式的前缀“data：”，清理空白字符
                    payload = chunk[6:].strip()
                    try:
                        # 解析JSON格式的相应内容
                        data = json.loads(payload)
                    except Exception:
                        # 解析失败则跳过，避免格式异常导致程序中断
                        continue
                    # 识别消息完成的表示
                    if data.get("type") == "message_complete":
                        # 提取完整回复内容和引用信息
                        assistant_full = data.get("full_content", "")
                        assistant_refs = data.get("references", [])

            # 流式响应返回完毕，持久化到数据库
            if assistant_full is not None:
                # 创建ChatMessage对象
                db.add(
                    ChatMessage(
                        session_id = session.id, # 关联当前会话ID
                        role = "assistant", # 角色为智能助手
                        content=assistant_full, # 完整的回复文本
                        references=assistant_refs or [] # 引用信息
                    )
                )
                # 异步提交数据库事务，完成保存
                await db.commit()


        return StreamingResponse(
            _stream_with_persist(),
            media_type="text/event_stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天失败：{str(e)}")




















