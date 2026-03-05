"""
@desc: 程序的入口
@character: utf-8
@file: kb.py
@time: 2026/3/4 21:07
@auther: sunscreen
@desc: 
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.db.models import User, KnowledgeBase, KnowledgeDocument
from app.services.rag_service import RagService

router = APIRouter(prefix="/api/kb", tags=["kb"])


# 知识库创建的输入模型（前端传参校验）
class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)  # 名称非空，长度限制
    description: str = Field(default="", max_length=5000)  # 描述可选，最大5000字符

# 知识库的输出模型（接口返回数据格式）
class KnowledgeBaseOut(BaseModel):
    id: int
    name: str
    description: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

# 文档的输出模型（接口返回数据格式）
class KnowledgeDocumentOut(BaseModel):
    id: int
    kb_id: int
    filename: str
    title: str
    mime_type: str
    sha256: str
    page_count: int
    created_at: datetime

@router.post("", response_model=KnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
async def create_kb(
    payload: KnowledgeBaseCreate,  # 前端传入的创建参数（自动校验）
    db: AsyncSession = Depends(get_db),  # 注入数据库会话
    current_user: User = Depends(get_current_user),  # 注入当前登录用户
):
    # 实例化知识库模型，关联当前用户
    kb = KnowledgeBase(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        is_default=False,  # 手动创建的知识库默认不是默认库
    )
    db.add(kb)  # 添加到会话
    await db.commit()  # 提交入库
    await db.refresh(kb)  # 刷新获取自动生成的字段（id/created_at等）
    return kb  # 自动序列化为KnowledgeBaseOut格式

@router.get("", response_model=list[KnowledgeBaseOut])
async def list_kb(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 查询当前用户的所有知识库，按更新时间降序排列
    result = await db.execute(
        select(KnowledgeBase)
        .where(KnowledgeBase.user_id == current_user.id)
        .order_by(KnowledgeBase.updated_at.desc())
    )
    # 转换为列表并自动序列化为KnowledgeBaseOut格式
    return list(result.scalars().all())

@router.get("/{kb_id}/documents", response_model=list[KnowledgeDocumentOut])
async def list_documents(
    kb_id: int,  # 路径参数：知识库ID
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 第一步：校验知识库是否存在且属于当前用户
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 第二步：查询该知识库下的所有文档，按创建时间降序
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.kb_id == kb_id)
        .order_by(KnowledgeDocument.created_at.desc())
    )
    return list(result.scalars().all())

@router.post("/{kb_id}/documents", response_model=KnowledgeDocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: int,  # 目标知识库ID
    pdf_file: UploadFile = File(...),  # 上传的PDF文件（必填）
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 校验知识库是否存在且属于当前用户
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id,
        )
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 读取PDF文件字节内容
    data = await pdf_file.read()
    # 调用RagService的ingest_pdf方法入库
    rag = RagService()
    try:
        doc = await rag.ingest_pdf(
            db=db,
            kb_id=kb_id,
            filename=pdf_file.filename or "document.pdf",
            file_content=data
        )
    except Exception as e:
        # 入库失败返回500错误，附带具体原因
        raise HTTPException(status_code=500, detail=f"入库失败：{str(e)}")

    return doc  # 返回文档信息

@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: int,  # 要删除的文档ID
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rag = RagService()
    try:
        # 调用RagService的delete_document方法删除（自动校验归属）
        await rag.delete_document(db=db, user_id=current_user.id, doc_id=doc_id)
    except ValueError as e:
        # 文档不存在返回404
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 其他错误返回500
        raise HTTPException(status_code=500, detail=f"删除失败：{str(e)}")

























