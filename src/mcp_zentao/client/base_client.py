"""
禅道API基础客户端

提供HTTP请求、错误处理、响应解析等基础功能。
"""

import json
from typing import Any, Dict, Optional, Type, TypeVar, Union, List
import httpx
from pydantic import BaseModel

from ..models.common import BaseResponse, ResponseStatus, ZenTaoError
from ..models.pagination import PaginationHelper, PagerInfo, PageParams

T = TypeVar('T', bound=BaseModel)


class BaseClient:
    """禅道API基础客户端类
    
    提供HTTP请求、错误处理、响应解析等基础功能。
    所有具体的客户端都应该继承此类。
    """
    
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        """初始化基础客户端
        
        Args:
            base_url: 禅道系统的基础URL，例如 http://zentao.example.com
            timeout: 请求超时时间，默认30秒
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._session_id: Optional[str] = None
        
        # 创建HTTP客户端（支持cookies以维持会话状态）
        self._client = httpx.Client(
            timeout=timeout,
            headers={
                'User-Agent': 'MCP-ZenTao-Client/1.0',
                'Accept': 'application/json',
            },
            # 启用cookie支持以维持会话状态
            cookies=httpx.Cookies()
        )
    
    def __enter__(self) -> 'BaseClient':
        """上下文管理器进入"""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器退出"""
        self.close()
    
    def close(self) -> None:
        """关闭HTTP客户端"""
        if hasattr(self, '_client'):
            self._client.close()
    
    @property
    def session_id(self) -> Optional[str]:
        """获取当前会话ID"""
        return self._session_id
    
    @session_id.setter
    def session_id(self, value: Optional[str]) -> None:
        """设置会话ID"""
        self._session_id = value
    
    def _build_url(self, endpoint: str, **params: Any) -> str:
        """构建完整的API URL
        
        Args:
            endpoint: API端点，例如 'api-getSessionID.json'
            **params: URL参数，如sessionid等
            
        Returns:
            完整的API URL
        """
        # 替换URL中的参数占位符
        for key, value in params.items():
            placeholder = f'{{{key}}}'
            if placeholder in endpoint:
                endpoint = endpoint.replace(placeholder, str(value))
        
        return f"{self.base_url}/{endpoint}"
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **url_params: Any
    ) -> httpx.Response:
        """发起HTTP请求
        
        Args:
            method: HTTP方法 (GET, POST, PUT, DELETE)
            endpoint: API端点
            params: URL查询参数
            data: 请求体数据
            **url_params: URL路径参数
            
        Returns:
            HTTP响应对象
            
        Raises:
            ZenTaoError: 禅道API错误
            httpx.HTTPError: HTTP请求错误
        """
        url = self._build_url(endpoint, **url_params)
        
        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None
            )
            response.raise_for_status()
            return response
            
        except httpx.HTTPStatusError as e:
            raise ZenTaoError(
                status="error",
                message=f"HTTP错误 {e.response.status_code}: {e.response.text}",
                data=None
            )
        except httpx.RequestError as e:
            raise ZenTaoError(
                status="error", 
                message=f"请求错误: {str(e)}",
                data=None
            )
    
    def _parse_response(
        self,
        response: httpx.Response,
        response_model: Type[T]
    ) -> T:
        """解析API响应
        
        Args:
            response: HTTP响应对象
            response_model: 响应数据模型类
            
        Returns:
            解析后的响应数据
            
        Raises:
            ZenTaoError: 数据解析错误或API错误
        """
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            raise ZenTaoError(
                status="error",
                message=f"JSON解析错误: {str(e)}",
                data=None
            )
        
        # 检查API响应状态
        if not isinstance(response_data, dict):
            raise ZenTaoError(
                status="error",
                message="无效的响应格式",
                data=response_data
            )
        
        status = response_data.get('status')
        if status != 'success':
            error_message = response_data.get('message', '未知错误')
            raise ZenTaoError(
                status=status or "error",
                message=error_message,
                data=response_data.get('data')
            )
        
        # 解析为指定的数据模型
        try:
            return response_model.model_validate(response_data)
        except Exception as e:
            raise ZenTaoError(
                status="error",
                message=f"数据模型验证失败: {str(e)}",
                data=response_data
            )
    
    def get(
        self,
        endpoint: str,
        response_model: Type[T],
        params: Optional[Dict[str, Any]] = None,
        **url_params: Any
    ) -> T:
        """发起GET请求
        
        Args:
            endpoint: API端点
            response_model: 响应数据模型类
            params: URL查询参数
            **url_params: URL路径参数
            
        Returns:
            解析后的响应数据
        """
        response = self._make_request('GET', endpoint, params=params, **url_params)
        return self._parse_response(response, response_model)
    
    def post(
        self,
        endpoint: str,
        response_model: Type[T],
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **url_params: Any
    ) -> T:
        """发起POST请求
        
        Args:
            endpoint: API端点
            response_model: 响应数据模型类
            data: 请求体数据
            params: URL查询参数
            **url_params: URL路径参数
            
        Returns:
            解析后的响应数据
        """
        response = self._make_request('POST', endpoint, params=params, data=data, **url_params)
        return self._parse_response(response, response_model)
    
    def put(
        self,
        endpoint: str,
        response_model: Type[T],
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **url_params: Any
    ) -> T:
        """发起PUT请求
        
        Args:
            endpoint: API端点
            response_model: 响应数据模型类
            data: 请求体数据
            params: URL查询参数
            **url_params: URL路径参数
            
        Returns:
            解析后的响应数据
        """
        response = self._make_request('PUT', endpoint, params=params, data=data, **url_params)
        return self._parse_response(response, response_model)
    
    def delete(
        self,
        endpoint: str,
        response_model: Type[T],
        params: Optional[Dict[str, Any]] = None,
        **url_params: Any
    ) -> T:
        """发起DELETE请求
        
        Args:
            endpoint: API端点
            response_model: 响应数据模型类
            params: URL查询参数
            **url_params: URL路径参数
            
        Returns:
            解析后的响应数据
        """
        response = self._make_request('DELETE', endpoint, params=params, **url_params)
        return self._parse_response(response, response_model)
    
    def get_paginated(
        self,
        base_endpoint: str,
        response_model: Type[T],
        page: int = 1,
        per_page: int = 20,
        sort_key: str = "id_desc",
        params: Optional[Dict[str, Any]] = None,
        **url_params: Any
    ) -> T:
        """发起分页GET请求
        
        Args:
            base_endpoint: 基础端点，如 'my-task', 'my-bug'
            response_model: 响应数据模型类
            page: 页码，从1开始
            per_page: 每页记录数
            sort_key: 排序键，如 'id_desc'
            params: URL查询参数
            **url_params: URL路径参数
            
        Returns:
            解析后的响应数据
        """
        # 首先获取第一页以获取总记录数
        if page == 1:
            # 直接使用基础API获取第一页
            first_page_response = self.get(
                endpoint=f"{base_endpoint}.json",
                response_model=response_model,
                params=params,
                **url_params
            )
            return first_page_response
        else:
            # 需要先获取总记录数，然后请求指定页面
            first_page_response = self.get(
                endpoint=f"{base_endpoint}.json", 
                response_model=response_model,
                params=params,
                **url_params
            )
            
            # 从第一页响应中提取分页信息
            rec_total = self._extract_rec_total(first_page_response)
            
            # 构建分页URL
            paginated_endpoint = PaginationHelper.build_paginated_url(
                base_endpoint=base_endpoint,
                sort_key=sort_key,
                rec_total=rec_total,
                rec_per_page=per_page,
                page_id=page
            )
            
            return self.get(
                endpoint=paginated_endpoint,
                response_model=response_model,
                params=params,
                **url_params
            )
    
    def get_all_pages(
        self,
        base_endpoint: str,
        response_model: Type[T],
        per_page: int = 20,
        sort_key: str = "id_desc",
        params: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        **url_params: Any
    ) -> List[T]:
        """获取所有页面的数据
        
        Args:
            base_endpoint: 基础端点
            response_model: 响应数据模型类
            per_page: 每页记录数
            sort_key: 排序键
            params: URL查询参数
            max_pages: 最大页数限制，None表示无限制
            **url_params: URL路径参数
            
        Returns:
            所有页面的响应数据列表
        """
        results = []
        
        # 获取第一页
        first_page = self.get_paginated(
            base_endpoint=base_endpoint,
            response_model=response_model,
            page=1,
            per_page=per_page,
            sort_key=sort_key,
            params=params,
            **url_params
        )
        results.append(first_page)
        
        # 提取分页信息
        rec_total = self._extract_rec_total(first_page)
        total_pages = (rec_total + per_page - 1) // per_page  # 向上取整
        
        # 限制最大页数
        if max_pages:
            total_pages = min(total_pages, max_pages)
        
        # 获取剩余页面
        for page in range(2, total_pages + 1):
            try:
                page_response = self.get_paginated(
                    base_endpoint=base_endpoint,
                    response_model=response_model,
                    page=page,
                    per_page=per_page,
                    sort_key=sort_key,
                    params=params,
                    **url_params
                )
                results.append(page_response)
            except Exception as e:
                # 如果某页获取失败，记录错误但继续
                print(f"获取第{page}页失败: {e}")
                break
        
        return results
    
    def _extract_rec_total(self, response: BaseModel) -> int:
        """从响应中提取总记录数
        
        Args:
            response: API响应对象
            
        Returns:
            总记录数
        """
        # 尝试不同的方式提取总记录数
        try:
            # 对于任务响应
            if hasattr(response, 'get_task_list_data'):
                data = response.get_task_list_data()
                return data.get('recTotal', 0)
            
            # 对于缺陷响应  
            if hasattr(response, 'get_bug_list_data'):
                data = response.get_bug_list_data()
                return data.get('recTotal', 0)
                
            # 对于项目响应
            if hasattr(response, 'get_project_list_data'):
                data = response.get_project_list_data()
                return data.get('recTotal', 0)
                
            # 如果有data属性，尝试解析
            if hasattr(response, 'data') and response.data:
                import json
                if isinstance(response.data, str):
                    parsed_data = json.loads(response.data)
                    return parsed_data.get('recTotal', 0)
                elif isinstance(response.data, dict):
                    return response.data.get('recTotal', 0)
                    
        except Exception as e:
            print(f"提取总记录数失败: {e}")
            
        # 默认返回0
        return 0
