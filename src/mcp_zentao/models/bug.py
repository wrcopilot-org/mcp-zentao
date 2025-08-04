"""
缺陷管理数据模型
定义禅道缺陷相关的数据结构
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
from collections import OrderedDict


class BugSeverity(int, Enum):
    """缺陷严重程度枚举"""
    LOWEST = 1    # 1-建议
    LOW = 2       # 2-一般
    NORMAL = 3    # 3-重要
    HIGH = 4      # 4-严重


class BugPriority(int, Enum):
    """缺陷优先级枚举"""
    LOWEST = 1    # 最低
    LOW = 2       # 低
    NORMAL = 3    # 正常
    HIGH = 4      # 高


class BugStatus(str, Enum):
    """缺陷状态枚举"""
    ACTIVE = "active"      # 激活
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"      # 已关闭


class BugType(str, Enum):
    """缺陷类型枚举"""
    CODEERROR = "codeerror"        # 代码错误
    INTERFACE = "interface"        # 界面优化
    CONFIG = "config"              # 配置相关
    INSTALL = "install"            # 安装部署
    SECURITY = "security"          # 安全相关
    PERFORMANCE = "performance"    # 性能问题
    STANDARD = "standard"          # 标准规范
    AUTOMATION = "automation"      # 测试脚本
    OTHERS = "others"              # 其他
    
    # 中文系统特有的类型代码
    GNWT = "gnwt"                  # 功能问题
    JMLJ = "jmlj"                  # 界面逻辑
    LWT = "lwt"                    # 逻辑问题
    SJQX = "sjqx"                  # 数据缺陷


class BugResolution(str, Enum):
    """缺陷解决方案枚举"""
    FIXED = "fixed"                # 已修复
    POSTPONED = "postponed"        # 延期处理
    WILLNOTFIX = "willnotfix"      # 不予修复
    BYDESIGN = "bydesign"          # 设计如此
    DUPLICATE = "duplicate"        # 重复Bug
    EXTERNAL = "external"          # 外部原因
    NOTREPRO = "notrepro"          # 无法重现


class BugModel(BaseModel):
    """缺陷信息模型"""
    # 基本标识
    id: str = Field(description="缺陷ID")
    product: str = Field(description="所属产品ID")
    branch: str = Field(description="分支ID")
    module: str = Field(description="所属模块ID")
    project: str = Field(description="所属项目ID")
    plan: str = Field(description="所属计划ID")
    
    # 需求关联
    story: str = Field(description="相关需求ID")
    storyVersion: str = Field(description="需求版本")
    task: str = Field(description="相关任务ID")
    toTask: str = Field(description="转任务ID")
    toStory: str = Field(description="转需求ID")
    
    # 缺陷基本信息
    title: str = Field(description="缺陷标题")
    keywords: Optional[str] = Field(default="", description="关键词")
    severity: BugSeverity = Field(description="严重程度")
    pri: BugPriority = Field(description="优先级")
    type: BugType = Field(description="缺陷类型")
    os: Optional[str] = Field(default="", description="操作系统")
    browser: Optional[str] = Field(default="", description="浏览器")
    
    # 重现信息
    steps: Optional[str] = Field(default="", description="重现步骤")
    status: BugStatus = Field(description="缺陷状态")
    subStatus: Optional[str] = Field(default="", description="子状态")
    color: Optional[str] = Field(default="", description="颜色标识")
    confirmed: str = Field(description="是否确认，1=已确认，0=未确认")
    
    # 创建信息
    openedBy: str = Field(description="创建者")
    openedDate: str = Field(description="创建时间")
    openedBuild: str = Field(description="创建时的版本")
    
    # 分配信息
    assignedTo: str = Field(description="指派给")
    assignedDate: str = Field(description="指派时间")
    
    # 解决信息
    resolvedBy: Optional[str] = Field(default="", description="解决者")
    resolution: Optional[BugResolution] = Field(default=None, description="解决方案")
    resolvedBuild: Optional[str] = Field(default="", description="解决版本")
    resolvedDate: str = Field(description="解决时间")
    
    # 关闭信息
    closedBy: Optional[str] = Field(default="", description="关闭者")
    closedDate: str = Field(description="关闭时间")
    
    # 激活信息
    activatedBy: Optional[str] = Field(default="", description="激活者")
    activatedDate: str = Field(description="激活时间")
    activatedCount: str = Field(description="激活次数")
    
    # 邮件通知
    mailto: Optional[str] = Field(default="", description="邮件通知列表")
    
    # 编辑信息
    lastEditedBy: str = Field(description="最后编辑者")
    lastEditedDate: str = Field(description="最后编辑时间")
    
    # 删除标识
    deleted: str = Field(description="是否删除，0=未删除")
    
    # 重复缺陷
    duplicateBug: str = Field(description="重复的缺陷ID")
    linkBug: str = Field(description="相关缺陷ID")
    
    # 用例关联
    case: str = Field(description="相关用例ID")
    caseVersion: str = Field(description="用例版本")
    result: str = Field(description="测试结果ID")
    
    # 需求变更
    feedbackBy: Optional[str] = Field(default="", description="反馈者")
    notifyEmail: Optional[str] = Field(default="", description="通知邮箱")
    
    @field_validator('resolution', mode='before')
    @classmethod
    def validate_resolution(cls, v):
        """处理空字符串的resolution字段"""
        if v == "" or v is None:
            return None
        return v

    def __repr__(self) -> str:
        """简洁的字符串表示"""
        return f"Bug({self.id}: {self.title} - {self.status.value})"

    def display_fields(self) -> OrderedDict[str, Any]:
        """返回与禅道界面字段匹配的有序字典"""
        return OrderedDict([
            ("ID", self.id),
            ("级别", self._get_severity_display()),
            ("P", self._get_priority_display()),
            ("类型", self._get_type_display()),
            ("Bug标题", self.title),
            ("创建", self.openedBy),
            ("指派给", self.assignedTo),
            ("解决", self.resolvedBy or ""),
            ("方案", self._get_resolution_display()),
        ])

    def _get_severity_display(self) -> str:
        """获取严重程度的中文显示"""
        severity_map = {
            BugSeverity.LOWEST: "1-建议",
            BugSeverity.LOW: "2-一般", 
            BugSeverity.NORMAL: "3-重要",
            BugSeverity.HIGH: "4-严重"
        }
        return severity_map.get(self.severity, str(self.severity.value))

    def _get_priority_display(self) -> str:
        """获取优先级的中文显示"""
        priority_map = {
            BugPriority.LOWEST: "低",
            BugPriority.LOW: "低",
            BugPriority.NORMAL: "中", 
            BugPriority.HIGH: "高"
        }
        return priority_map.get(self.pri, str(self.pri.value))

    def _get_type_display(self) -> str:
        """获取类型的中文显示"""
        type_map = {
            BugType.CODEERROR: "代码错误",
            BugType.INTERFACE: "界面优化",
            BugType.CONFIG: "配置相关",
            BugType.INSTALL: "安装部署",
            BugType.SECURITY: "安全相关",
            BugType.PERFORMANCE: "性能问题",
            BugType.STANDARD: "标准规范",
            BugType.AUTOMATION: "测试脚本",
            BugType.OTHERS: "其他",
            BugType.GNWT: "功能问题",
            BugType.JMLJ: "界面逻辑",
            BugType.LWT: "逻辑问题",
            BugType.SJQX: "数据缺陷"
        }
        return type_map.get(self.type, self.type.value)

    def _get_resolution_display(self) -> str:
        """获取解决方案的中文显示"""
        if self.resolution is None:
            return ""
        
        resolution_map = {
            BugResolution.FIXED: "已修复",
            BugResolution.POSTPONED: "延期处理",
            BugResolution.WILLNOTFIX: "不予修复",
            BugResolution.BYDESIGN: "设计如此",
            BugResolution.DUPLICATE: "重复Bug",
            BugResolution.EXTERNAL: "外部原因",
            BugResolution.NOTREPRO: "无法重现"
        }
        return resolution_map.get(self.resolution, self.resolution.value)

    def _get_status_display(self) -> str:
        """获取状态的中文显示"""
        status_map = {
            BugStatus.ACTIVE: "激活",
            BugStatus.RESOLVED: "已解决",
            BugStatus.CLOSED: "已关闭"
        }
        return status_map.get(self.status, self.status.value)

    def available_actions(self) -> Dict[str, bool]:
        """返回可用操作的状态"""
        return {
            "确认": self.status == BugStatus.ACTIVE and self.confirmed == "0",
            "解决": self.status == BugStatus.ACTIVE and self.confirmed == "1",
            "关闭": self.status == BugStatus.RESOLVED
        }

    def display_summary(self) -> str:
        """格式化的展示摘要"""
        fields = self.display_fields()
        actions = self.available_actions()
        
        lines = []
        lines.append("=" * 50)
        lines.append(f"Bug详情: {fields['Bug标题']}")
        lines.append("=" * 50)
        
        # 基本信息
        for key, value in fields.items():
            lines.append(f"{key:8}: {value}")
        
        # 当前状态
        lines.append(f"当前状态  : {self._get_status_display()}")
        lines.append(f"确认状态  : {'已确认' if self.confirmed == '1' else '未确认'}")
        
        # 可用操作
        lines.append("\n可用操作:")
        for action, available in actions.items():
            status = "✓" if available else "✗"
            lines.append(f"  {status} {action}")
        
        return "\n".join(lines)


class BugListData(BaseModel):
    """缺陷列表数据结构"""
    bugs: List[BugModel] = Field(description="缺陷列表")
    
    def get_bug_list(self) -> List[BugModel]:
        """获取缺陷列表"""
        return self.bugs


class BugListResponse(BaseModel):
    """获取缺陷列表的API响应"""
    status: str = Field(description="响应状态")
    data: str = Field(description="JSON字符串格式的缺陷数据")
    
    def get_bug_data(self) -> BugListData:
        """解析data字段并返回BugListData对象"""
        import json
        parsed_data = json.loads(self.data)
        return BugListData.model_validate(parsed_data)
    
    def get_bug_list(self) -> List[BugModel]:
        """获取缺陷列表"""
        bug_data = self.get_bug_data()
        return bug_data.get_bug_list()
    
    def get_bug_list_data(self) -> Dict[str, Any]:
        """获取原始缺陷列表数据（用于分页）"""
        import json
        return json.loads(self.data)


class BugDetailResponse(BaseModel):
    """缺陷详情响应"""
    status: str = Field(description="响应状态")
    bug: BugModel = Field(description="缺陷详细信息")


class BugCreateRequest(BaseModel):
    """创建缺陷请求"""
    product: str = Field(description="产品ID")
    title: str = Field(description="缺陷标题")
    type: BugType = Field(description="缺陷类型")
    severity: BugSeverity = Field(description="严重程度")
    pri: BugPriority = Field(default=BugPriority.NORMAL, description="优先级")
    steps: str = Field(description="重现步骤")
    assignedTo: Optional[str] = Field(default="", description="指派给")
    os: Optional[str] = Field(default="", description="操作系统")
    browser: Optional[str] = Field(default="", description="浏览器")
    keywords: Optional[str] = Field(default="", description="关键词")


class BugEditRequest(BaseModel):
    """编辑缺陷请求"""
    title: Optional[str] = Field(default=None, description="缺陷标题")
    type: Optional[BugType] = Field(default=None, description="缺陷类型")
    severity: Optional[BugSeverity] = Field(default=None, description="严重程度")
    pri: Optional[BugPriority] = Field(default=None, description="优先级")
    steps: Optional[str] = Field(default=None, description="重现步骤")
    assignedTo: Optional[str] = Field(default=None, description="指派给")
    status: Optional[BugStatus] = Field(default=None, description="缺陷状态")


class BugResolveRequest(BaseModel):
    """解决缺陷请求"""
    resolution: BugResolution = Field(description="解决方案")
    resolvedBuild: Optional[str] = Field(default="", description="解决版本")
    comment: Optional[str] = Field(default="", description="解决备注")


class BugAssignRequest(BaseModel):
    """缺陷指派请求"""
    assignedTo: str = Field(description="指派给")
    comment: Optional[str] = Field(default="", description="指派备注")


class BugConfirmRequest(BaseModel):
    """确认缺陷请求"""
    assignedTo: Optional[str] = Field(default="", description="指派给")
    comment: Optional[str] = Field(default="", description="确认备注")
