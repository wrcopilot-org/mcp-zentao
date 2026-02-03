"""
缺陷管理数据模型
定义禅道缺陷相关的数据结构
"""

from pydantic import BaseModel, Field
from pydantic import field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
from collections import OrderedDict


class BugSeverity(int, Enum):
    """缺陷严重程度枚举"""
    LOWEST = 1
    LOW = 2 
    NORMAL = 3
    HIGH = 4
    
    def __str__(self) -> str:
        """返回中文描述"""
        return {
            1: "提示",
            2: "其他", 
            3: "一般",
            4: "严重"
        }.get(self.value, f"级别{self.value}")
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def emoji(self) -> str:
        """严重程度对应的emoji"""
        return {
            1: "💡",
            2: "🔵", 
            3: "🟡",
            4: "🔴"
        }.get(self.value, "📊")
    
    @property
    def display_text(self) -> str:
        """带表情符号的显示文本"""
        return {
            1: "💡提示",
            2: "🔵其他", 
            3: "🟡一般",
            4: "🔴严重"
        }.get(self.value, f"📊级别{self.value}")


class BugPriority(int, Enum):
    """缺陷优先级枚举"""
    NONE = 0      # 无优先级
    HIGH = 1      # 高
    NORMAL = 2    # 中
    LOW = 3       # 低
    URGENT = 4    # 紧急
    
    def __str__(self) -> str:
        """返回中文描述"""
        return {
            0: "无",
            1: "高",
            2: "中", 
            3: "低",
            4: "紧急"
        }.get(self.value, f"级别{self.value}")
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def emoji(self) -> str:
        """优先级对应的emoji"""
        return {
            0: "⚪",
            1: "🟠",
            2: "🟡",
            3: "🟢",
            4: "🔥"
        }.get(self.value, "📊")
    
    @property
    def display_text(self) -> str:
        """带表情符号的显示文本"""
        return {
            0: "⚪无",
            1: "🟠高",
            2: "🟡中", 
            3: "🟢低",
            4: "🔥紧急"
        }.get(self.value, f"📊级别{self.value}")


class BugStatus(str, Enum):
    """缺陷状态枚举"""
    ACTIVE = "active"      # 激活
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"      # 已关闭
    
    def __str__(self) -> str:
        """返回中文描述"""
        return {
            "active": "激活",
            "resolved": "已解决", 
            "closed": "已关闭"
        }.get(self.value, self.value)
    
    def __repr__(self) -> str:
        return self.__str__()
    
    @property
    def emoji(self) -> str:
        """状态对应的emoji"""
        return {
            "active": "🔥",
            "resolved": "✅",
            "closed": "🔒"
        }.get(self.value, "📝")
    
    @property
    def display_text(self) -> str:
        """带表情符号的显示文本"""
        return {
            "active": "🔥激活",
            "resolved": "✅已解决", 
            "closed": "🔒已关闭"
        }.get(self.value, f"🔍{self.value}")


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
    LWT = "lwt"                    # 历史遗留
    JMLJ = "jmlj"                  # 界面交互  
    JMYH = "jmyh"                  # 界面优化
    XNWT = "xnwt"                  # 性能问题
    JRXWT = "jrxwt"                # 兼容性问题
    SJWT = "sjwt"                  # 随机问题
    XGYR = "xgyr"                  # 修改引入
    YHFK = "yhfk"                  # 用户反馈
    XQJY = "xqjy"                  # 需求建议
    XZXQ = "xzxq"                  # 新增需求
    SJQX = "sjqx"                  # 设计问题
    PZWT = "pzwt"                  # 配置问题
    QT = "qt"                      # 其他
    
    def __str__(self) -> str:
        """返回中文描述"""
        return {
            "codeerror": "代码错误",
            "interface": "界面优化", 
            "config": "配置相关",
            "install": "安装部署",
            "security": "安全相关",
            "performance": "性能问题",
            "standard": "标准规范",
            "automation": "测试脚本",
            "others": "其他",
            # 中文系统特有类型
            "gnwt": "功能问题",
            "lwt": "历史遗留",
            "jmlj": "界面交互",
            "jmyh": "界面优化",
            "xnwt": "性能问题",
            "jrxwt": "兼容性问题",
            "sjwt": "随机问题",
            "xgyr": "修改引入",
            "yhfk": "用户反馈",
            "xqjy": "需求建议",
            "xzxq": "新增需求",
            "sjqx": "设计问题",
            "pzwt": "配置问题",
            "qt": "其他"
        }.get(self.value, self.value)
    
    def __repr__(self) -> str:
        return self.__str__()


class BugResolution(str, Enum):
    """缺陷解决方案枚举"""
    FIXED = "fixed"                # 已修复
    POSTPONED = "postponed"        # 延期处理
    WILLNOTFIX = "willnotfix"      # 不予修复
    BYDESIGN = "bydesign"          # 设计如此
    DUPLICATE = "duplicate"        # 重复Bug
    EXTERNAL = "external"          # 外部原因
    NOTREPRO = "notrepro"          # 无法重现
    NONPROBLEM = "nonproblem"      # 非问题
    
    def __str__(self) -> str:
        """返回中文描述"""
        return {
            "fixed": "已修复",
            "postponed": "延期处理", 
            "willnotfix": "不予修复",
            "bydesign": "设计如此",
            "duplicate": "重复Bug",
            "external": "外部原因",
            "notrepro": "无法重现",
            "nonproblem": "非问题"
        }.get(self.value, self.value)
    
    def __repr__(self) -> str:
        return self.__str__()


class BugActionType(str, Enum):
    """缺陷操作类型枚举"""
    OPENED = "opened"            # 创建
    COMMENTED = "commented"      # 添加备注
    ASSIGNED = "assigned"        # 指派给
    RESOLVED = "resolved"        # 解决
    CLOSED = "closed"            # 关闭
    ACTIVATED = "activated"      # 激活
    EDITED = "edited"            # 编辑
    
    def __str__(self) -> str:
        """返回中文描述"""
        return {
            "opened": "创建",
            "commented": "添加备注",
            "assigned": "指派给",
            "resolved": "解决",
            "closed": "关闭",
            "activated": "激活",
            "edited": "编辑"
        }.get(self.value, self.value)
    
    @property
    def emoji(self) -> str:
        """操作类型对应的emoji"""
        return {
            "opened": "📌",
            "commented": "💬",
            "assigned": "👤",
            "resolved": "✅",
            "closed": "🔒",
            "activated": "🔄",
            "edited": "✏️"
        }.get(self.value, "📝")
    
    @property
    def display_text(self) -> str:
        """带表情符号的显示文本"""
        return f"{self.emoji}{str(self)}"


class ActionHistoryItem(BaseModel):
    """操作历史变更条目"""
    id: str = Field(description="历史记录ID")
    action: str = Field(description="关联的操作ID")
    field: str = Field(description="变更字段名")
    old: str = Field(description="旧值")
    new: str = Field(description="新值")  
    diff: str = Field(default="", description="差异信息")
    
    def __str__(self) -> str:
        """友好的字符串表示"""
        return f"{self.field}: {self.old} → {self.new}"
    
    def __repr__(self) -> str:
        """简洁的字符串表示"""
        return f"ActionHistoryItem(field='{self.field}', old='{self.old}', new='{self.new}')"


class BugAction(BaseModel):
    """缺陷操作记录"""
    id: str = Field(description="操作ID")
    objectType: str = Field(description="对象类型")
    objectID: str = Field(description="对象ID") 
    product: str = Field(description="产品ID")
    project: str = Field(description="项目ID")
    actor: str = Field(description="操作者用户名")
    action: BugActionType = Field(description="操作类型")
    date: str = Field(description="操作时间")
    comment: str = Field(default="", description="备注内容")
    extra: str = Field(default="", description="额外信息")
    read: bool = Field(description="是否已读")
    efforted: bool = Field(description="是否计入工时")
    history: List[ActionHistoryItem] = Field(default_factory=list, description="历史变更记录")
    appendLink: Optional[str] = Field(default="", description="附加链接")
    
    @field_validator("read", "efforted", mode="before")
    @classmethod
    def validate_boolean_from_string(cls, v):
        """将字符串'0'/'1'转换为布尔值"""
        if isinstance(v, str):
            return v == "1"
        return bool(v)


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
    
    # 文件附件（仅在详情响应中存在）
    files: Optional[Dict[str, Dict[str, Any]]] = Field(default=None, description="附件文件列表")
    
    @field_validator('files', mode='before')
    @classmethod
    def validate_files(cls, v):
        """处理 files 字段的不同格式"""
        if v is None or v == "":
            return None
        # 如果是空列表，转换为 None
        if isinstance(v, list) and len(v) == 0:
            return None
        # 如果是列表但不为空，需要转换为字典格式
        if isinstance(v, list):
            # 这里可以根据实际需要进行处理
            return None
        return v
    
    @field_validator('resolution', mode='before')
    @classmethod
    def validate_resolution(cls, v):
        """处理空字符串的resolution字段"""
        if v == "" or v is None:
            return None
        return v

    def get_type_display(self) -> str:
        """获取类型的中文显示"""
        if not self.type:
            return "未指定"
        
        # 如果是字符串格式的枚举值，直接使用映射
        if isinstance(self.type, str):
            try:
                return BugType(self.type).__str__()
            except ValueError:
                return self.type
        elif isinstance(self.type, BugType):
            return str(self.type)
        else:
            return str(self.type)
    
    def get_severity_display(self) -> str:
        """获取严重程度的中文显示"""
        if isinstance(self.severity, BugSeverity):
            return str(self.severity)
        elif isinstance(self.severity, int):
            return BugSeverity(self.severity).__str__()
        return str(self.severity)
    
    def get_severity_display_with_emoji(self) -> str:
        """获取严重程度的带表情符号显示"""
        if isinstance(self.severity, BugSeverity):
            return self.severity.display_text
        elif isinstance(self.severity, int):
            return BugSeverity(self.severity).display_text
        return str(self.severity)
    
    def get_priority_display(self) -> str:
        """获取优先级的中文显示"""
        if isinstance(self.pri, BugPriority):
            return str(self.pri)
        elif isinstance(self.pri, int):
            return BugPriority(self.pri).__str__()
        return str(self.pri)
    
    def get_priority_display_with_emoji(self) -> str:
        """获取优先级的带表情符号显示"""
        if isinstance(self.pri, BugPriority):
            return self.pri.display_text
        elif isinstance(self.pri, int):
            return BugPriority(self.pri).display_text
        return str(self.pri)
    
    def get_status_display(self) -> str:
        """获取状态的中文显示"""
        if isinstance(self.status, BugStatus):
            return str(self.status)
        elif isinstance(self.status, str):
            try:
                return BugStatus(self.status).__str__()
            except ValueError:
                return self.status
        return str(self.status)
    
    def get_status_display_with_emoji(self) -> str:
        """获取状态的带表情符号显示"""
        if isinstance(self.status, BugStatus):
            return self.status.display_text
        elif isinstance(self.status, str):
            try:
                return BugStatus(self.status).display_text
            except ValueError:
                return str(self.status)
        return str(self.status)
    
    def get_resolution_display(self) -> str:
        """获取解决方案的中文显示"""
        if not self.resolution:
            return ""
        if isinstance(self.resolution, BugResolution):
            return str(self.resolution)
        elif isinstance(self.resolution, str):
            try:
                return BugResolution(self.resolution).__str__()
            except ValueError:
                return self.resolution
        return str(self.resolution)

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
            BugPriority.NONE: "无",
            BugPriority.HIGH: "高",
            BugPriority.NORMAL: "中", 
            BugPriority.LOW: "低",
            BugPriority.URGENT: "紧急"
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
            "已确认": self.status == BugStatus.ACTIVE and self.confirmed == "0",
            "已解决": self.status == BugStatus.ACTIVE and self.confirmed == "1",
            "已关闭": self.status == BugStatus.RESOLVED
        }


class BugListItem(BaseModel):
    """缺陷列表项（简化版）"""

    id: str = Field(description="缺陷ID")
    title: str = Field(description="缺陷标题")
    status: str | BugStatus | None = Field(default=None, description="缺陷状态")
    severity: int | str | None = Field(default=None, description="严重程度")
    pri: int | str | None = Field(default=None, description="优先级")
    assignedTo: str | None = Field(default=None, description="指派人")
    openedBy: str | None = Field(default="", description="创建人")
    openedDate: str | None = Field(default=None, description="创建时间")
    resolvedBy: str | None = Field(default="", description="解决者")
    resolution: str | None = Field(default=None, description="解决方案")


class BugListData(BaseModel):
    """缺陷列表数据结构"""

    bugs: List[BugListItem] = Field(description="缺陷列表")
    users: Dict[str, str] = Field(default_factory=dict, description="用户列表映射")
    pager: Dict[str, Any] | None = Field(default=None, description="分页信息")

    def get_bug_list(self) -> List[BugListItem]:
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
    
    def get_bug_list(self) -> List[BugListItem]:
        """获取缺陷列表"""
        bug_data = self.get_bug_data()
        return bug_data.get_bug_list()
    
    def get_bug_list_data(self) -> Dict[str, Any]:
        """获取原始缺陷列表数据（用于分页）"""
        import json
        return json.loads(self.data)


class BugDetailData(BaseModel):
    """缺陷详情数据结构（来自API的data字段）"""
    title: str = Field(description="页面标题")
    products: Dict[str, str] = Field(description="所有产品列表")
    productID: str = Field(description="当前产品ID")
    productName: str = Field(description="当前产品名称")
    branches: List[Any] = Field(description="分支信息")
    modulePath: List[Dict[str, Any]] = Field(description="模块路径")
    bugModule: Dict[str, Any] = Field(description="缺陷所属模块")
    bug: BugModel = Field(description="缺陷详细信息")
    branchName: str = Field(description="分支名称")
    users: Dict[str, str] = Field(description="用户列表，用户名到真实姓名的映射")
    actions: Dict[str, BugAction] = Field(description="操作历史")
    builds: Dict[str, str] = Field(description="版本构建列表")
    preAndNext: Dict[str, Any] = Field(description="前一个和后一个缺陷")
    pager: Optional[Any] = Field(default=None, description="分页信息")
    
    @staticmethod
    def _clean_html_content(html_content: str) -> str:
        """清理HTML内容，转换为纯文本格式
        
        Args:
            html_content: 包含HTML标签的文本内容
            
        Returns:
            清理后的纯文本内容
        """
        if not html_content:
            return ""
        
        import re
        cleaned_text = html_content
        
        # 处理段落标签
        cleaned_text = re.sub(r'<p[^>]*>', '\n', cleaned_text)
        cleaned_text = cleaned_text.replace("</p>", "\n")
        
        # 处理样式标签
        cleaned_text = re.sub(r'<span[^>]*>', '', cleaned_text)
        cleaned_text = cleaned_text.replace("</span>", "")
        
        # 处理换行标签
        cleaned_text = cleaned_text.replace("<br />", "\n").replace("<br>", "\n")
        
        # 移除其他常见的HTML标签
        cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)
        
        # 清理换行符
        cleaned_text = cleaned_text.replace("\r\n", "\n").replace("\r", "\n")
        
        # 移除HTML实体编码（基本的）
        cleaned_text = cleaned_text.replace("&lt;", "<").replace("&gt;", ">")
        cleaned_text = cleaned_text.replace("&amp;", "&").replace("&nbsp;", " ")
        
        return cleaned_text.strip()


class BugDetailResponse(BaseModel):
    """缺陷详情响应"""
    status: str = Field(description="响应状态")
    data: str = Field(description="JSON字符串格式的详情数据")
    md5: Optional[str] = Field(default=None, description="数据MD5校验")
    
    def get_bug_detail_data(self) -> BugDetailData:
        """解析data字段并返回BugDetailData对象"""
        import json
        parsed_data = json.loads(self.data)
        return BugDetailData.model_validate(parsed_data)
    
    def get_bug(self) -> BugModel:
        """获取缺陷详细信息"""
        detail_data = self.get_bug_detail_data()
        return detail_data.bug
    
    def get_users_mapping(self) -> Dict[str, str]:
        """获取用户名到真实姓名的映射"""
        detail_data = self.get_bug_detail_data()
        return detail_data.users
    
    def get_products_mapping(self) -> Dict[str, str]:
        """获取产品ID到产品名称的映射"""
        detail_data = self.get_bug_detail_data()
        return detail_data.products
    
    def get_builds_mapping(self) -> Dict[str, str]:
        """获取版本构建的映射"""
        detail_data = self.get_bug_detail_data()
        return detail_data.builds


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
