"""
@desc: 初始化数据库
@character: utf-8
@file: init_db.py
@time: 2026/3/3 8:22
@auther: sunscreen
@desc: 
"""

from sqlalchemy import text
from app.core.config import EMBEDDING_DIM
from app.db.database import Base, engine
import app.db.models

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS knowledge_bases_user_id_idx ON knowledge_bases (user_id)"))
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS knowledge_documents_kb_id_idx ON knowledge_documents (kb_id)"))
        await conn.execute(
            text("CREATE INDEX IF NOT EXISTS knowledge_chunks_document_id_idx ON knowledge_chunks (document_id)"))
        if EMBEDDING_DIM <= 2000:
            await conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_ivfflat_idx "
                    "ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
                )
            )