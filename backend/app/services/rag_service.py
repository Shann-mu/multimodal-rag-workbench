"""
@desc: 向量检索与知识库入库服务
@character: utf-8
@file: rag_service.py
@time: 2026/3/4 20:22
@auther: sunscreen
@desc: 
"""
import asyncio
import hashlib
import os
from typing import Optional

from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_BASE_URL,
    EMBEDDING_API_KEY,
    EMBEDDING_DIM,
)
from app.db.models import KnowledgeBase, KnowledgeDocument, KnowledgeChunk
from app.utils.pdf_utils import PDFProcessor


class RagService:
    def __init__(self):
        # 初始化嵌入模型
        self._emb = OpenAIEmbeddings(
            model=EMBEDDING_MODEL_NAME,
            api_key=EMBEDDING_API_KEY,
            base_url=EMBEDDING_BASE_URL,
        )

    async def _embed_query(self, text: str) -> list[float]:
        try:
            vec = await asyncio.to_thread(self._emb.embed_query, text)
        except Exception as e:
            raise RuntimeError(
                f"生成查询向量失败：{str(e)}；请检查 EMBEDDING_MODEL_NAME/EMBEDDING_BASE_URL/EMBEDDING_API_KEY 配置"
            )

        if not isinstance(vec, list) or not vec:
            raise RuntimeError("生成查询向量失败：返回空向量")
        if len(vec) != EMBEDDING_DIM:
            raise RuntimeError(
                "Embedding维度不匹配："
                f"期望 {EMBEDDING_DIM}，实际 {len(vec)}；"
                f"env(EMBEDDING_DIM)={os.getenv('EMBEDDING_DIM')}；"
                f"cwd={os.getcwd()}"
            )
        return vec

    async def _embed_documents(self, texts: list[str]) -> list[list[float]]:
        try:
            vectors = await asyncio.to_thread(self._emb.embed_documents, texts)
        except Exception as e:
            raise RuntimeError(
                f"生成文档向量失败：{str(e)}；请检查 EMBEDDING_MODEL_NAME/EMBEDDING_BASE_URL/EMBEDDING_API_KEY 配置"
            )

        if not isinstance(vectors, list) or not vectors:
            raise RuntimeError("生成文档向量失败：返回空结果")

        bad = [len(v) for v in vectors if not isinstance(v, list) or len(v) != EMBEDDING_DIM]
        if bad:
            raise RuntimeError(
                "Embedding维度不匹配："
                f"期望 {EMBEDDING_DIM}，实际出现 {bad[:5]}；"
                f"env(EMBEDDING_DIM)={os.getenv('EMBEDDING_DIM')}；"
                f"cwd={os.getcwd()}"
            )

        return vectors

    @staticmethod
    def _sha256(data: bytes) -> str:
        # 生成字节数据的SHA256哈希值
        return hashlib.sha256(data).hexdigest()

    async def ingest_pdf(
            self,
            db: AsyncSession,
            kb_id: int,
            filename: str,
            file_content: bytes,
    ) -> KnowledgeDocument:
        # 检验知识库是否存在
        result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        )
        kb = result.scalar_one_or_none()
        if kb is None:
            raise ValueError("知识库不存在")

        # 生成pdf哈希值，校验是否已经上传
        digest = self._sha256(file_content)
        result = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.kb_id == kb_id,
                KnowledgeDocument.sha256 == digest,
            )
        )
        existed = result.scalar_one_or_none()
        if existed is not None:
            return existed

        # 解析pdf 提取文本/OCR 分块
        processor = PDFProcessor()
        parsed = await processor.process_pdf(file_content=file_content, filename=filename)

        # 创建文档记录
        doc = KnowledgeDocument(
            kb_id=kb_id,
            filename=filename,
            title=filename,
            mime_type="application/pdf",
            sha256=digest,
            page_count=int(parsed.get("page_count") or 0),
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        # 处理文本块 生成向量并入库
        chunks: list[dict] = list(parsed.get("chunks") or [])
        if not chunks:
            return doc

        # 提取文本和元数据（过滤空文本，避免embedding服务报错）
        items: list[tuple[str, dict]] = []
        for c in chunks:
            text = (c.get("content") or "").strip()
            if not text:
                continue
            meta = c.get("metadata") or {}
            items.append((text, meta))

        if not items:
            return doc

        vectors = await self._embed_documents([t for t, _ in items])

        rows: list[KnowledgeChunk] = []
        for i, ((text, meta), vec) in enumerate(zip(items, vectors)):
            rows.append(
                KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=int(meta.get("chunk_index", i)),
                    page_number=int(meta.get("page_number", 1)),
                    content=text,
                    chunk_metadata=meta,
                    embedding=vec,
                )
            )

        # 批量插入
        if rows:
            db.add_all(rows)
            await db.commit()

        return doc

    async def retrieve(
            self,
            db: AsyncSession,
            user_id: int,
            kb_id: int,
            query: str,
            top_k: int = 5,
            document_ids: Optional[list[int]] = None,
    ) -> list[dict]:
        # 校验查询文本非空
        query = (query or "").strip()
        if not query:
            return []

        # 校验知识库归属
        result = await db.execute(
            select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        kb = result.scalar_one_or_none()
        if kb is None:
            return []

        # 生成查询向量
        qvec = await self._embed_query(query)
        # 检索最相似的文档
        distance = KnowledgeChunk.embedding.cosine_distance(qvec).label("distance")
        # 构建查询向量sql
        stmt = (
            select(KnowledgeChunk,KnowledgeDocument, distance)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .where(KnowledgeDocument.kb_id == kb_id)
            .order_by(distance.asc())
            .limit(int(top_k))
        )

        # 限定检索文档ID范围
        if document_ids:
            stmt = stmt.where(KnowledgeDocument.id.in_(document_ids))

        # 执行查询
        result = await db.execute(stmt)
        rows = result.all()

        # 格式化返回结果
        out: list[dict] = []
        for chunk, doc, dist in rows:
            out.append({
                "content": chunk.content,
                "score": float(dist) if dist is not None else None,
                "metadata":{
                    "kb_id": kb_id,
                    "document_id": doc.id,
                    "source": doc.filename,
                    "page_number": chunk.page_number,
                    "chunk_id": chunk.chunk_index,
                    "chunk_index": chunk.chunk_index,
                    "source_info": f"{doc.title or doc.filename} - 第{chunk.page_number}页",
                },
            })
        return out

    async def delete_document(self, db: AsyncSession, user_id: int ,doc_id: int) -> None:
        # 校验文档存在且归属当前用户
        result = await db.execute(
            select(KnowledgeDocument, KnowledgeBase)
            .join(KnowledgeBase, KnowledgeDocument.kb_id == KnowledgeBase.id)
            .where(
                KnowledgeDocument.id == doc_id,
                KnowledgeBase.user_id == user_id,
            )
        )
        row = result.first()
        if row is None:
            raise ValueError("文档不存在")

        # 删除文档（级联删除关联的文本块，因为外键设置了ondelete="CASCADE"）
        await db.execute(delete(KnowledgeDocument).where(KnowledgeDocument.id == doc_id))
        await db.commit()




































