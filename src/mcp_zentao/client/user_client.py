"""
禅道用户管理客户端

提供用户信息查询等功能。
"""

from typing import List, Optional, Dict, Any
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
    
    def get_users(self, dept_id: Optional[int] = 0) -> List[Dict[str, Any]]:
        """获取用户列表
        
        Args:
            dept_id: 部门ID。如果为0，则获取所有用户。
            
        Returns:
            用户列表数组
            
        Raises:
            ZenTaoError: 获取用户列表失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取用户列表")
        
        response = self.get(
            endpoint='company-browse-{dept_id}.json',
            response_model=UserListResponse,
            dept_id=str(dept_id)  # API需要字符串格式的dept_id
        )
        
        return response.get_users()
