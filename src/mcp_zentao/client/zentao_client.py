"""
禅道API主客户端

整合所有模块的功能，提供统一的禅道API访问接口。
统一管理HTTP会话和Cookie，确保登录状态在所有子客户端间共享。
"""

import httpx
from typing import Optional
from .base_client import BaseClient
from .session_client import SessionClient
from .user_client import UserClient
from .project_client import ProjectClient
from .task_client import TaskClient
from .bug_client import BugClient
from ..models.user import UserModel


class ZenTaoClient:
    """禅道API主客户端
    
    整合了会话管理、用户管理、项目管理、任务管理、缺陷管理等所有功能。
    提供统一的API访问接口和会话管理，所有子客户端共享同一个HTTP会话，
    确保登录后的 zentaosid Cookie 在所有API调用中保持一致。
    
    使用示例:
        # 创建客户端
        client = ZenTaoClient("http://zentao.example.com")
        
        # 登录
        user = client.login("username", "password")
        
        # 获取我的项目（自动使用登录后的Cookie）
        projects = client.projects.get_my_projects()
        
        # 获取我的任务
        tasks = client.tasks.get_my_tasks()
        
        # 获取我的缺陷
        bugs = client.bugs.get_my_bugs()
        
        # 关闭客户端
        client.close()
        
    或使用上下文管理器:
        with ZenTaoClient("http://zentao.example.com") as client:
            user = client.login("username", "password")
            projects = client.get_my_projects()
    """
    
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        """初始化禅道客户端
        
        Args:
            base_url: 禅道系统的基础URL，例如 http://zentao.example.com
            timeout: 请求超时时间，默认30秒
        """
        self.base_url = base_url
        self.timeout = timeout
        
        # 创建共享的HTTP客户端，用于管理Cookie
        self._http_client = httpx.Client(
            timeout=timeout,
            follow_redirects=True
        )
        
        # 创建各个功能模块的客户端，使用共享的HTTP客户端
        self._session_client = SessionClient(base_url, timeout)
        self._user_client = UserClient(base_url, timeout)
        self._project_client = ProjectClient(base_url, timeout)
        self._task_client = TaskClient(base_url, timeout)
        self._bug_client = BugClient(base_url, timeout)
        
        # 让所有客户端共享HTTP会话
        self._sync_http_clients()
        
        self._current_user: Optional[UserModel] = None
    
    def _sync_http_clients(self) -> None:
        """同步所有客户端的HTTP会话，确保Cookie一致性"""
        # 所有客户端使用同一个HTTP客户端实例，确保Cookie共享
        self._session_client._client = self._http_client
        self._user_client._client = self._http_client
        self._project_client._client = self._http_client
        self._task_client._client = self._http_client
        self._bug_client._client = self._http_client
    
    def __enter__(self) -> 'ZenTaoClient':
        """上下文管理器进入"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出"""
        self.close()
    
    def close(self) -> None:
        """关闭HTTP客户端连接"""
        try:
            self._http_client.close()
        except Exception:
            pass  # 忽略关闭时的错误
    @property
    def session_id(self) -> Optional[str]:
        """获取当前会话ID
        
        注意：使用Cookie管理时，session_id主要用于URL构建，
        实际认证依赖HTTP客户端中的zentaosid Cookie
        """
        return self._session_client.session_id
    
    @property
    def current_user(self) -> Optional[UserModel]:
        """获取当前登录用户信息"""
        return self._current_user
    
    @property
    def is_logged_in(self) -> bool:
        """检查是否已登录
        
        检查HTTP客户端是否有有效的zentaosid Cookie
        """
        # 检查是否有zentaosid Cookie
        for cookie in self._http_client.cookies.jar:
            if cookie.name == 'zentaosid' and cookie.value:
                return True
        return False
    
    @property 
    def zentao_cookie(self) -> Optional[str]:
        """获取当前的zentaosid Cookie值"""
        for cookie in self._http_client.cookies.jar:
            if cookie.name == 'zentaosid':
                return cookie.value
        return None
    
    # 会话管理方法
    def get_session_id(self) -> str:
        """获取会话ID
        
        Returns:
            会话ID字符串
            
        Note:
            获取session_id后会自动设置到所有子客户端，
            但实际认证主要依赖共享的HTTP客户端中的Cookie
        """
        session_id = self._session_client.get_session_id()
        self._sync_session_id_to_clients()
        return session_id
    
    def _sync_session_id_to_clients(self) -> None:
        """同步会话ID到所有子客户端（用于URL构建）"""
        session_id = self._session_client.session_id
        
        self._user_client.session_id = session_id
        self._project_client.session_id = session_id
        self._task_client.session_id = session_id
        self._bug_client.session_id = session_id
    
    def login(self, username: str, password: str) -> UserModel:
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            当前登录用户的详细信息
            
        Raises:
            ZenTaoError: 登录失败
            
        Note:
            登录成功后，zentaosid Cookie会自动保存在共享的HTTP客户端中，
            后续所有API调用都会自动携带此Cookie进行认证
        """
        user_response = self._session_client.login(username, password)
        self._sync_session_id_to_clients()
        
        # 提取用户信息
        self._current_user = user_response.user
        
        return self._current_user
    
    def logout(self) -> bool:
        """用户登出
        
        Returns:
            登出是否成功
            
        Note:
            登出后会清除共享HTTP客户端中的所有Cookie
        """
        result = self._session_client.logout()
        self._sync_session_id_to_clients()
        self._current_user = None
        
        # 清除所有Cookie
        self._http_client.cookies.clear()
        
        return result
    
    # 各模块客户端的访问属性
    @property
    def sessions(self) -> SessionClient:
        """会话管理客户端"""
        return self._session_client
    
    @property
    def users(self) -> UserClient:
        """用户管理客户端"""
        return self._user_client
    
    @property
    def projects(self) -> ProjectClient:
        """项目管理客户端"""
        return self._project_client
    
    @property
    def tasks(self) -> TaskClient:
        """任务管理客户端"""
        return self._task_client
    
    @property
    def bugs(self) -> BugClient:
        """缺陷管理客户端"""
        return self._bug_client
    
    # 便捷方法，提供常用操作的快速访问
    def get_my_projects(self):
        """获取我的项目列表（便捷方法）"""
        return self.projects.get_my_projects()
    
    def get_my_tasks(self, status=None):
        """获取我的任务列表（便捷方法）"""
        return self.tasks.get_my_tasks(status)
    
    def get_my_bugs(self, status=None):
        """获取我的缺陷列表（便捷方法）"""
        return self.bugs.get_my_bugs(status)
    
    def get_project_by_id(self, project_id: str):
        """根据ID获取项目信息（便捷方法）"""
        return self.projects.get_project_by_id(project_id)
    
    def get_task_by_id(self, task_id: str):
        """根据ID获取任务信息（便捷方法）"""
        return self.tasks.get_task_by_id(task_id)
    
    def get_bug_by_id(self, bug_id: str):
        """根据ID获取缺陷信息（便捷方法）"""
        return self.bugs.get_bug_by_id(bug_id)
    
    def ensure_logged_in(self) -> None:
        """确保已登录，如果未登录则抛出异常
        
        Raises:
            ValueError: 如果未登录
        """
        if not self.is_logged_in:
            raise ValueError("需要先登录才能执行此操作")
    
    def refresh_current_user(self) -> UserModel:
        """刷新当前用户信息
        
        Returns:
            更新后的用户信息
            
        Raises:
            ZenTaoError: 刷新失败
        """
        self.ensure_logged_in()
        self._current_user = self.users.get_current_user()
        return self._current_user
