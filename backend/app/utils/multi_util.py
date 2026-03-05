"""
@desc: 多模态
@character: utf-8
@file: multi_util.py
@time: 2026/1/24 15:23
@auther: sunscreen
@desc: 
"""
from fastapi import UploadFile
from langchain_core.messages import HumanMessage
from app.models.schemas import MessageRequest
from app.utils.audio_utils import AudioProcessor
from app.utils.image_utils import ImageProcessor


def create_multimodal_message(
        request: MessageRequest,
        image_file: UploadFile | None = None,
        audio_file: UploadFile | None =None,
        ) -> HumanMessage:
    """创建多模态消息"""
    message_content = []

    # 如果有图片
    if image_file:
        processor = ImageProcessor()
        mime_type = processor.get_image_mime_type(image_file.filename)
        base64_image = processor.image_to_base64(image_file)
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{base64_image}"
            }
        })

    # 如果有音频
    if audio_file:
        processor = AudioProcessor()
        mime_type = processor.get_audio_mime_type(audio_file.filename)
        base64_audio = processor.audio_to_base64(audio_file)
        message_content.append({
            "type": "audio_url",
            "audio_url": {
                "url": f"data:{mime_type};base64,{base64_audio}"
            }
        })

    # 处理块内容
    for i, block in enumerate(request.content_blocks):
        if block.type == "text":
            message_content.append({
                "type": "text",
                "text": block.content
            })
        elif block.type == "image":
            # 只有base64格式的消息才会被接入
            if block.content.startswith("data:image"):
                message_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": block.content
                    }
                })
        elif block.type == "audio":
            # 只有base64格式的消息才会被接入
            if block.content.startswith("data:audio"):
                message_content.append({
                    "type": "audio_url",
                    "audio_url": {
                        "url": block.content
                    }
                })
    return HumanMessage(content=message_content)