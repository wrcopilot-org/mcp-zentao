"""
禅道用户管理客户端

提供用户信息查询等功能。
"""

from typing import List, Optional
from .base_client import BaseClient
from ..models.user import UserDetailResponse, UserListResponse, UserModel


class UserClient(BaseClient):
    """禅道用户管理客户端
    
    负责处理用户信息查询、用户列表获取等用户相关操作。
    """
    
    def get_current_user(self) -> UserModel:
        """获取当前登录用户的详细信息
        
        Returns:
            当前用户的详细信息
            
        Raises:
            ZenTaoError: 获取用户信息失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取用户信息")
        
        response = self.get(
            endpoint='user-login-{sessionid}.json',
            response_model=UserDetailResponse,
            sessionid=self.session_id
        )
        
        return response.get_user_data()
    
    def get_user_by_id(self, user_id: str) -> UserModel:
        """根据用户ID获取用户详细信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户详细信息
            
        Raises:
            ZenTaoError: 获取用户信息失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取用户信息")
        
        # 注意：这个API端点需要根据实际禅道API确认
        response = self.get(
            endpoint='user-view-{user_id}-{sessionid}.json',
            response_model=UserDetailResponse,
            user_id=user_id,
            sessionid=self.session_id
        )
        
        return response.get_user_data()
    
    def get_users(self, dept_id: Optional[str] = None) -> List[UserModel]:
        """获取用户列表
        
        Args:
            dept_id: 部门ID，可选。如果指定则只获取该部门的用户
            
        Returns:
            用户列表
            
        Raises:
            ZenTaoError: 获取用户列表失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取用户列表")
        
        params = {}
        if dept_id:
            params['dept'] = dept_id
        
        # 注意：这个API端点需要根据实际禅道API确认
        response = self.get(
            endpoint='user-browse-{sessionid}.json',
            response_model=UserListResponse,
            params=params if params else None,
            sessionid=self.session_id
        )
        
        return response.get_user_list()
    
    def search_users(self, keyword: str) -> List[UserModel]:
        """搜索用户
        
        Args:
            keyword: 搜索关键词（用户名、真实姓名等）
            
        Returns:
            匹配的用户列表
            
        Raises:
            ZenTaoError: 搜索用户失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能搜索用户")
        
        response = self.get(
            endpoint='user-browse-{sessionid}.json',
            response_model=UserListResponse,
            params={'search': keyword},
            sessionid=self.session_id
        )
        
        return response.get_user_list()
    
    def is_user_active(self, user_id: str) -> bool:
        """检查用户是否激活状态
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户是否激活
            
        Raises:
            ZenTaoError: 获取用户状态失败
        """
        try:
            user = self.get_user_by_id(user_id)
            return user.deleted == "0"  # deleted字段为"0"表示未删除（激活）
        except Exception:
            return False
