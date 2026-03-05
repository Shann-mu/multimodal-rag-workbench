"""
@desc: pdf处理工具
@character: utf-8
@file: pdf_utils.py
@time: 2026/2/2 14:50
@auther: sunscreen
@desc: 
"""

import base64
import time
import fitz
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import httpx

from app.core.config import(
    OCR_PROVIDER,
    OCR_TEXT_MIN_CHARS,
    OCR_MAX_PAGES,
    BAIDU_OCR_API_KEY,
    BAIDU_OCR_SECRET_KEY,
)

# 全局变量缓存百度OCR的access_token，避免重复请求
_baidu_token: dict | None = None

class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 200,
            separators = ["\n\n", "\n", " ", ""],
        )

    @staticmethod
    # PDF页面转图片
    async def extract_pdf_pages_as_image(file_content: bytes, max_pages: int = 5) -> List[str]:
        # 使用fitz打开PDF字节流
        pdf_document = fitz.open(stream=file_content, filetype="pdf")
        total_pages = len(pdf_document)
        # 限制提取页数，避免处理超大PDF
        pages_to_extract = min(max_pages,total_pages)
        images = []
        for page_num in range(pages_to_extract):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap()
            png_bytes = pix.tobytes("png")
            images.append(base64.b64encode(png_bytes).decode("utf-8"))
        pdf_document.close()
        return images

    @staticmethod
    async def extract_pdf_pages_as_images(file_content: bytes, max_pages: int = 5) -> List[str]:
        return await PDFProcessor.extract_pdf_pages_as_image(file_content=file_content, max_pages=max_pages)

    async def _baidu_get_access_token(self) -> str:
        """百度令牌获取并缓存"""
        global _baidu_token
        # 缓存有效（令牌存在且距离过期还有30秒以上）
        if _baidu_token and _baidu_token.get("expires_at", 0) > time.time() + 30:
            return _baidu_token["access_token"]

        # 校验配置（缺少密钥则抛出异常）
        if not BAIDU_OCR_API_KEY or not BAIDU_OCR_SECRET_KEY:
            raise RuntimeError("百度OCR密钥未配置")

        # 异步请求百度OCR令牌接口
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://aip.baidubce.com/oauth/2.0/token",
                params={
                    "grant_type": "client_credentials",
                    "client_id": BAIDU_OCR_API_KEY,
                    "client_secret": BAIDU_OCR_SECRET_KEY,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        # 缓存令牌和过期时间
        access_token = data["access_token"]
        expires_in = int(data.get("expires_in", 0))
        _baidu_token = {
            "access_token": access_token,
            "expires_at": time.time() + max(expires_in,0),
        }
        return access_token

    async def _baidu_ocr_image(self, image_bytes: bytes) -> str:
        """百度ocr图片识别"""
        access_token = await self._baidu_get_access_token()
        # 异步调用百度通用ocr接口
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic",
                params={"access_token": access_token},
                data={"image": base64.b64encode(image_bytes).decode("utf-8")},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()

        # 提取识别结果中的文字，拼接成字符串
        words = [w.get("words", "") for w in data.get("words_result", [])]
        return "\n".join([w for w in words if w]).strip()

    async def _ocr_page_texts(self, doc: fitz.Document) -> dict[int, str]:
        """ocr识别pdf所有页面文本"""
        pages: dict[int, str] = {}
        page_count = len(doc)
        # 限制OCR处理的最大页数
        limit = min(page_count, max(OCR_MAX_PAGES,0) or page_count)

        # 遍历每页，调用OCR识别
        for page_index in range(limit):
            page = doc.load_page(page_index)
            pix = page.get_pixmap()
            png_bytes = pix.tobytes("png")

            if OCR_PROVIDER == "baidu":
                text = await self._baidu_ocr_image(png_bytes)
            else:
                raise RuntimeError(f"不支持的OCR提供商：{OCR_PROVIDER}")

            pages[page_index + 1] = text

        # 未处理的页面重码空字符串
        for page_index in range(limit, page_count):
            pages[page_index + 1] = ""

        return pages

    async def process_pdf(self, file_content: bytes, filename: str) -> dict:
        """处理pdf并生成文本块"""
        doc = fitz.open(stream=file_content, filetype="pdf")
        page_count = len(doc)

        # 尝试直接提取pdf文本
        pages_content: dict[int, str] = {}
        full_text_parts: list[str] = []
        for page_index in range(page_count):
            page = doc.load_page(page_index)
            text = (page.get_text() or "").strip()
            pages_content[page_index + 1] = text
            if text:
                full_text_parts.append(text)

        full_text = "\n".join(full_text_parts).strip()
        extraction = "text"

        # 若文本长度不足阈值，出发OCR
        if OCR_PROVIDER != "none" and len(full_text) < OCR_TEXT_MIN_CHARS:
            pages_content = await self._ocr_page_texts(doc)
            extraction = "ocr"

        doc.close()

        # 拆解文本为chunk
        chunks: list[dict] = []
        chunk_index = 0
        for page_number in range(1, page_count+1):
            page_text = (pages_content.get(page_number) or "").strip()
            if not page_text:
                continue

            # 用初始化的分割器拆分当前文本
            for part in self.text_splitter.split_text(page_text):
                content = (part or "").strip()
                if not content:
                    continue

                # 创建chunk字典，包含内容和元组
                chunks.append(
                    {
                        "content": content,
                        "metadata": {
                            "source": filename,
                            "chunk_index": chunk_index,
                            "chunk_size": len(content),
                            "page_number": page_number,
                            "source_info": f"{filename} - 第{page_number}页",
                            "extraction": extraction,
                        },
                    }
                )
                chunk_index += 1
        # 返回处理结果
        return{
            "filename": filename,
            "page_count": page_count,
            "extraction": extraction,
            "chunks": chunks,
        }















