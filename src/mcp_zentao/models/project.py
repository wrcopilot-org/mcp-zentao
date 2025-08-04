"""
项目管理数据模型
定义禅道项目相关的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import date
from collections import OrderedDict


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

    def __repr__(self) -> str:
        """简洁的字符串表示"""
        return f"Project({self.id}: {self.name} - {self.status.value})"

    def display_fields(self) -> OrderedDict[str, Any]:
        """返回与禅道界面字段匹配的有序字典"""
        return OrderedDict([
            ("ID", self.id),
            ("项目代号", self.code),
            ("项目名称", self.name),
            ("开始日期", self.begin),
            ("截止日期", self.end),
            ("状态", self._get_status_display()),
            ("角色", self._get_role_display()),
            ("加盟日", self.join),
            ("可用工时/天", self._get_available_hours_display()),
        ])

    def _get_status_display(self) -> str:
        """获取状态的中文显示"""
        status_map = {
            ProjectStatus.WAIT: "未开始",
            ProjectStatus.DOING: "进行中",
            ProjectStatus.SUSPENDED: "已挂起",
            ProjectStatus.CLOSED: "已关闭"
        }
        return status_map.get(self.status, self.status.value)

    def _get_role_display(self) -> str:
        """获取角色的中文显示"""
        # 角色映射可能需要根据实际系统进行调整
        role_map = {
            "po": "产品经理",
            "pm": "项目经理", 
            "qd": "测试负责人",
            "rd": "开发负责人",
            "dev": "开发人员",
            "test": "测试人员",
            "pm1": "项目经理",
            "admin": "管理员"
        }
        return role_map.get(self.role.lower(), self.role)

    def _get_available_hours_display(self) -> str:
        """获取可用工时显示"""
        if self.hours and self.hours != "0":
            return self.hours
        return "8.0"  # 默认8小时工作制

    def _get_priority_display(self) -> str:
        """获取优先级的中文显示"""
        priority_map = {
            ProjectPriority.LOW: "低",
            ProjectPriority.NORMAL: "正常",
            ProjectPriority.HIGH: "高", 
            ProjectPriority.URGENT: "紧急"
        }
        return priority_map.get(self.pri, str(self.pri.value))

    def available_actions(self) -> Dict[str, bool]:
        """返回可用操作的状态"""
        return {
            "开始": self.status == ProjectStatus.WAIT,
            "挂起": self.status == ProjectStatus.DOING,
            "激活": self.status == ProjectStatus.SUSPENDED,
            "关闭": self.status in [ProjectStatus.DOING, ProjectStatus.SUSPENDED],
            "编辑": self.status != ProjectStatus.CLOSED,
            "删除": self.status == ProjectStatus.CLOSED
        }

    def display_summary(self) -> str:
        """格式化的展示摘要"""
        fields = self.display_fields()
        actions = self.available_actions()
        
        lines = []
        lines.append("=" * 50)
        lines.append(f"项目详情: {fields['项目名称']}")
        lines.append("=" * 50)
        
        # 基本信息
        for key, value in fields.items():
            lines.append(f"{key:10}: {value}")
        
        # 团队信息
        lines.append(f"\n团队信息:")
        if self.PO:
            lines.append(f"  产品负责人: {self.PO}")
        if self.PM:
            lines.append(f"  项目经理  : {self.PM}")
        if self.QD:
            lines.append(f"  测试负责人: {self.QD}")
        if self.RD:
            lines.append(f"  开发负责人: {self.RD}")
        
        # 进度信息
        lines.append(f"\n工时统计:")
        lines.append(f"  预估工时  : {self.estimate}")
        lines.append(f"  已消耗    : {self.consumed}")
        lines.append(f"  剩余工时  : {self.left}")
        
        # 延期情况
        if hasattr(self, 'delay') and self.delay and self.delay > 0:
            lines.append(f"  延期天数  : {self.delay}天")
        
        # 可用操作
        lines.append(f"\n可用操作:")
        for action, available in actions.items():
            status = "✓" if available else "✗"
            lines.append(f"  {status} {action}")
        
        return "\n".join(lines)


class ProjectListData(BaseModel):
    """项目列表数据结构"""
    projects: List[ProjectModel] = Field(description="项目列表")
    
    def get_project_list(self) -> List[ProjectModel]:
        """获取项目列表"""
        return self.projects


class ProjectListResponse(BaseModel):
    """获取项目列表的API响应"""
    status: str = Field(description="响应状态")
    data: str = Field(description="JSON字符串格式的项目数据")
    
    def get_project_data(self) -> ProjectListData:
        """解析data字段并返回ProjectListData对象"""
        import json
        parsed_data = json.loads(self.data)
        return ProjectListData.model_validate(parsed_data)
    
    def get_project_list(self) -> List[ProjectModel]:
        """获取项目列表"""
        project_data = self.get_project_data()
        return project_data.get_project_list()
    
    def get_project_list_data(self) -> Dict[str, Any]:
        """获取原始项目列表数据（用于分页）"""
        import json
        return json.loads(self.data)


class ProjectDetailResponse(BaseModel):
    """项目详情响应"""
    status: str = Field(description="响应状态")
    project: ProjectModel = Field(description="项目详细信息")


class ProjectTaskData(BaseModel):
    """项目任务数据结构（来自API的data字段）"""
    title: str = Field(description="页面标题")
    projects: Dict[str, str] = Field(description="所有项目列表")
    project: Dict[str, Any] = Field(description="当前项目信息")  # 使用Dict来避免字段不匹配
    childProjects: List[Any] = Field(description="子项目列表")
    products: List[Any] = Field(description="产品列表")
    teamMembers: Dict[str, Dict[str, Any]] = Field(description="团队成员信息")
    modulePairs: List[Any] = Field(description="模块对")
    tasks: Dict[str, Dict[str, Any]] = Field(description="任务列表，任务ID到任务信息的映射")
    summary: str = Field(description="任务统计摘要")
    tabID: str = Field(description="标签页ID")
    pager: Optional[Dict[str, Any]] = Field(default=None, description="分页信息")
    recTotal: int = Field(description="总记录数")
    recPerPage: int = Field(description="每页记录数")
    orderBy: str = Field(description="排序方式")
    browseType: str = Field(description="浏览类型")
    status: str = Field(description="状态过滤")
    users: Dict[str, str] = Field(description="用户列表，用户名到真实姓名的映射")
    param: int = Field(description="参数")
    projectID: str = Field(description="项目ID")
    productID: int = Field(description="产品ID")
    modules: List[str] = Field(description="模块列表")
    moduleID: int = Field(description="模块ID")
    memberPairs: Dict[str, str] = Field(description="成员对，用户名到真实姓名的映射")
    branchGroups: List[Any] = Field(description="分支组")
    setModule: bool = Field(description="是否设置模块")


class ProjectTaskResponse(BaseModel):
    """项目任务响应"""
    status: str = Field(description="响应状态")
    data: str = Field(description="JSON字符串格式的任务数据")
    md5: Optional[str] = Field(default=None, description="数据MD5校验")
    
    def get_project_task_data(self) -> ProjectTaskData:
        """解析data字段并返回ProjectTaskData对象"""
        import json
        parsed_data = json.loads(self.data)
        return ProjectTaskData.model_validate(parsed_data)
    
    def get_project_info(self) -> Dict[str, Any]:
        """获取项目信息"""
        task_data = self.get_project_task_data()
        return task_data.project
    
    def get_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取任务列表"""
        task_data = self.get_project_task_data()
        return task_data.tasks
    
    def get_team_members(self) -> Dict[str, Dict[str, Any]]:
        """获取团队成员信息"""
        task_data = self.get_project_task_data()
        return task_data.teamMembers
    
    def get_summary(self) -> str:
        """获取任务统计摘要"""
        task_data = self.get_project_task_data()
        return task_data.summary


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
