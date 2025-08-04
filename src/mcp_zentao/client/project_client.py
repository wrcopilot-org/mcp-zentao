"""
禅道项目管理客户端

提供项目查询、创建、编辑等功能。
"""

from typing import List, Optional, Dict, Any
from .base_client import BaseClient
from ..models.project import (
    ProjectListResponse, ProjectModel, ProjectCreateRequest, 
    ProjectEditRequest, ProjectDetailResponse, ProjectTaskResponse
)
from ..models.common import CommonOperationResponse


class ProjectClient(BaseClient):
    """禅道项目管理客户端
    
    负责处理项目相关的所有操作：查询、创建、编辑、删除等。
    """
    
    def get_my_projects(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_key: str = "id_desc"
    ) -> List[ProjectModel]:
        """获取我参与的项目列表
        
        Args:
            page: 页码，从1开始
            per_page: 每页记录数，默认20
            sort_key: 排序键，默认id_desc
        
        Returns:
            项目列表
            
        Raises:
            ZenTaoError: 获取项目列表失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取项目列表")
        
        response = self.get_paginated(
            base_endpoint='my-project',
            response_model=ProjectListResponse,
            page=page,
            per_page=per_page,
            sort_key=sort_key
        )
        
        return response.get_project_list()
    
    def get_my_projects_all_pages(
        self,
        per_page: int = 20,
        sort_key: str = "id_desc",
        max_pages: Optional[int] = None
    ) -> List[ProjectModel]:
        """获取我参与的项目列表（所有页面）
        
        Args:
            per_page: 每页记录数
            sort_key: 排序键
            max_pages: 最大页数限制
            
        Returns:
            所有项目列表
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取项目列表")
        
        all_responses = self.get_all_pages(
            base_endpoint='my-project',
            response_model=ProjectListResponse,
            per_page=per_page,
            sort_key=sort_key,
            max_pages=max_pages
        )
        
        # 合并所有页面的项目
        all_projects = []
        for response in all_responses:
            all_projects.extend(response.get_project_list())
        
        return all_projects
    
    def get_project_by_id(self, project_id: str) -> ProjectModel:
        """根据项目ID获取项目详细信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目详细信息
            
        Raises:
            ZenTaoError: 获取项目信息失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取项目信息")
        
        response = self.get(
            endpoint='project-task-{project_id}.json',
            response_model=ProjectTaskResponse,
            project_id=project_id
        )
        
        return response.get_project_info()
    
    def create_project(self, project_data: ProjectCreateRequest) -> ProjectModel:
        """创建新项目
        
        Args:
            project_data: 项目创建请求数据
            
        Returns:
            创建的项目信息
            
        Raises:
            NotImplementedError: 该功能暂未验证，不建议使用
        """
        raise NotImplementedError("创建项目功能暂未验证，不建议使用")
        
        # 以下代码保留作为参考，但暂时不可用
        if not self.session_id:
            raise ValueError("需要先登录才能创建项目")
        
        response = self.post(
            endpoint='project-create-{sessionid}.json',
            response_model=CommonOperationResponse,
            data=project_data.model_dump(exclude_none=True),
            sessionid=self.session_id
        )
        
        # 如果创建成功，获取新创建的项目信息
        if hasattr(response, 'data') and response.data:
            project_id = str(response.data.get('id', ''))
            if project_id:
                return self.get_project_by_id(project_id)
        
        # 如果无法获取新项目ID，返回基础项目信息
        return ProjectModel(
            id=response.data.get('id', '0') if response.data else '0',
            name=project_data.name,
            code=project_data.code or '',
            type=project_data.type,
            status='wait',  # 新项目默认状态
            **{k: v for k, v in project_data.model_dump().items() 
               if k in ProjectModel.model_fields and v is not None}
        )
    
    def close_project(self, project_id: str, comment: Optional[str] = None) -> bool:
        """关闭项目
        
        Args:
            project_id: 项目ID
            comment: 关闭备注
            
        Returns:
            是否关闭成功
            
        Raises:
            NotImplementedError: 该功能暂未验证，不建议使用
        """
        raise NotImplementedError("关闭项目功能暂未验证，不建议使用")
        
        # 以下代码保留作为参考，但暂时不可用
        if not self.session_id:
            raise ValueError("需要先登录才能关闭项目")
        
        data = {}
        if comment:
            data['comment'] = comment
        
        try:
            self.post(
                endpoint='project-close-{project_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                data=data if data else None,
                project_id=project_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def start_project(self, project_id: str) -> bool:
        """启动项目
        
        Args:
            project_id: 项目ID
            
        Returns:
            是否启动成功
            
        Raises:
            NotImplementedError: 该功能暂未验证，不建议使用
        """
        raise NotImplementedError("启动项目功能暂未验证，不建议使用")
        
        # 以下代码保留作为参考，但暂时不可用
        if not self.session_id:
            raise ValueError("需要先登录才能启动项目")
        
        try:
            self.post(
                endpoint='project-start-{project_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                project_id=project_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def get_project_tasks(self, project_id: str) -> ProjectTaskResponse:
        """获取项目任务详情
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目任务响应对象，包含项目信息、任务列表、团队成员等
            
        Raises:
            ZenTaoError: 获取项目任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取项目任务")
        
        response = self.get(
            endpoint='project-task-{project_id}.json',
            response_model=ProjectTaskResponse,
            project_id=project_id
        )
        
        return response
