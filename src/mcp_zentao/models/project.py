"""
项目管理数据模型
定义禅道项目相关的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import date


class ProjectType(str, Enum):
    """项目类型枚举"""
    SPRINT = "sprint"      # 敏捷项目
    WATERFALL = "waterfall"  # 瀑布项目
    KANBAN = "kanban"      # 看板项目


class ProjectStatus(str, Enum):
    """项目状态枚举"""
    WAIT = "wait"          # 未开始
    DOING = "doing"        # 进行中
    SUSPENDED = "suspended" # 已挂起
    CLOSED = "closed"      # 已关闭


class ProjectACL(str, Enum):
    """项目访问控制枚举"""
    OPEN = "open"          # 开放
    PRIVATE = "private"    # 私有
    CUSTOM = "custom"      # 自定义


class ProjectPriority(int, Enum):
    """项目优先级枚举"""
    LOW = 1      # 低
    NORMAL = 2   # 正常
    HIGH = 3     # 高
    URGENT = 4   # 紧急


class ProjectModel(BaseModel):
    """项目信息模型"""
    # 基本标识
    id: str = Field(description="项目ID")
    root: str = Field(description="根项目ID")
    type: ProjectType = Field(description="项目类型")
    parent: str = Field(description="父项目ID，0表示顶级项目")
    
    # 分类信息
    isCat: str = Field(description="是否为分类，0=项目，1=分类")
    catID: str = Field(description="分类ID")
    
    # 项目基本信息
    name: str = Field(description="项目名称")
    code: str = Field(description="项目代码")
    desc: Optional[str] = Field(default="", description="项目描述")
    
    # 时间信息
    begin: str = Field(description="开始日期，格式：YYYY-MM-DD")
    end: str = Field(description="结束日期，格式：YYYY-MM-DD") 
    
    # 状态信息
    status: ProjectStatus = Field(description="项目状态")
    subStatus: Optional[str] = Field(default="", description="子状态")
    statge: str = Field(description="阶段，注意：原API拼写错误为statge")
    pri: ProjectPriority = Field(description="优先级")
    
    # 创建信息
    openedBy: str = Field(description="创建者")
    openedDate: str = Field(description="创建时间")
    openedVersion: str = Field(description="创建时的版本")
    
    # 关闭信息
    closedBy: Optional[str] = Field(default="", description="关闭者")
    closedDate: str = Field(description="关闭时间")
    canceledBy: Optional[str] = Field(default="", description="取消者")
    canceledDate: str = Field(description="取消时间")
    
    # 团队角色
    PO: Optional[str] = Field(default="", description="产品负责人")
    PM: Optional[str] = Field(default="", description="项目经理")
    QD: Optional[str] = Field(default="", description="测试负责人")
    RD: Optional[str] = Field(default="", description="开发负责人")
    team: str = Field(description="团队名称")
    
    # 访问控制
    acl: ProjectACL = Field(description="访问控制级别")
    whitelist: Optional[str] = Field(default="", description="白名单")
    
    # 成员信息（来自项目成员关联）
    account: str = Field(description="当前用户在项目中的账号")
    role: str = Field(description="当前用户在项目中的角色")
    limited: str = Field(description="权限是否受限")
    join: str = Field(description="加入项目时间")
    days: str = Field(description="工作天数")
    hours: str = Field(description="每日工作小时数")
    
    # 工作量统计
    estimate: str = Field(description="预估工时")
    consumed: str = Field(description="已消耗工时")
    left: str = Field(description="剩余工时")
    
    # 排序和状态
    order: str = Field(description="排序")
    deleted: str = Field(description="是否删除，0=未删除")
    delay: Optional[int] = Field(default=0, description="延期天数")


class ProjectListData(BaseModel):
    """项目列表数据结构"""
    projects: List[ProjectModel] = Field(description="项目列表")


class ProjectListResponse(BaseModel):
    """获取项目列表的API响应"""
    status: str = Field(description="响应状态")
    data: str = Field(description="JSON字符串格式的项目数据")
    
    def get_project_data(self) -> ProjectListData:
        """解析data字段并返回ProjectListData对象"""
        import json
        parsed_data = json.loads(self.data)
        return ProjectListData.model_validate(parsed_data)


class ProjectDetailResponse(BaseModel):
    """项目详情响应"""
    status: str = Field(description="响应状态")
    project: ProjectModel = Field(description="项目详细信息")


class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    name: str = Field(description="项目名称")
    code: Optional[str] = Field(default="", description="项目代码")
    type: ProjectType = Field(description="项目类型")
    begin: str = Field(description="开始日期")
    end: str = Field(description="结束日期")
    desc: Optional[str] = Field(default="", description="项目描述")
    pri: ProjectPriority = Field(default=ProjectPriority.NORMAL, description="优先级")
    acl: ProjectACL = Field(default=ProjectACL.OPEN, description="访问控制")


class ProjectEditRequest(BaseModel):
    """编辑项目请求"""
    name: Optional[str] = Field(default=None, description="项目名称")
    code: Optional[str] = Field(default=None, description="项目代码")
    begin: Optional[str] = Field(default=None, description="开始日期")
    end: Optional[str] = Field(default=None, description="结束日期")
    desc: Optional[str] = Field(default=None, description="项目描述")
    status: Optional[ProjectStatus] = Field(default=None, description="项目状态")
    pri: Optional[ProjectPriority] = Field(default=None, description="优先级")
