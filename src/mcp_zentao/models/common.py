"""
通用数据模型
定义禅道API的通用响应结构和错误处理
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar, List
from enum import Enum

T = TypeVar('T')


class ResponseStatus(str, Enum):
    """通用响应状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


class ZenTaoError(BaseModel):
    """禅道错误信息模型"""
    code: Optional[str] = Field(default=None, description="错误代码")
    message: str = Field(description="错误消息")
    details: Optional[dict] = Field(default=None, description="错误详情")


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型"""
    status: ResponseStatus = Field(description="响应状态")
    message: Optional[str] = Field(default=None, description="响应消息")
    error: Optional[ZenTaoError] = Field(default=None, description="错误信息")


class DataResponse(BaseResponse[T]):
    """带数据的响应模型"""
    data: T = Field(description="响应数据")


class StringDataResponse(BaseResponse):
    """字符串数据响应模型（用于需要额外解析的API）"""
    data: str = Field(description="JSON字符串格式的数据")


class ListResponse(BaseResponse[T]):
    """列表响应模型"""
    data: List[T] = Field(description="响应数据列表")
    total: Optional[int] = Field(default=None, description="总数")
    page: Optional[int] = Field(default=None, description="当前页")
    limit: Optional[int] = Field(default=None, description="每页数量")


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
