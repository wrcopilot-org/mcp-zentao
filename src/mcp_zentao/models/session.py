"""
禅道会话管理数据模型

本模块定义了禅道会话管理相关的所有数据结构，包括：
- 会话ID的获取和管理
- 用户登录和认证
- 会话状态的维护

禅道的会话管理流程：
1. 首先调用 /api-getSessionID.json 获取会话ID
2. 使用会话ID调用 /user-login-{sessionid}.json 进行用户登录
3. 登录成功后，后续API调用会自动维持会话状态
4. 可以调用 /user-logout.json 进行登出

特别说明：
- 禅道的SessionID响应中，data字段是JSON字符串，需要二次解析
- 会话ID对于所有后续API调用都是必需的
- 登录状态通过HTTP Cookie或会话机制维护
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from enum import Enum
import json

from .common import ResponseStatus, StringDataResponse, DataResponse, BaseResponse


class SessionData(BaseModel):
    """会话ID获取响应的数据部分
    
    当调用/api-getSessionID.json时，响应的data字段（JSON字符串）
    解析后包含的具体数据结构。
    
    Attributes:
        title: 页面标题，通常为空或包含系统信息
        sessionName: 会话名称，禅道固定为"zentaosid"
        sessionID: 会话ID，后续API调用的关键标识
        rand: 随机数，可能用于安全验证或防重放攻击
        pager: 分页信息，通常为None
    
    Example:
        ```python
        # 典型的会话数据
        session_data = SessionData(
            title="",
            sessionName="zentaosid",
            sessionID="abc123def456",
            rand=12345678,
            pager=None
        )
        ```
    """
    title: Optional[str] = Field(
        default="", 
        description="页面标题，通常为空字符串"
    )
    sessionName: str = Field(
        description="会话名称，禅道系统中固定为'zentaosid'"
    )
    sessionID: str = Field(
        description="会话ID，用于标识用户会话的唯一标识符"
    )
    rand: int = Field(
        description="随机数，用于安全验证，每次请求都会变化"
    )
    pager: Optional[str] = Field(
        default=None, 
        description="分页信息，在会话获取时通常为空"
    )
    
    @field_validator('sessionID')
    def validate_session_id(cls, v: str) -> str:
        """验证会话ID格式
        
        Args:
            v: 会话ID字符串
            
        Returns:
            str: 验证通过的会话ID
            
        Raises:
            ValueError: 当会话ID为空或格式不正确时
        """
        if not v or not v.strip():
            raise ValueError("会话ID不能为空")
        if len(v) < 10:  # 禅道的会话ID通常较长
            raise ValueError("会话ID长度不足，可能无效")
        return v.strip()
    
    @property
    def session_id(self) -> str:
        """获取会话ID的便捷属性
        
        Returns:
            str: 会话ID
        """
        return self.sessionID


class SessionResponse(StringDataResponse):
    """获取会话ID的API响应模型
    
    对应API: GET /api-getSessionID.json
    
    这个API的特殊之处在于data字段是JSON字符串而不是直接的对象，
    需要进行二次解析才能获得具体的会话数据。
    
    Example:
        ```python
        # API响应示例
        {
            "status": "success",
            "data": "{\"title\":\"\",\"sessionName\":\"zentaosid\",\"sessionID\":\"abc123\",\"rand\":12345}"
        }
        
        # 使用模型解析
        response = SessionResponse.model_validate(api_data)
        session_data = response.get_session_data()
        session_id = session_data.session_id
        ```
    """
    
    def get_session_data(self) -> SessionData:
        """解析data字段并返回SessionData对象
        
        将JSON字符串格式的data字段解析为结构化的SessionData对象。
        
        Returns:
            SessionData: 解析后的会话数据对象
            
        Raises:
            json.JSONDecodeError: 当data字段不是有效的JSON时
            ValidationError: 当解析后的数据不符合SessionData模型时
        """
        parsed_data = json.loads(self.data)
        return SessionData.model_validate(parsed_data)
    
    @property
    def session_id(self) -> str:
        """直接获取会话ID的便捷属性
        
        Returns:
            str: 会话ID
        """
        return self.get_session_data().session_id


class LoginRequest(BaseModel):
    """用户登录请求参数模型
    
    定义向/user-login-{sessionid}.json发送POST请求时的参数结构。
    
    Attributes:
        account: 用户账号/用户名
        password: 用户密码（明文）
        verifyRand: 验证随机数，某些情况下需要（如验证码）
        keepLogin: 是否保持登录状态
    
    Example:
        ```python
        login_req = LoginRequest(
            account="admin",
            password="123456",
            keepLogin=1  # 保持登录
        )
        ```
    """
    account: str = Field(
        min_length=1,
        max_length=100,
        description="用户账号，不能为空，最大长度100字符"
    )
    password: str = Field(
        min_length=1,
        description="用户密码，不能为空"
    )
    verifyRand: Optional[int] = Field(
        default=None, 
        description="验证随机数，在需要验证码验证时使用"
    )
    keepLogin: Optional[int] = Field(
        default=0, 
        description="是否保持登录状态，0=否，1=是"
    )
    
    @field_validator('account')
    def validate_account(cls, v: str) -> str:
        """验证账号格式
        
        Args:
            v: 账号字符串
            
        Returns:
            str: 验证通过的账号
        """
        if not v or not v.strip():
            raise ValueError("账号不能为空")
        return v.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于HTTP请求
        
        Returns:
            Dict[str, Any]: 请求参数字典
        """
        data = {
            "account": self.account,
            "password": self.password
        }
        if self.verifyRand is not None:
            data["verifyRand"] = self.verifyRand
        if self.keepLogin is not None:
            data["keepLogin"] = self.keepLogin
        return data


class LoginResponse(BaseResponse):
    """用户登录的API响应模型
    
    对应API: POST /user-login-{sessionid}.json
    
    登录成功时，响应中包含用户的详细信息。
    这里暂时使用Dict来存储用户信息，具体的用户模型在user.py中定义。
    
    Attributes:
        user: 用户信息字典，包含用户的详细信息
    
    Example:
        ```python
        # 登录成功的响应示例
        {
            "status": "success",
            "user": {
                "id": "1",
                "account": "admin",
                "realname": "管理员",
                "role": "admin",
                ...
            }
        }
        ```
    """
    user: Optional[Dict[str, Any]] = Field(
        default=None,
        description="用户信息，登录成功时包含完整的用户数据"
    )
    
    @property
    def is_logged_in(self) -> bool:
        """检查是否登录成功
        
        Returns:
            bool: 如果登录成功且包含用户信息则返回True
        """
        return self.is_success() and self.user is not None
    
    def get_user_id(self) -> Optional[str]:
        """获取用户ID
        
        Returns:
            Optional[str]: 用户ID，如果登录失败则返回None
        """
        if self.user:
            return self.user.get("id")
        return None
    
    def get_username(self) -> Optional[str]:
        """获取用户名
        
        Returns:
            Optional[str]: 用户名，如果登录失败则返回None
        """
        if self.user:
            return self.user.get("account")
        return None
    
    def get_realname(self) -> Optional[str]:
        """获取真实姓名
        
        Returns:
            Optional[str]: 真实姓名，如果登录失败则返回None
        """
        if self.user:
            return self.user.get("realname")
        return None


class LogoutResponse(BaseModel):
    """用户登出的API响应模型
    
    对应API: GET /user-logout.json
    
    登出接口相对简单，通常只返回状态信息。
    成功登出后，当前会话将失效。
    
    Example:
        ```python
        # 登出响应示例
        {
            "status": "success"
        }
        ```
    """
    status: ResponseStatus = Field(description="登出操作的状态")
    message: Optional[str] = Field(
        default=None, 
        description="可选的登出消息"
    )
    
    def is_logged_out(self) -> bool:
        """检查是否成功登出
        
        Returns:
            bool: 如果成功登出则返回True
        """
        return self.status == ResponseStatus.SUCCESS


# 会话管理的便捷类型别名
SessionID = str  # 会话ID类型别名
UserID = str     # 用户ID类型别名
    
    # 注意：这里暂时使用 dict，后续会在 user.py 中定义详细的 UserModel


class LogoutResponse(BaseModel):
    """用户登出的 API 响应模型"""
    status: ResponseStatus = Field(description="登出操作的状态")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success"
            }
        }