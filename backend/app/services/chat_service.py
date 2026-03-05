"""
@desc: 聊天业务逻辑
@character: utf-8
@file: chat_service.py
@time: 2026/1/23 18:30
@auther: sunscreen
@desc: 
"""
from app.utils.multi_util import create_multimodal_message

"""聊天业务逻辑层（多模态消息处理、流式响应生成）"""
from datetime import datetime
import json
import re
from typing import Dict, List, Any, AsyncGenerator
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage, AIMessage
from app.models.schemas import MessageRequest
from app.core.llm import get_chat_model

def convert_history_to_messages(history: List[Dict[str, Any]]) -> List[BaseMessage]:
    """将历史记录转换为LangChain消息格式，支持多模态"""
    messages = []

    # 系统提示词
    system_prompt = """
            你是一个专业的多模态 RAG 助手，具备如下能：
            1. 与用户对话的能力。
            2. 图像内容识别和分析能力(OCR, 对象检测， 场景理解)
            3. 音频转写与分析
            4. 知识检索与问答

            重要指导原则：
            - 当用户上传图片并提出问题时，请结合图片内容和用户的具体问题来回答
            - 仔细分析图片中的文字、图表、对象、场景等所有可见信息
            - 根据用户的问题重点，有针对性地分析图片相关部分
            - 如果图片包含文字，请准确识别并在回答中引用
            - 如果用户只上传图片没有问题，则提供图片的全面分析

            引用格式要求（重要）：
            - 当回答基于提供的参考资料时，必须在相关信息后添加引用标记，格式为[1]、[2]等
            - 引用标记应紧跟在相关内容后面，如："这是重要信息[1]"
            - 引用编号必须与“参考资料”里方括号编号一一对应（1-based）
            - 只需要在正文中使用角标引用，不需要在最后列出"参考来源"
            - 不要在回答里写“未收到资料/请提供资料/请上传资料”等句子；系统已经提供了参考资料
            - 如果资料不足以得出结论，请明确说明“参考资料不足以回答该问题”，并说明缺少什么

            请以专业、准确、友好的方式回答，并严格遵循引用格式。当有参考资料时，必须优先使用资料内容回答。
        """

    messages.append(SystemMessage(content=system_prompt))

    # 转换历史消息
    for i, msg in enumerate(history):
        content = msg.get("content", "")
        content_blocks = msg.get("content_blocks", [])
        message_content = []
        if msg["role"] == "user":
            for block in content_blocks:
                if block.get("type") == "text":
                    message_content.append({
                        "type": "text",
                        "text": block.get("content", "")
                    })
                elif block.get("type") == "image":
                    image_data = block.get("content", "")
                    if image_data.startswith("data:image"):
                        message_content.append({
                            "type": "image_url",
                            "image_url":{
                                "url": image_data
                            }
                        })
                elif block.get("type") == "audio":
                    audio_data = block.get("content", "")
                    if audio_data.startswith("data:audio"):
                        message_content.append({
                            "type": "audio_url",
                            "audio_url":{
                                "url": audio_data
                            }
                        })
            messages.append(HumanMessage(content=message_content))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=content))
    return messages

def extract_references_from_content(content: str, rag_chunks: list | None = None) -> list:
    references = []

    if not content or not rag_chunks:
        return references

    seen: set[int] = set()
    for m in re.finditer(r"\[(\d+)\]", content):
        ref_num = int(m.group(1))

        left = content[max(0, m.start() - 6): m.start()]
        right = content[m.end(): m.end() + 6]
        left_compact = left.replace(" ", "").replace("\n", "")
        right_compact = right.replace(" ", "").replace("\n", "")

        # 过滤示例性引用：如[1]、[2]等 / 例如[1]
        if left_compact.endswith("如") or left_compact.endswith("例如") or left_compact.endswith("比如"):
            continue
        if "如[" in left_compact or "例如[" in left_compact or "比如[" in left_compact:
            continue
        if right_compact.startswith("、") or right_compact.startswith("等"):
            continue

        if ref_num in seen:
            continue
        idx = ref_num - 1
        if 0 <= idx < len(rag_chunks):
            chunk = rag_chunks[idx]
            meta = chunk.get("metadata", {})
            text = chunk.get("content", "")
            references.append(
                {
                    "id": ref_num,
                    "text": (text[:200] + "...") if len(text) > 200 else text,
                    "source": meta.get("source", "未知来源"),
                    "page": meta.get("page_number", 1),
                    "chunk_id": meta.get("chunk_id", meta.get("chunk_index", 0)),
                    "document_id": meta.get("document_id"),
                    "source_info": meta.get("source_info", "未知来源"),
                }
            )
            seen.add(ref_num)

    return references

def build_rag_context_message(rag_chunks: list[dict]) -> SystemMessage:
    """构建rag参考资料上下文"""
    lines: list[str] = ["===参考资料（已提供）==="]
    # 遍历rag检索结果，按1-based编号构建参考资料
    for i, chunk in enumerate(rag_chunks, start=1):
        content = (chunk.get("content") or "").strip()
        meta = chunk.get("metadata", {})
        source_info = meta.get("source_info") or meta.get("source") or "未知来源"
        lines.append(f"[{i}] {content}\n来源：{source_info}")

    lines.append(
        "\n要求：你已经收到参考资料，必须基于参考资料回答，不要说\"未收到资料/请提供资料\"。"
        "若资料不足以回答，请明确说明\"参考资料不足以回答\"并说明缺少什么。"
        "引用必须用[1]、[2]等且编号与资料一致。"
    )
    return SystemMessage(content="\n\n".join(lines))



async def generate_streaming_response(
        message: List[BaseMessage],
        rag_chunks: List[Dict[str, Any]] = None
) -> AsyncGenerator[str, None]:
    """生成流式响应"""
    try:
        model = get_chat_model()
        full_response = ""
        chunk_count = 0
        async for chunk in model.astream(message):
            chunk_count += 1
            if hasattr(chunk, 'content') and chunk.content:
                content = chunk.content
                full_response += content
                # 流式返回chunk
                data = {
                    "type": "content_delta",
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

        # 提取引用信息
        reference = extract_references_from_content(full_response, rag_chunks) if rag_chunks else []

        # 发送完成信号
        final_data = {
            "type": "message_complete",
            "full_content": full_response,
            "references": reference,
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(final_data, ensure_ascii=False)}\n\n"
    except Exception as e:
        error_data = {
            "type": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"


async def get_sync_chat_response(request: MessageRequest) -> dict:
    """同步聊天响应逻辑"""
    messages = convert_history_to_messages(request.history)
    current_message = create_multimodal_message(request)
    messages.append(current_message)
    model = get_chat_model()
    response = await model.ainvoke(messages)
    return {
        "content": response.content,
        "timestamp": datetime.now().isoformat(),
        "role": "assistant",
        "references": [],
    }

