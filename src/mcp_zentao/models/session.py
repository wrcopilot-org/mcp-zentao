"""
会话管理数据模型
定义禅道会话管理相关的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class SessionStatus(str, Enum):
    """会话状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


class SessionData(BaseModel):
    """SessionID 获取响应的数据部分"""
    title: Optional[str] = Field(default="", description="页面标题")
    sessionName: str = Field(description="会话名称，通常为 'zentaosid'")
    sessionID: str = Field(description="会话ID")
    rand: int = Field(description="随机数，可能用于验证")
    pager: Optional[str] = Field(default=None, description="分页信息")


class SessionResponse(BaseModel):
    """获取 SessionID 的 API 响应模型"""
    status: SessionStatus = Field(description="响应状态")
    data: str = Field(description="JSON 字符串格式的数据，需要额外解析")
    
    def get_session_data(self) -> SessionData:
        """解析 data 字段并返回 SessionData 对象"""
        import json
        parsed_data = json.loads(self.data)
        return SessionData.model_validate(parsed_data)


class LoginRequest(BaseModel):
    """用户登录请求参数"""
    account: str = Field(description="用户账号")
    password: str = Field(description="用户密码")
    verifyRand: Optional[int] = Field(default=None, description="验证随机数")
    keepLogin: Optional[int] = Field(default=0, description="是否保持登录，0=否，1=是")


class LoginResponse(BaseModel):
    """用户登录的 API 响应模型"""
    status: SessionStatus = Field(description="响应状态")
    user: dict = Field(description="用户信息，将在 UserModel 中详细定义")
    
    # 注意：这里暂时使用 dict，后续会在 user.py 中定义详细的 UserModel


class LogoutResponse(BaseModel):
    """用户登出的 API 响应模型"""
    status: SessionStatus = Field(description="响应状态")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success"
            }
        }