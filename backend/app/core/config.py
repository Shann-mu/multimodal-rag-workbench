"""
@desc: 统一配置
@character: utf-8
@file: config.py
@time: 2026/1/24 15:04
@auther: sunscreen
@desc: 
"""

import os
from dotenv import load_dotenv

_DOTENV_CANDIDATES = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")),
    os.path.abspath(os.path.join(os.getcwd(), ".env")),
]

for _dotenv_path in _DOTENV_CANDIDATES:
    if os.path.exists(_dotenv_path):
        load_dotenv(dotenv_path=_dotenv_path, override=True)
        break

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"环境变量 {name} 未设置")
    return value

# 原有数据库和JWT配置
DATABASE_URL = _require_env("DATABASE_URL")
JWT_SECRET_KEY = _require_env("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# 模型名称
CHAT_MODEL_NAME = os.getenv("CHAT_MODEL_NAME", "Qwen/Qwen3-Omni-30B-A3B-Instruct")
# 模型提供商
CHAT_MODEL_PROVIDER = os.getenv("CHAT_MODEL_PROVIDER", "openai")
# API基础地址
CHAT_MODEL_BASE_URL = os.getenv("CHAT_MODEL_BASE_URL", "https://api.siliconflow.cn/v1/")
# API密钥
CHAT_MODEL_API_KEY = _require_env("CHAT_MODEL_API_KEY")

# 控制RAG检索时返回的最相似的结果数量
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# 文本嵌入（Embedding）相关配置
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "text-embedding-3-small")
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", CHAT_MODEL_BASE_URL)
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", CHAT_MODEL_API_KEY)
EMBEDDING_DIM = int(_require_env("EMBEDDING_DIM"))

# OCR相关配置
OCR_PROVIDER = os.getenv("OCR_PROVIDER", "none")
OCR_TEXT_MIN_CHARS = int(os.getenv("OCR_TEXT_MIN_CHARS", "80"))
OCR_MAX_PAGES = int(os.getenv("OCR_MAX_PAGES", "50"))
# 百度OCR密钥配置
BAIDU_OCR_API_KEY = os.getenv("BAIDU_OCR_API_KEY", "")
BAIDU_OCR_SECRET_KEY = os.getenv("BAIDU_OCR_SECRET_KEY", "")










