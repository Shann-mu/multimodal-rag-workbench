"""
@desc: 视频处理工具
@character: utf-8
@file: audio_utils.py
@time: 2026/1/24 16:33
@auther: sunscreen
@desc: 
"""
import base64

from fastapi import UploadFile, HTTPException


class AudioProcessor:
    """音频处理工具类"""

    @staticmethod
    def audio_to_base64(audio_file: UploadFile) -> str:
        try:
            # 验证文件类型
            if not AudioProcessor.is_valid_audio_type(audio_file.content_type, audio_file.filename):
                raise HTTPException(status_code=400, detail="不支持的音频格式，支持的格式有：MP3, WAV, OGG, M4A, FLAC")

            # 读取文件内容
            contents = audio_file.file.read()

            # 验证文件大小
            max_size = 10 * 1024 * 1024
            if len(contents) > max_size:
                raise HTTPException(status_code=400, detail="音频文件大小超出限制，最大支持10MB")

            base64_encoded = base64.b64encode(contents).decode('utf-8')
            return base64_encoded
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"音频处理失败：{str(e)}")

    @staticmethod
    def get_audio_mime_type(filename: str) -> str:
        extension = filename.split('.')[-1].lower()
        mime_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': '/mp4',
        }
        return mime_types.get(extension, 'audio/mpeg')

    @staticmethod
    def is_valid_audio_type(content_type: str, filename: str) -> bool:
        """获取支持的MIME类型列表"""
        support_mimes = {
            'audio/mpeg', 'audio/wav', 'audio/mp4'
        }

        # 检查conten_type
        if content_type and content_type in support_mimes:
            return True

        # 检查文件扩展名
        file_extension = filename.split('.')[-1].lower()
        supported_extensions = {
            'mp3', 'wav', 'm4a'
        }
        return file_extension in supported_extensions
