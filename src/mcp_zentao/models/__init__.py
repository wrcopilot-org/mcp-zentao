"""
MCP-ZenTao 数据模型包
提供禅道API的所有数据模型和类型定义
"""

# 通用模型
from .common import (
    ResponseStatus,
    ZenTaoError,
    BaseResponse,
    DataResponse,
    StringDataResponse,
    ListResponse,
    PaginationParams,
    SortParams,
    FilterParams,
    CommonOperationResponse,
    CommonStatus,
    YesNoFlag,
    ZERO_DATE,
    ZERO_DATETIME,
    validate_date_string,
    validate_datetime_string,
)

# 分页模型
from .pagination import (
    SortOrder,
    SortField, 
    PageParams,
    PagerInfo,
    PaginatedListParams,
    PaginatedResponse,
    PaginationHelper,
)

# 会话管理模型
from .session import (
    SessionStatus,
    SessionData,
    SessionResponse,
    LoginRequest,
    LoginResponse,
)

# 用户管理模型
from .user import (
    UserRole,
    UserGender,
    UserStatus,
    UserRights,
    UserView,
    UserModel,
    UserListResponse,
    UserDetailResponse,
)

# 项目管理模型
from .project import (
    ProjectType,
    ProjectStatus,
    ProjectACL,
    ProjectPriority,
    ProjectModel,
    ProjectListData,
    ProjectListResponse,
    ProjectDetailResponse,
    ProjectCreateRequest,
    ProjectEditRequest,
)

# 任务管理模型
from .task import (
    TaskType,
    TaskStatus,
    TaskPriority,
    TaskModel,
    TaskListData,
    TaskListResponse,
    TaskDetailResponse,
    TaskCreateRequest,
    TaskEditRequest,
    TaskFinishRequest,
    TaskAssignRequest,
)

# 缺陷管理模型
from .bug import (
    BugSeverity,
    BugPriority,
    BugStatus,
    BugType,
    BugResolution,
    BugModel,
    BugListData,
    BugListResponse,
    BugDetailResponse,
    BugCreateRequest,
    BugEditRequest,
    BugResolveRequest,
    BugAssignRequest,
    BugConfirmRequest,
)

__all__ = [
    # 通用模型
    "ResponseStatus",
    "ZenTaoError", 
    "BaseResponse",
    "DataResponse",
    "StringDataResponse",
    "ListResponse",
    "PaginationParams",
    "SortParams",
    "FilterParams",
    "CommonOperationResponse",
    "CommonStatus",
    "YesNoFlag",
    "ZERO_DATE",
    "ZERO_DATETIME",
    "validate_date_string",
    "validate_datetime_string",
    
    # 分页模型
    "SortOrder",
    "SortField", 
    "PageParams",
    "PagerInfo",
    "PaginatedListParams",
    "PaginatedResponse",
    "PaginationHelper",
    
    # 会话管理
    "SessionStatus",
    "SessionData",
    "SessionResponse",
    "LoginRequest", 
    "LoginResponse",
    
    # 用户管理
    "UserRole",
    "UserGender",
    "UserStatus",
    "UserRights",
    "UserView",
    "UserModel",
    "UserListResponse",
    "UserDetailResponse",
    
    # 项目管理
    "ProjectType",
    "ProjectStatus",
    "ProjectACL",
    "ProjectPriority",
    "ProjectModel",
    "ProjectListData",
    "ProjectListResponse",
    "ProjectDetailResponse",
    "ProjectCreateRequest",
    "ProjectEditRequest",
    
    # 任务管理
    "TaskType",
    "TaskStatus",
    "TaskPriority",
    "TaskModel",
    "TaskListData",
    "TaskListResponse",
    "TaskDetailResponse",
    "TaskCreateRequest",
    "TaskEditRequest",
    "TaskFinishRequest",
    "TaskAssignRequest",
    
    # 缺陷管理
    "BugSeverity",
    "BugPriority",
    "BugStatus",
    "BugType",
    "BugResolution",
    "BugModel",
    "BugListData",
    "BugListResponse",
    "BugDetailResponse",
    "BugCreateRequest",
    "BugEditRequest",
    "BugResolveRequest",
    "BugAssignRequest",
    "BugConfirmRequest",
]
