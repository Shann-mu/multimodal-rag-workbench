"""
@desc: 登录注册接口
@character: utf-8
@file: auth.py
@time: 2026/3/3 9:42
@auther: sunscreen
@desc: 
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_db  # 数据库会话、当前用户认证依赖
from app.core.security import create_access_token, hash_password, verify_password  # 密码加密/令牌生成
from app.db.models import User  # 用户数据库模型
from app.models.auth_schemas import LoginRequest, Token, UserCreate, UserPublic  # 数据校验/响应模型

# 创建路由
router = APIRouter(prefix="/api/auth", tags=["auth"])

# 注册接口 POST /api/auth/register
@router.post("/register", response_model=UserPublic)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")

    # 创建新用户
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        avatar_url=data.avatar_url,
    )
    # 将对象添加到数据库会话
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserPublic(id=user.id, username=user.username, avatar_url=user.avatar_url)

# 登录接口 POST /api/auth/login
@router.post("/login", response_model=Token)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否存在
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成访问令牌
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)

# 获取当前用户 GET /api/auth/me
@router.get("/me", response_model=UserPublic)
async def me(current_user: User = Depends(get_current_user)):
    return UserPublic(id=current_user.id, username=current_user.username, avatar_url=current_user.avatar_url)










