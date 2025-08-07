"""
禅道用户管理数据模型

本模块定义了禅道系统中用户相关的所有数据结构，包括：
- 用户基本信息模型

数据来源：
- 用户登录API：/user-login-{sessionid}.json
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from enum import Enum
from datetime import datetime

from .common import DataResponse, StringDataResponse


class UserRole(str, Enum):
    """用户角色枚举
    
    定义禅道系统中的标准用户角色。
    每个角色对应不同的权限级别和工作职责。
    
    Attributes:
        DEV: 开发人员，主要负责功能开发和bug修复
        QA: 测试人员，负责质量保证和测试工作
        PM: 项目经理，负责项目管理和进度控制
        PO: 产品负责人，负责产品规划和需求管理
        TOP: 高级管理人员，拥有系统管理权限
        ADMIN: 系统管理员（如果存在）
    """
    DEV = "dev"      # 开发人员
    QA = "qa"        # 测试人员
    PM = "pm"        # 项目经理
    PO = "po"        # 产品负责人
    TOP = "top"      # 高级管理人员
    ADMIN = "admin"  # 系统管理员


class UserGender(str, Enum):
    """用户性别枚举
    
    定义用户性别的标准值。
    
    Attributes:
        MALE: 男性
        FEMALE: 女性
        UNKNOWN: 未知或不愿透露
    """
    MALE = "m"
    FEMALE = "f"
    UNKNOWN = ""


class UserStatus(str, Enum):
    """用户状态枚举
    
    定义用户当前的活动状态。
    
    Attributes:
        ONLINE: 在线状态
        OFFLINE: 离线状态
        BUSY: 忙碌状态
        AWAY: 离开状态
    """
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    AWAY = "away"


class UserAccountStatus(str, Enum):
    """用户账号状态枚举
    
    定义用户账号的管理状态。
    
    Attributes:
        ACTIVE: 账号激活，可正常使用
        INACTIVE: 账号未激活
        LOCKED: 账号被锁定
        DELETED: 账号已删除
    """
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    DELETED = "deleted"


class UserRights(BaseModel):
    """用户权限结构模型
    
    定义用户在系统中的详细权限信息。
    禅道采用细粒度的权限控制，对不同模块和操作分别设置权限。
    
    Attributes:
        rights: 详细权限映射，格式为 {模块: {操作: 是否允许}}
        acls: 访问控制列表，定义特殊的访问控制规则
    
    Example:
        ```python
        user_rights = UserRights(
            rights={
                "project": {"create": True, "delete": False},
                "task": {"create": True, "edit": True, "delete": False}
            },
            acls={
                "products": [1, 2, 3],  # 可访问的产品ID列表
                "projects": [10, 11]    # 可访问的项目ID列表
            }
        )
        ```
    """
    rights: Dict[str, Dict[str, bool]] = Field(
        default_factory=dict,
        description="详细权限映射，结构为 {模块名: {操作名: 是否允许}}"
    )
    acls: Dict[str, Any] = Field(
        default_factory=dict,
        description="访问控制列表，定义特殊的访问控制规则"
    )
    
    def has_permission(self, module: str, action: str) -> bool:
        """检查用户是否有特定模块的特定操作权限
        
        Args:
            module: 模块名，如"project"、"task"、"bug"等
            action: 操作名，如"create"、"edit"、"delete"等
            
        Returns:
            bool: 如果有权限则返回True，否则返回False
        """
        return self.rights.get(module, {}).get(action, False)
    
    def get_accessible_items(self, item_type: str) -> List[int]:
        """获取用户可访问的特定类型项目列表
        
        Args:
            item_type: 项目类型，如"products"、"projects"等
            
        Returns:
            List[int]: 可访问的项目ID列表
        """
        items = self.acls.get(item_type, [])
        if isinstance(items, list):
            return [int(item) for item in items if str(item).isdigit()]
        return []


class UserView(BaseModel):
    """用户视图权限模型
    
    定义用户在不同视图中的访问权限。
    这个模型通常用于控制用户在前端界面中能看到哪些数据。
    
    Attributes:
        account: 用户账号
        products: 可访问的产品ID列表，通常以逗号分隔的字符串形式存储
        projects: 可访问的项目ID列表，通常以逗号分隔的字符串形式存储
    """
    account: str = Field(description="用户账号")
    products: str = Field(
        default="",
        description="可访问的产品ID列表，多个ID用逗号分隔"
    )
    projects: str = Field(
        default="",
        description="可访问的项目ID列表，多个ID用逗号分隔"
    )
    
    def get_product_ids(self) -> List[int]:
        """获取可访问的产品ID列表
        
        Returns:
            List[int]: 产品ID列表
        """
        if not self.products or self.products.strip() == "":
            return []
        return [int(pid.strip()) for pid in self.products.split(",") if pid.strip().isdigit()]
    
    def get_project_ids(self) -> List[int]:
        """获取可访问的项目ID列表
        
        Returns:
            List[int]: 项目ID列表
        """
        if not self.projects or self.projects.strip() == "":
            return []
        return [int(pid.strip()) for pid in self.projects.split(",") if pid.strip().isdigit()]


class UserModel(BaseModel):
    """用户信息完整模型
    
    定义用户在禅道系统中的完整信息结构。
    这个模型包含了用户的所有基本信息、权限信息和状态信息。
    
    主要用途：
    - 用户登录后的用户信息存储
    - 用户管理界面的数据展示
    - 权限检查和访问控制
    - 用户信息的API响应解析
    
    Example:
        ```python
        user = UserModel(
            id="1",
            account="admin",
            realname="管理员",
            role="admin",
            email="admin@example.com",
            dept="1",
            position="系统管理员"
        )
        ```
    """
    # 基本信息
    id: str = Field(description="用户ID，系统内唯一标识")
    account: str = Field(description="用户账号，登录用的用户名")
    realname: str = Field(description="真实姓名")
    role: UserRole = Field(description="用户角色")
    dept: str = Field(description="部门ID")
    
    # 个人信息
    nickname: Optional[str] = Field(default="", description="昵称")
    avatar: Optional[str] = Field(default="", description="头像")
    birthday: Optional[str] = Field(default="0000-00-00", description="生日")
    gender: UserGender = Field(description="性别")
    
    # 联系方式
    email: Optional[str] = Field(default="", description="邮箱")
    mobile: Optional[str] = Field(default="", description="手机")
    phone: Optional[str] = Field(default="", description="电话")
    address: Optional[str] = Field(default="", description="地址")
    zipcode: Optional[str] = Field(default="", description="邮编")
    
    # 社交账号
    skype: Optional[str] = Field(default="", description="Skype")
    qq: Optional[str] = Field(default="", description="QQ")
    yahoo: Optional[str] = Field(default="", description="Yahoo")
    gtalk: Optional[str] = Field(default="", description="GTalk")
    wangwang: Optional[str] = Field(default="", description="旺旺")
    weixin: Optional[str] = Field(default="", description="微信")
    dingding: Optional[str] = Field(default="", description="钉钉")
    slack: Optional[str] = Field(default="", description="Slack")
    whatsapp: Optional[str] = Field(default="", description="WhatsApp")
    
    # 开发相关
    commiter: Optional[str] = Field(default="", description="提交者")
    
    # 系统信息
    join: Optional[str] = Field(default="0000-00-00", description="加入日期")
    visits: str = Field(description="访问次数")
    ip: str = Field(description="最后登录IP")
    last: str = Field(description="最后登录时间")
    fails: str = Field(description="登录失败次数")
    locked: str = Field(description="锁定时间")
    ranzhi: Optional[str] = Field(default="", description="然之集成")
    
    # 积分系统
    score: str = Field(description="积分")
    scoreLevel: str = Field(description="积分等级")
    
    # 状态
    status: UserStatus = Field(description="在线状态")
    clientLang: str = Field(description="客户端语言")
    clientStatus: UserStatus = Field(description="客户端状态")
    lastTime: str = Field(description="最后活动时间戳")
    
    # 权限标识
    admin: bool = Field(description="是否为管理员")
    modifyPassword: bool = Field(description="是否需要修改密码")
    
    # 复杂权限结构
    rights: UserRights = Field(description="用户权限")
    groups: Dict[str, str] = Field(description="用户组")
    view: UserView = Field(description="视图权限")
    
    # 公司信息
    company: str = Field(description="公司名称")


class UserListData(BaseModel):
    """用户列表数据结构"""
    title: str = Field(description="页面标题")
    users: List[Dict[str, Any]] = Field(description="用户列表数组")
    searchForm: str = Field(description="搜索表单数据")
    deptTree: str = Field(description="部门树HTML")
    parentDepts: List[Any] = Field(description="父级部门")
    dept: Union[Dict[str, Any], bool] = Field(description="当前部门信息")
    orderBy: str = Field(description="排序方式")
    deptID: int = Field(description="部门ID")
    pager: Dict[str, Any] = Field(description="分页信息")
    param: str = Field(description="参数")
    type: str = Field(description="类型")


class UserListResponse(BaseModel):
    """用户列表响应"""
    status: str = Field(description="响应状态")
    data: str = Field(description="JSON字符串格式的用户数据")
    md5: Optional[str] = Field(default=None, description="数据MD5校验")
    
    def get_user_list_data(self) -> UserListData:
        """解析data字段并返回UserListData对象"""
        import json
        parsed_data = json.loads(self.data)
        return UserListData.model_validate(parsed_data)
    
    def get_users(self) -> List[Dict[str, Any]]:
        """获取用户列表"""
        user_data = self.get_user_list_data()
        return user_data.users
    
    def get_dept_info(self) -> Union[Dict[str, Any], bool]:
        """获取部门信息"""
        user_data = self.get_user_list_data()
        return user_data.dept


# 用于获取特定用户信息的响应
class UserDetailResponse(BaseModel):
    """用户详情响应"""
    status: str = Field(description="响应状态")
    user: UserModel = Field(description="用户详细信息")
