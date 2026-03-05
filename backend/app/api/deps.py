"""
@desc: 用户依赖
@character: utf-8
@file: deps.py
@time: 2026/3/3 9:19
@auther: sunscreen
@desc: 
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_access_token
from app.db.database import AsyncSessionLocal
from app.db.models import User


# 初始化OAuth2密码模式的Bearer Token验证器
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 创建数据库绘画依赖函数
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# 获取当前登录用户的核心依赖函数
async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db : AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers = {"WWW-Authenticate": "Bearer"}
    )
    try:
        # 解析JWT令牌，获取荷载
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except (JWTError, ValueError):
        raise credentials_exception

    # 异步查询数据库，根据user_id查询用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
