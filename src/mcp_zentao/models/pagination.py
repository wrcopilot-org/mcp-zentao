"""
分页相关数据模型

定义禅道API分页的请求参数和响应数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class SortOrder(str, Enum):
    """排序方向枚举"""
    ASC = "asc"      # 升序
    DESC = "desc"    # 降序


class SortField(str, Enum):
    """排序字段枚举"""
    ID = "id"                    # 按ID排序
    NAME = "name"               # 按名称排序  
    STATUS = "status"           # 按状态排序
    PRIORITY = "priority"       # 按优先级排序
    ASSIGNED_TO = "assignedTo"  # 按指派人排序
    OPENED_BY = "openedBy"      # 按创建人排序
    OPENED_DATE = "openedDate"  # 按创建时间排序
    DEADLINE = "deadline"       # 按截止时间排序


class PageParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, description="页码，从1开始")
    per_page: int = Field(default=20, description="每页记录数，默认20")
    sort_field: SortField = Field(default=SortField.ID, description="排序字段")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="排序方向")
    
    def get_sort_key(self) -> str:
        """获取排序键，格式：字段名_方向"""
        return f"{self.sort_field.value}_{self.sort_order.value}"


class PagerInfo(BaseModel):
    """分页器信息"""
    rec_total: int = Field(description="总记录数")
    rec_per_page: int = Field(description="每页记录数")
    page_id: int = Field(description="当前页码")
    page_total: int = Field(description="总页数")
    
    # 可选的其他分页信息
    first_page: Optional[int] = Field(default=None, description="首页页码")
    last_page: Optional[int] = Field(default=None, description="末页页码")  
    prev_page: Optional[int] = Field(default=None, description="上一页页码")
    next_page: Optional[int] = Field(default=None, description="下一页页码")


class PaginatedListParams(BaseModel):
    """分页列表请求参数"""
    # 分页参数
    page_params: PageParams = Field(default_factory=PageParams, description="分页参数")
    
    # 过滤参数
    status: Optional[str] = Field(default=None, description="状态过滤")
    assigned_to: Optional[str] = Field(default=None, description="指派人过滤")
    created_by: Optional[str] = Field(default=None, description="创建人过滤")
    project_id: Optional[str] = Field(default=None, description="项目ID过滤")
    product_id: Optional[str] = Field(default=None, description="产品ID过滤")
    
    # 搜索参数
    keyword: Optional[str] = Field(default=None, description="搜索关键词")
    
    def to_url_params(self) -> Dict[str, Any]:
        """转换为URL参数字典"""
        params = {}
        
        # 添加非空的过滤参数
        if self.status:
            params['status'] = self.status
        if self.assigned_to:
            params['assignedTo'] = self.assigned_to
        if self.created_by:
            params['openedBy'] = self.created_by
        if self.project_id:
            params['project'] = self.project_id
        if self.product_id:
            params['product'] = self.product_id
        if self.keyword:
            params['search'] = self.keyword
            
        return params


class PaginatedResponse(BaseModel):
    """分页响应基类"""
    pager: Optional[PagerInfo] = Field(default=None, description="分页信息")
    
    def has_next_page(self) -> bool:
        """是否有下一页"""
        if not self.pager:
            return False
        return self.pager.page_id < self.pager.page_total
    
    def has_prev_page(self) -> bool:
        """是否有上一页"""
        if not self.pager:
            return False
        return self.pager.page_id > 1
    
    def get_next_page(self) -> Optional[int]:
        """获取下一页页码"""
        if self.has_next_page():
            return self.pager.page_id + 1
        return None
    
    def get_prev_page(self) -> Optional[int]:
        """获取上一页页码"""  
        if self.has_prev_page():
            return self.pager.page_id - 1
        return None


class PaginationHelper:
    """分页助手类
    
    负责构建禅道API的分页URL和处理分页逻辑
    """
    
    @staticmethod
    def build_paginated_url(
        base_endpoint: str,
        sort_key: str = "id_desc",
        rec_total: int = 0,
        rec_per_page: int = 20,
        page_id: int = 1,
        operation: str = "assignedTo"
    ) -> str:
        """构建分页URL
        
        Args:
            base_endpoint: 基础端点，如 'my-task', 'my-bug'
            sort_key: 排序键，如 'id_desc'
            rec_total: 总记录数
            rec_per_page: 每页记录数
            page_id: 页码
            operation: 操作，如 'assignedTo', 'openedBy', 'resolvedBy', 'closedBy', 'finishedBy'
        Returns:
            分页URL，如 'my-task-assignedTo-id_desc-301-20-2.json'
        """
        return f"{base_endpoint}-{operation}-{sort_key}-{rec_total}-{rec_per_page}-{page_id}.json"

    @staticmethod
    def extract_pager_info(data: Dict[str, Any]) -> Optional[PagerInfo]:
        """从API响应数据中提取分页信息
        
        Args:
            data: 解析后的API响应数据
            
        Returns:
            分页信息对象，如果没有分页信息则返回None
        """
        pager_data = data.get('pager')
        if not pager_data:
            return None
        
        try:
            return PagerInfo(
                rec_total=pager_data.get('recTotal', 0),
                rec_per_page=pager_data.get('recPerPage', 20),
                page_id=pager_data.get('pageID', 1),
                page_total=pager_data.get('pageTotal', 1)
            )
        except Exception:
            return None
    
    @staticmethod
    def calculate_page_range(current_page: int, total_pages: int, window_size: int = 5) -> List[int]:
        """计算分页显示范围
        
        Args:
            current_page: 当前页码
            total_pages: 总页数  
            window_size: 显示窗口大小
            
        Returns:
            页码列表
        """
        if total_pages <= window_size:
            return list(range(1, total_pages + 1))
        
        # 计算显示窗口的起始和结束位置
        half_window = window_size // 2
        start = max(1, current_page - half_window)
        end = min(total_pages, start + window_size - 1)
        
        # 如果结尾不够，调整起始位置
        if end - start + 1 < window_size:
            start = max(1, end - window_size + 1)
        
        return list(range(start, end + 1))
