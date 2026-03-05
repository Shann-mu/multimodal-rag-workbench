"""
@desc: 图像处理工具
@character: utf-8
@file: image_utils.py
@time: 2026/1/24 15:15
@auther: sunscreen
@desc: 
"""

import base64
from fastapi import UploadFile, HTTPException


class ImageProcessor:
    """图像处理工具类"""

    @staticmethod
    def image_to_base64(image_file: UploadFile) -> str:
        try:
            # 读取文件内容
            content = image_file.file.read()
            # 进行base64编码
            base64_encoded = base64.b64encode(content).decode('utf-8')
            return base64_encoded
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"图片处理失败：{str(e)}")


    @staticmethod
    def get_image_mime_type(filename: str) -> str:
        extension = filename.split('.')[-1].lower()
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'bmp': 'image/bmp',
            'webp': 'image/webp',
        }
        return mime_types.get(extension, 'image/jpeg')

