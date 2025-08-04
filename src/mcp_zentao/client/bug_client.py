"""
禅道缺陷管理客户端

提供缺陷查询、创建、编辑、解决等功能。
"""

from typing import List, Optional
from .base_client import BaseClient
from ..models.bug import (
    BugListResponse, BugModel, BugCreateRequest, BugEditRequest,
    BugResolveRequest, BugAssignRequest, BugConfirmRequest, BugDetailResponse
)
from ..models.common import CommonOperationResponse


class BugClient(BaseClient):
    """禅道缺陷管理客户端
    
    负责处理缺陷相关的所有操作：查询、创建、编辑、解决、关闭等。
    """
    
    def get_my_bugs(
        self, 
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort_key: str = "id_desc"
    ) -> List[BugModel]:
        """获取我的缺陷列表
        
        Args:
            status: 缺陷状态过滤 ('active', 'resolved', 'closed')
            page: 页码，从1开始
            per_page: 每页记录数，默认20
            sort_key: 排序键，默认id_desc
            
        Returns:
            缺陷列表
            
        Raises:
            ZenTaoError: 获取缺陷列表失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取缺陷列表")
        
        params = {}
        if status:
            params['status'] = status
        
        response = self.get_paginated(
            base_endpoint='my-bug',
            response_model=BugListResponse,
            page=page,
            per_page=per_page,
            sort_key=sort_key,
            params=params if params else None
        )
        
        return response.get_bug_list()
    
    def get_my_bugs_all_pages(
        self, 
        status: Optional[str] = None,
        per_page: int = 20,
        sort_key: str = "id_desc",
        max_pages: Optional[int] = None
    ) -> List[BugModel]:
        """获取我的缺陷列表（所有页面）
        
        Args:
            status: 缺陷状态过滤
            per_page: 每页记录数
            sort_key: 排序键
            max_pages: 最大页数限制
            
        Returns:
            所有缺陷列表
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取缺陷列表")
        
        params = {}
        if status:
            params['status'] = status
        
        all_responses = self.get_all_pages(
            base_endpoint='my-bug',
            response_model=BugListResponse,
            per_page=per_page,
            sort_key=sort_key,
            params=params if params else None,
            max_pages=max_pages
        )
        
        # 合并所有页面的缺陷
        all_bugs = []
        for response in all_responses:
            all_bugs.extend(response.get_bug_list())
        
        return all_bugs
    
    def get_project_bugs(
        self, 
        project_id: str,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> List[BugModel]:
        """获取项目下的缺陷列表
        
        Args:
            project_id: 项目ID
            status: 缺陷状态过滤
            assigned_to: 指派给某人的缺陷
            
        Returns:
            缺陷列表
            
        Raises:
            ZenTaoError: 获取缺陷列表失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取缺陷列表")
        
        params = {}
        if status:
            params['status'] = status
        if assigned_to:
            params['assignedTo'] = assigned_to
        
        response = self.get(
            endpoint='project-bug-{project_id}-{sessionid}.json',
            response_model=BugListResponse,
            params=params if params else None,
            project_id=project_id,
            sessionid=self.session_id
        )
        
        return response.get_bug_list()
    
    def get_bug_by_id(self, bug_id: str) -> BugModel:
        """根据缺陷ID获取缺陷详细信息
        
        Args:
            bug_id: 缺陷ID
            
        Returns:
            缺陷详细信息
            
        Raises:
            ZenTaoError: 获取缺陷信息失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取缺陷信息")
        
        response = self.get(
            endpoint='bug-view-{bug_id}-{sessionid}.json',
            response_model=BugDetailResponse,
            bug_id=bug_id,
            sessionid=self.session_id
        )
        
        return response.get_bug_data()
    
    def create_bug(self, bug_data: BugCreateRequest) -> BugModel:
        """创建新缺陷
        
        Args:
            bug_data: 缺陷创建请求数据
            
        Returns:
            创建的缺陷信息
            
        Raises:
            ZenTaoError: 创建缺陷失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能创建缺陷")
        
        response = self.post(
            endpoint='bug-create-{product_id}-{branch}-moduleID={module_id}-{sessionid}.json',
            response_model=CommonOperationResponse,
            data=bug_data.model_dump(exclude_none=True),
            product_id=bug_data.product,
            branch=bug_data.branch or '0',
            module_id=bug_data.module or '0',
            sessionid=self.session_id
        )
        
        # 如果创建成功，获取新创建的缺陷信息
        if hasattr(response, 'data') and response.data:
            bug_id = str(response.data.get('id', ''))
            if bug_id:
                return self.get_bug_by_id(bug_id)
        
        # 如果无法获取新缺陷ID，返回基础缺陷信息
        return BugModel(
            id=response.data.get('id', '0') if response.data else '0',
            title=bug_data.title,
            product=bug_data.product,
            severity=bug_data.severity,
            priority=bug_data.priority,
            status='active',  # 新缺陷默认状态
            **{k: v for k, v in bug_data.model_dump().items() 
               if k in BugModel.model_fields and v is not None}
        )
    
    def edit_bug(self, bug_id: str, bug_data: BugEditRequest) -> BugModel:
        """编辑缺陷信息
        
        Args:
            bug_id: 缺陷ID
            bug_data: 缺陷编辑请求数据
            
        Returns:
            更新后的缺陷信息
            
        Raises:
            ZenTaoError: 编辑缺陷失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能编辑缺陷")
        
        response = self.post(
            endpoint='bug-edit-{bug_id}-{sessionid}.json',
            response_model=CommonOperationResponse,
            data=bug_data.model_dump(exclude_none=True),
            bug_id=bug_id,
            sessionid=self.session_id
        )
        
        # 返回更新后的缺陷信息
        return self.get_bug_by_id(bug_id)
    
    def assign_bug(self, bug_id: str, assign_data: BugAssignRequest) -> BugModel:
        """分配缺陷
        
        Args:
            bug_id: 缺陷ID
            assign_data: 缺陷分配请求数据
            
        Returns:
            更新后的缺陷信息
            
        Raises:
            ZenTaoError: 分配缺陷失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能分配缺陷")
        
        response = self.post(
            endpoint='bug-assignTo-{bug_id}-{sessionid}.json',
            response_model=CommonOperationResponse,
            data=assign_data.model_dump(exclude_none=True),
            bug_id=bug_id,
            sessionid=self.session_id
        )
        
        # 返回更新后的缺陷信息
        return self.get_bug_by_id(bug_id)
    
    def resolve_bug(self, bug_id: str, resolve_data: BugResolveRequest) -> bool:
        """解决缺陷
        
        Args:
            bug_id: 缺陷ID
            resolve_data: 缺陷解决请求数据
            
        Returns:
            是否解决成功
            
        Raises:
            ZenTaoError: 解决缺陷失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能解决缺陷")
        
        try:
            self.post(
                endpoint='bug-resolve-{bug_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                data=resolve_data.model_dump(exclude_none=True),
                bug_id=bug_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def confirm_bug(self, bug_id: str, confirm_data: BugConfirmRequest) -> bool:
        """确认缺陷
        
        Args:
            bug_id: 缺陷ID
            confirm_data: 缺陷确认请求数据
            
        Returns:
            是否确认成功
            
        Raises:
            ZenTaoError: 确认缺陷失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能确认缺陷")
        
        try:
            self.post(
                endpoint='bug-confirmBug-{bug_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                data=confirm_data.model_dump(exclude_none=True),
                bug_id=bug_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def close_bug(self, bug_id: str, comment: Optional[str] = None) -> bool:
        """关闭缺陷
        
        Args:
            bug_id: 缺陷ID
            comment: 关闭备注
            
        Returns:
            是否关闭成功
            
        Raises:
            ZenTaoError: 关闭缺陷失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能关闭缺陷")
        
        data = {}
        if comment:
            data['comment'] = comment
        
        try:
            self.post(
                endpoint='bug-close-{bug_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                data=data if data else None,
                bug_id=bug_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def activate_bug(self, bug_id: str, comment: Optional[str] = None) -> bool:
        """激活缺陷
        
        Args:
            bug_id: 缺陷ID
            comment: 激活备注
            
        Returns:
            是否激活成功
            
        Raises:
            ZenTaoError: 激活缺陷失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能激活缺陷")
        
        data = {}
        if comment:
            data['comment'] = comment
        
        try:
            self.post(
                endpoint='bug-activate-{bug_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                data=data if data else None,
                bug_id=bug_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def search_bugs(
        self, 
        keyword: str,
        product_id: Optional[str] = None
    ) -> List[BugModel]:
        """搜索缺陷
        
        Args:
            keyword: 搜索关键词（缺陷标题、描述等）
            product_id: 限定在某个产品内搜索
            
        Returns:
            匹配的缺陷列表
            
        Raises:
            ZenTaoError: 搜索缺陷失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能搜索缺陷")
        
        params = {'search': keyword}
        
        if product_id:
            endpoint = 'product-bug-{product_id}-{sessionid}.json'
            response = self.get(
                endpoint=endpoint,
                response_model=BugListResponse,
                params=params,
                product_id=product_id,
                sessionid=self.session_id
            )
        else:
            # 全局搜索缺陷
            response = self.get(
                endpoint='bug-browse-{sessionid}.json',
                response_model=BugListResponse,
                params=params,
                sessionid=self.session_id
            )
        
        return response.get_bug_list()
