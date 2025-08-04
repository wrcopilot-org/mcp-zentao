"""
禅道会话管理客户端

提供会话ID获取、用户登录/登出等功能。
"""

from typing import Optional
from .base_client import BaseClient
from ..models.session import SessionResponse, LoginRequest, LoginResponse, LogoutResponse
from ..models.user import UserDetailResponse


class SessionClient(BaseClient):
    """禅道会话管理客户端
    
    负责处理会话ID获取、用户认证等会话相关操作。
    """
    
    def get_session_id(self) -> str:
        """获取会话ID
        
        Returns:
            会话ID字符串
            
        Raises:
            ZenTaoError: 获取会话ID失败
        """
        response = self.get(
            endpoint='api-getSessionID.json',
            response_model=SessionResponse
        )
        
        # 提取并存储会话ID
        session_data = response.get_session_data()
        self.session_id = session_data.sessionID
        
        return session_data.sessionID
    
    def login(self, username: str, password: str) -> UserDetailResponse:
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户详细信息
            
        Raises:
            ZenTaoError: 登录失败
        """
        # 确保有会话ID
        if not self.session_id:
            self.get_session_id()
        
        # 构建登录请求
        login_request = LoginRequest(
            account=username,
            password=password
        )
        
        # 发起登录请求
        response = self.get(
            endpoint='user-login-{sessionid}.json',
            response_model=LoginResponse,
            params=login_request.model_dump(),
            sessionid=self.session_id
        )
        
        # 从LoginResponse中提取用户信息并转换为UserModel
        user_data = response.user
        from ..models.user import UserModel
        
        # 将用户字典转换为UserModel
        user_model = UserModel.model_validate(user_data)
        
        # 返回包装的UserDetailResponse
        from ..models.user import UserDetailResponse
        return UserDetailResponse(
            status="success",
            user=user_model
        )
    
    def logout(self) -> bool:
        """用户登出
        
        Returns:
            登出是否成功
            
        Raises:
            ZenTaoError: 登出失败
        """
        if not self.session_id:
            return True  # 没有会话ID，认为已经登出
        
        try:
            # 发起登出请求
            response = self.get(
                endpoint='user-logout-{sessionid}.json',
                response_model=LogoutResponse,
                sessionid=self.session_id
            )
            
            # 清除会话ID
            self.session_id = None
            # 根据响应状态判断是否成功
            return response.status == "success"
            
        except Exception:
            # 登出失败，但仍然清除本地会话ID
            self.session_id = None
            return False
    
    def is_logged_in(self) -> bool:
        """检查是否已登录
        
        Returns:
            是否已登录
        """
        return self.session_id is not None
    
    def ensure_session(self) -> str:
        """确保有有效的会话ID
        
        Returns:
            会话ID字符串
            
        Raises:
            ZenTaoError: 无法获取会话ID
        """
        if not self.session_id:
            return self.get_session_id()
        return self.session_id
