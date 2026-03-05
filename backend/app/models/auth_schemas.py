"""
@desc: 数据模型
@character: utf-8
@file: auth_schemas.py
@time: 2026/3/3 9:36
@auther: sunscreen
@desc: 
"""
from pydantic import BaseModel, Field
from pydantic.v1.validators import max_str_int


# 用户创建的请求模型
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    avatar_url: str | None = None

# 用户信息的公共返回模型
class UserPublic(BaseModel):
    id: int
    username: str
    avatar_url: str | None = None

# 用户登录的请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

# 用户登录成功后返回的令牌模型
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"






