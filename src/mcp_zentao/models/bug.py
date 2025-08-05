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
    
    # 文件附件（仅在详情响应中存在）
    files: Optional[Dict[str, Dict[str, Any]]] = Field(default=None, description="附件文件列表")
    
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
            "已确认": self.status == BugStatus.ACTIVE and self.confirmed == "0",
            "已解决": self.status == BugStatus.ACTIVE and self.confirmed == "1",
            "已关闭": self.status == BugStatus.RESOLVED
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
            lines.append(f"  {action} {status}")
        
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
    actions: Dict[str, Dict[str, Any]] = Field(description="操作历史")
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
    
    def display_summary(self, session_id: str, zentao_base_url: str = "http://192.168.2.84/zentao/") -> str:
        """生成markdown格式的Bug详情摘要"""
        # 获取用户真实姓名
        def get_user_name(username: str) -> str:
            return self.users.get(username, username) if username else ""
        
        lines = []
        
        # 标题
        lines.append(f"# Bug #{self.bug.id}: {self.bug.title}")
        lines.append("")
        
        # 基本信息
        lines.append("## 基本信息")
        lines.append("")
        
        # 获取产品名称
        product_name = self.products.get(self.bug.product, f"产品ID-{self.bug.product}")
        
        # 获取模块路径
        module_path = " > ".join([m.get("name", "") for m in self.modulePath if m.get("name")])
        
        # 基本信息表格
        lines.append("| 字段 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| 所属产品 | {product_name} |")
        lines.append(f"| 所属模块 | {module_path} |")
        lines.append(f"| Bug类型 | {self.bug._get_type_display()} |")
        lines.append(f"| 严重程度 | {self.bug._get_severity_display()} |")
        lines.append(f"| 优先级 | {self.bug._get_priority_display()} |")
        lines.append(f"| Bug状态 | {self.bug._get_status_display()} |")
        lines.append(f"| 激活次数 | {self.bug.activatedCount} |")
        lines.append(f"| 激活日期 | {self.bug.activatedDate if self.bug.activatedDate else '无'} |")
        lines.append(f"| 是否确认 | {'已确认' if self.bug.confirmed == '1' else '未确认'} |")
        lines.append(f"| 当前指派 | {get_user_name(self.bug.assignedTo)} |")
        lines.append(f"| 操作系统 | {self.bug.os if self.bug.os else '全部'} |")
        lines.append("")
        
        # 重现步骤
        lines.append("## 重现步骤")
        lines.append("")
        
        if self.bug.steps:
            import re
            # 处理图片标签，转换为markdown
            html_content = self.bug.steps

            # 先处理以/zentao/开头的相对路径图片
            html_content = re.sub(
                r'<img[^>]*src="/zentao/([^"]*)"[^>]*>', 
                f'![图片]({zentao_base_url}\\1)', 
                html_content
            )

            # 使用静态方法清理HTML内容
            cleaned_steps = self._clean_html_content(html_content)
            
            # 分割为行并添加到输出
            for line in cleaned_steps.split("\n"):
                line = line.strip()
                if line:
                    lines.append(line)
        else:
            lines.append("暂无重现步骤")
        
        lines.append("")
        
        # 附件
        if self.bug.files:
            lines.append("### 附件")
            lines.append("")
            for file_id, file_info in self.bug.files.items():
                title = file_info.get("title", "未知文件")
                size = file_info.get("size", "0")
                # 将字节转换为KB显示
                size_kb = round(int(size) / 1024, 2) if size.isdigit() else "未知"
                
                # 生成下载链接
                download_url = f"{zentao_base_url}file-download-{file_id}.html?zentaosid={session_id}"
                
                lines.append(f"- [{title} ({size_kb}K)]({download_url})")
            lines.append("")
        
        # 历史记录
        lines.append("## 历史记录")
        lines.append("")
        
        if self.actions:
            # 按日期排序操作历史
            sorted_actions = sorted(
                self.actions.items(), 
                key=lambda x: x[1].get("date", "")
            )
            
            for action_id, action in sorted_actions:
                date = action.get("date", "")
                actor = get_user_name(action.get("actor", ""))
                action_type = action.get("action", "")
                comment = action.get("comment", "")
                
                # 根据动作类型生成中文描述
                action_desc = {
                    "opened": "创建",
                    "commented": "添加备注",
                    "assigned": "指派给",
                    "resolved": "解决",
                    "closed": "关闭",
                    "activated": "激活",
                    "edited": "编辑",
                }.get(action_type, action_type)
                
                lines.append(f"**{date}** - **{actor}** {action_desc}")
                
                # 处理历史变更
                history = action.get("history", [])
                if history:
                    for change in history:
                        field = change.get("field", "")
                        old_val = change.get("old", "")
                        new_val = change.get("new", "")
                        
                        # 转换用户名为真实姓名
                        if field == "assignedTo":
                            old_val = get_user_name(old_val)
                            new_val = get_user_name(new_val)
                        
                        lines.append(f"  - {field}: {old_val} → {new_val}")
                
                # 添加备注内容
                if comment:
                    # 使用静态方法清理HTML内容
                    cleaned_comment = self._clean_html_content(comment)
                    
                    # 分割为行并添加到输出
                    for comment_line in cleaned_comment.split("\n"):
                        comment_line = comment_line.strip()
                        if comment_line:
                            lines.append(f"  > {comment_line}")
                
                lines.append("")
        else:
            lines.append("暂无历史记录")
        
        return "\n".join(lines)


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
