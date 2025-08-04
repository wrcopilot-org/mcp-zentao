"""
禅道任务管理客户端

提供任务查询、创建、编辑、状态变更等功能。
"""

from typing import List, Optional, Dict, Any
from .base_client import BaseClient
from ..models.task import (
    TaskListResponse, TaskModel, TaskCreateRequest, TaskEditRequest,
    TaskFinishRequest, TaskAssignRequest, TaskDetailResponse
)
from ..models.common import CommonOperationResponse


class TaskClient(BaseClient):
    """禅道任务管理客户端
    
    负责处理任务相关的所有操作：查询、创建、编辑、分配、完成等。
    """
    
    def get_my_tasks(
        self, 
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort_key: str = "id_desc"
    ) -> List[TaskModel]:
        """获取我的任务列表
        
        Args:
            status: 任务状态过滤 ('wait', 'doing', 'done', 'pause', 'cancel', 'closed')
            page: 页码，从1开始
            per_page: 每页记录数，默认20
            sort_key: 排序键，默认id_desc
            
        Returns:
            任务列表
            
        Raises:
            ZenTaoError: 获取任务列表失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取任务列表")
        
        params = {}
        if status:
            params['status'] = status
        
        response = self.get_paginated(
            base_endpoint='my-task',
            response_model=TaskListResponse,
            page=page,
            per_page=per_page,
            sort_key=sort_key,
            params=params if params else None
        )
        
        return response.get_task_list()
    
    def get_my_tasks_all_pages(
        self, 
        status: Optional[str] = None,
        per_page: int = 20,
        sort_key: str = "id_desc",
        max_pages: Optional[int] = None
    ) -> List[TaskModel]:
        """获取我的任务列表（所有页面）
        
        Args:
            status: 任务状态过滤
            per_page: 每页记录数
            sort_key: 排序键
            max_pages: 最大页数限制
            
        Returns:
            所有任务列表
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取任务列表")
        
        params = {}
        if status:
            params['status'] = status
        
        all_responses = self.get_all_pages(
            base_endpoint='my-task',
            response_model=TaskListResponse,
            per_page=per_page,
            sort_key=sort_key,
            params=params if params else None,
            max_pages=max_pages
        )
        
        # 合并所有页面的任务
        all_tasks = []
        for response in all_responses:
            all_tasks.extend(response.get_task_list())
        
        return all_tasks
    
    def get_project_tasks(
        self, 
        project_id: str,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None
    ) -> List[TaskModel]:
        """获取项目下的任务列表
        
        Args:
            project_id: 项目ID
            status: 任务状态过滤
            assigned_to: 指派给某人的任务
            
        Returns:
            任务列表
            
        Raises:
            ZenTaoError: 获取任务列表失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取任务列表")
        
        params = {}
        if status:
            params['status'] = status
        if assigned_to:
            params['assignedTo'] = assigned_to
        
        response = self.get(
            endpoint='project-task-{project_id}-{sessionid}.json',
            response_model=TaskListResponse,
            params=params if params else None,
            project_id=project_id,
            sessionid=self.session_id
        )
        
        return response.get_task_list()
    
    def get_task_by_id(self, task_id: str) -> Dict[str, Any]:
        """根据任务ID获取任务详细信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务详细信息
            
        Raises:
            ZenTaoError: 获取任务信息失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取任务信息")
        
        response = self.get(
            endpoint='task-view-{task_id}-{sessionid}.json',
            response_model=TaskDetailResponse,
            task_id=task_id,
            sessionid=self.session_id
        )
        
        return response.get_task()
    
    def get_task_detail(self, task_id: str) -> TaskDetailResponse:
        """获取任务完整详情响应（包含项目信息、用户映射等附加信息）
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务详情响应对象，包含附加信息
            
        Raises:
            ZenTaoError: 获取任务详情失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能获取任务详情")
        
        response = self.get(
            endpoint='task-view-{task_id}-{sessionid}.json',
            response_model=TaskDetailResponse,
            task_id=task_id,
            sessionid=self.session_id
        )
        
        return response
    
    def create_task(self, task_data: TaskCreateRequest) -> TaskModel:
        """创建新任务
        
        Args:
            task_data: 任务创建请求数据
            
        Returns:
            创建的任务信息
            
        Raises:
            ZenTaoError: 创建任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能创建任务")
        
        response = self.post(
            endpoint='task-create-{project_id}--{module_id}-{sessionid}.json',
            response_model=CommonOperationResponse,
            data=task_data.model_dump(exclude_none=True),
            project_id=task_data.project,
            module_id=task_data.module or '0',
            sessionid=self.session_id
        )
        
        # 如果创建成功，获取新创建的任务信息
        if hasattr(response, 'data') and response.data:
            task_id = str(response.data.get('id', ''))
            if task_id:
                return self.get_task_by_id(task_id)
        
        # 如果无法获取新任务ID，返回基础任务信息
        return TaskModel(
            id=response.data.get('id', '0') if response.data else '0',
            name=task_data.name,
            project=task_data.project,
            type=task_data.type,
            status='wait',  # 新任务默认状态
            **{k: v for k, v in task_data.model_dump().items() 
               if k in TaskModel.model_fields and v is not None}
        )
    
    def edit_task(self, task_id: str, task_data: TaskEditRequest) -> TaskModel:
        """编辑任务信息
        
        Args:
            task_id: 任务ID
            task_data: 任务编辑请求数据
            
        Returns:
            更新后的任务信息
            
        Raises:
            ZenTaoError: 编辑任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能编辑任务")
        
        response = self.post(
            endpoint='task-edit-{task_id}-{sessionid}.json',
            response_model=CommonOperationResponse,
            data=task_data.model_dump(exclude_none=True),
            task_id=task_id,
            sessionid=self.session_id
        )
        
        # 返回更新后的任务信息
        return self.get_task_by_id(task_id)
    
    def assign_task(self, task_id: str, assign_data: TaskAssignRequest) -> TaskModel:
        """分配任务
        
        Args:
            task_id: 任务ID
            assign_data: 任务分配请求数据
            
        Returns:
            更新后的任务信息
            
        Raises:
            ZenTaoError: 分配任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能分配任务")
        
        response = self.post(
            endpoint='task-assignTo-{task_id}-{sessionid}.json',
            response_model=CommonOperationResponse,
            data=assign_data.model_dump(exclude_none=True),
            task_id=task_id,
            sessionid=self.session_id
        )
        
        # 返回更新后的任务信息
        return self.get_task_by_id(task_id)
    
    def start_task(self, task_id: str) -> bool:
        """开始任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否开始成功
            
        Raises:
            ZenTaoError: 开始任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能开始任务")
        
        try:
            self.post(
                endpoint='task-start-{task_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                task_id=task_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def finish_task(self, task_id: str, finish_data: TaskFinishRequest) -> bool:
        """完成任务
        
        Args:
            task_id: 任务ID
            finish_data: 任务完成请求数据
            
        Returns:
            是否完成成功
            
        Raises:
            ZenTaoError: 完成任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能完成任务")
        
        try:
            self.post(
                endpoint='task-finish-{task_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                data=finish_data.model_dump(exclude_none=True),
                task_id=task_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def close_task(self, task_id: str, comment: Optional[str] = None) -> bool:
        """关闭任务
        
        Args:
            task_id: 任务ID
            comment: 关闭备注
            
        Returns:
            是否关闭成功
            
        Raises:
            ZenTaoError: 关闭任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能关闭任务")
        
        data = {}
        if comment:
            data['comment'] = comment
        
        try:
            self.post(
                endpoint='task-close-{task_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                data=data if data else None,
                task_id=task_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def cancel_task(self, task_id: str, comment: Optional[str] = None) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            comment: 取消备注
            
        Returns:
            是否取消成功
            
        Raises:
            ZenTaoError: 取消任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能取消任务")
        
        data = {}
        if comment:
            data['comment'] = comment
        
        try:
            self.post(
                endpoint='task-cancel-{task_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                data=data if data else None,
                task_id=task_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def pause_task(self, task_id: str, comment: Optional[str] = None) -> bool:
        """暂停任务
        
        Args:
            task_id: 任务ID
            comment: 暂停备注
            
        Returns:
            是否暂停成功
            
        Raises:
            ZenTaoError: 暂停任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能暂停任务")
        
        data = {}
        if comment:
            data['comment'] = comment
        
        try:
            self.post(
                endpoint='task-pause-{task_id}-{sessionid}.json',
                response_model=CommonOperationResponse,
                data=data if data else None,
                task_id=task_id,
                sessionid=self.session_id
            )
            return True
        except Exception:
            return False
    
    def search_tasks(
        self, 
        keyword: str,
        project_id: Optional[str] = None
    ) -> List[TaskModel]:
        """搜索任务
        
        Args:
            keyword: 搜索关键词（任务名称、描述等）
            project_id: 限定在某个项目内搜索
            
        Returns:
            匹配的任务列表
            
        Raises:
            ZenTaoError: 搜索任务失败
        """
        if not self.session_id:
            raise ValueError("需要先登录才能搜索任务")
        
        params = {'search': keyword}
        
        if project_id:
            endpoint = 'project-task-{project_id}-{sessionid}.json'
            response = self.get(
                endpoint=endpoint,
                response_model=TaskListResponse,
                params=params,
                project_id=project_id,
                sessionid=self.session_id
            )
        else:
            # 全局搜索任务
            response = self.get(
                endpoint='task-browse-{sessionid}.json',
                response_model=TaskListResponse,
                params=params,
                sessionid=self.session_id
            )
        
        return response.get_task_list()
