"""
禅道API通用数据模型

本模块定义了禅道API的通用响应结构、错误处理和基础数据类型。
所有具体的数据模型都应该基于这些基础模型构建，确保API响应的一致性和类型安全。

主要功能：
- 统一的响应状态枚举
- 通用的异常处理类
- 基础响应模型（泛型支持）
- 特殊情况的响应模型（如字符串数据需要二次解析）

设计原则：
- 类型安全：所有模型都有完整的类型提示
- 可扩展：使用泛型支持不同类型的数据
- 一致性：统一的字段命名和结构
- 灵活性：支持禅道API的各种响应格式
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar, List, Dict, Union
from enum import Enum

# 泛型类型变量，用于支持不同类型的数据
T = TypeVar('T')


class ResponseStatus(str, Enum):
    """禅道API响应状态枚举
    
    定义禅道API返回的标准状态值。
    禅道API通常使用这些状态来表示请求的处理结果。
    
    Attributes:
        SUCCESS: 请求成功处理
        FAILED: 请求处理失败（业务逻辑错误）
        ERROR: 请求处理出错（系统错误）
    """
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


class ZenTaoError(Exception):
    """禅道API错误异常类
    
    用于封装禅道API返回的错误信息，提供结构化的异常处理。
    继承自Python标准异常类，同时保留原始的错误数据。
    
    Attributes:
        status (str): 错误状态，通常是"failed"或"error"
        message (str): 错误消息描述
        data (Any): 附加的错误数据，可能包含详细的错误信息
    
    Example:
        ```python
        if response_data["status"] != "success":
            raise ZenTaoError(
                status=response_data["status"],
                message=response_data.get("message", "未知错误"),
                data=response_data.get("data")
            )
        ```
    """
    
    def __init__(self, status: str, message: str, data: Any = None) -> None:
        """初始化禅道错误异常
        
        Args:
            status: 错误状态代码
            message: 错误消息描述
            data: 附加的错误数据（可选）
        """
        self.status = status
        self.message = message
        self.data = data
        super().__init__(message)
    
    def __str__(self) -> str:
        """返回错误的字符串表示"""
        return f"ZenTaoError({self.status}): {self.message}"
    
    def __repr__(self) -> str:
        """返回错误的详细表示"""
        return f"ZenTaoError(status='{self.status}', message='{self.message}', data={self.data})"


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型
    
    定义禅道API响应的基本结构。这是一个泛型模型，
    可以通过类型参数T来指定具体的数据类型。
    
    所有禅道API的响应都至少包含status字段，
    某些响应还可能包含message字段用于说明。
    
    Type Parameters:
        T: 响应数据的类型
    
    Attributes:
        status: 响应状态，必须是ResponseStatus枚举值之一
        message: 可选的响应消息，通常在出错时提供详细说明
    
    Example:
        ```python
        # 基础响应，只有状态
        response = BaseResponse[None](status="success")
        
        # 带消息的响应
        response = BaseResponse[None](
            status="failed", 
            message="用户名或密码错误"
        )
        ```
    """
    status: ResponseStatus = Field(
        description="响应状态，表示请求的处理结果"
    )
    message: Optional[str] = Field(
        default=None, 
        description="可选的响应消息，通常在状态为failed或error时提供详细说明"
    )
    
    def is_success(self) -> bool:
        """检查响应是否成功
        
        Returns:
            bool: 如果status为SUCCESS则返回True，否则返回False
        """
        return self.status == ResponseStatus.SUCCESS
    
    def raise_for_status(self) -> None:
        """如果响应不成功则抛出异常
        
        Raises:
            ZenTaoError: 当响应状态不是success时
        """
        if not self.is_success():
            raise ZenTaoError(
                status=self.status.value,
                message=self.message or f"请求失败，状态: {self.status.value}"
            )


class DataResponse(BaseResponse[T]):
    """带数据的响应模型
    
    用于包含具体数据的API响应。这是最常用的响应模型，
    在基础响应的基础上增加了data字段来承载实际的业务数据。
    
    Type Parameters:
        T: data字段的数据类型
    
    Attributes:
        data: 响应的业务数据，类型由泛型参数T指定
    
    Example:
        ```python
        # 用户信息响应
        response = DataResponse[UserModel](
            status="success",
            data=UserModel(id=1, name="张三")
        )
        
        # 项目列表响应
        response = DataResponse[List[ProjectModel]](
            status="success",
            data=[ProjectModel(id=1, name="项目1")]
        )
        ```
    """
    data: T = Field(description="响应的业务数据")


class StringDataResponse(BaseResponse):
    """字符串数据响应模型
    
    专门用于处理禅道API中一种特殊的响应格式：
    data字段是JSON字符串而不是直接的对象。
    
    禅道的某些API会返回这种格式，需要对data字段进行二次JSON解析。
    使用这个模型可以明确标识这种情况，便于后续处理。
    
    Attributes:
        data: JSON字符串格式的数据，需要使用json.loads()进行解析
    
    Example:
        ```python
        # 禅道API可能返回这样的响应
        {
            "status": "success",
            "data": "{\"sessionID\": \"abc123\", \"user\": {...}}"
        }
        
        # 使用模型解析
        response = StringDataResponse.model_validate(api_response)
        actual_data = json.loads(response.data)
        ```
    """
    data: str = Field(description="JSON字符串格式的数据，需要进行二次解析")
    
    def parse_data(self) -> Dict[str, Any]:
        """解析JSON字符串数据
        
        Returns:
            Dict[str, Any]: 解析后的数据字典
            
        Raises:
            json.JSONDecodeError: 当data不是有效的JSON字符串时
        """
        import json
        return json.loads(self.data)


class ListResponse(BaseResponse[T]):
    """列表响应模型
    
    用于包含列表数据的API响应，通常用于分页查询等场景。
    除了基本的列表数据外，还可以包含分页相关的元信息。
    
    Type Parameters:
        T: 列表元素的数据类型
    
    Attributes:
        data: 响应的列表数据
        total: 可选的总记录数，用于分页
        page: 可选的当前页码，用于分页
        limit: 可选的每页数量，用于分页
    
    Example:
        ```python
        # 项目列表响应
        response = ListResponse[ProjectModel](
            status="success",
            data=[ProjectModel(id=1, name="项目1")],
            total=100,
            page=1,
            limit=10
        )
        ```
    """
    data: List[T] = Field(description="响应的列表数据")
    total: Optional[int] = Field(default=None, description="总记录数，用于分页")
    page: Optional[int] = Field(default=None, description="当前页码，从1开始")
    limit: Optional[int] = Field(default=None, description="每页数量")
    
    def has_pagination(self) -> bool:
        """检查是否包含分页信息
        
        Returns:
            bool: 如果包含分页信息则返回True
        """
        return self.total is not None and self.page is not None


class ErrorResponse(BaseResponse):
    """错误响应模型
    
    专门用于处理错误响应的模型。
    当API返回错误时，通常会包含错误代码和详细的错误信息。
    
    Attributes:
        error_code: 可选的错误代码
        error_details: 可选的详细错误信息
    """
    error_code: Optional[str] = Field(default=None, description="错误代码")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="详细错误信息")


# 常用的响应类型别名，简化使用
SimpleResponse = BaseResponse[None]  # 只有状态的简单响应
DictResponse = DataResponse[Dict[str, Any]]  # 包含字典数据的响应
StringResponse = DataResponse[str]  # 包含字符串数据的响应
IntResponse = DataResponse[int]  # 包含整数数据的响应


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    limit: int = Field(default=20, ge=1, le=100, description="每页数量")


class SortParams(BaseModel):
    """排序参数"""
    sort_field: str = Field(description="排序字段")
    sort_order: str = Field(default="asc", pattern="^(asc|desc)$", description="排序方向")


class FilterParams(BaseModel):
    """筛选参数基类"""
    pass


class CommonOperationResponse(BaseResponse):
    """通用操作响应（创建、更新、删除等）"""
    id: Optional[str] = Field(default=None, description="操作对象的ID")
    affected_rows: Optional[int] = Field(default=None, description="影响的行数")


# 常用的状态枚举
class CommonStatus(str, Enum):
    """通用状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ENABLED = "enabled"
    DISABLED = "disabled"
    NORMAL = "normal"
    DELETED = "deleted"


class YesNoFlag(str, Enum):
    """是否标识枚举"""
    YES = "1"
    NO = "0"


# 日期时间相关常量
ZERO_DATE = "0000-00-00"
ZERO_DATETIME = "0000-00-00 00:00:00"


# 验证函数
def validate_date_string(date_str: str) -> bool:
    """验证日期字符串格式"""
    if date_str == ZERO_DATE:
        return True
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_datetime_string(datetime_str: str) -> bool:
    """验证日期时间字符串格式"""
    if datetime_str == ZERO_DATETIME:
        return True
    try:
        from datetime import datetime
        datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        return True
    except ValueError:
        return False
