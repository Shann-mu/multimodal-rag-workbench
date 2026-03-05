"""
@desc: 用户密码加密及jwt
@character: utf-8
@file: security.py
@time: 2026/3/3 9:07
@auther: sunscreen
@desc: 
"""
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES,JWT_SECRET_KEY,JWT_ALGORITHM

# 初始密码加密上下文，使用bcrypt算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 将铭文密码转为不可逆的哈希字符串
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 密码验证函数
def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

# 生成JWT访问令牌函数
def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    # 计算令牌过期时间： 当前utc时间 + 过期分钟数
    expire = datetime.now(timezone.utc) + timedelta(minutes = expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES)
    # JWT载荷，包含用户表示和过期时间
    payload = {"sub" : subject, "exp" : expire}
    # 加密生成JWT令牌
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm = JWT_ALGORITHM)

# 解析JWT访问令牌函数
def decode_access_token(token: str) -> str:
    return jwt.decode(token, JWT_SECRET_KEY, algorithms = [JWT_ALGORITHM])


