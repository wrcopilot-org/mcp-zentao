"""
用户管理数据模型
定义禅道用户相关的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    """用户角色枚举"""
    DEV = "dev"  # 开发人员
    QA = "qa"   # 测试人员
    PM = "pm"   # 项目经理
    PO = "po"   # 产品负责人
    TOP = "top" # 高级管理


class UserGender(str, Enum):
    """用户性别枚举"""
    MALE = "m"
    FEMALE = "f"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"


class UserRights(BaseModel):
    """用户权限结构"""
    rights: Dict[str, Dict[str, bool]] = Field(description="详细权限映射")
    acls: Dict[str, Any] = Field(description="访问控制列表")


class UserView(BaseModel):
    """用户视图权限"""
    account: str = Field(description="用户账号")
    products: str = Field(description="可访问的产品ID列表，逗号分隔")
    projects: str = Field(description="可访问的项目ID列表，逗号分隔")


class UserModel(BaseModel):
    """用户信息完整模型"""
    # 基本信息
    id: str = Field(description="用户ID")
    account: str = Field(description="用户账号")
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


class UserListResponse(BaseModel):
    """用户列表响应"""
    status: str = Field(description="响应状态")
    users: List[UserModel] = Field(description="用户列表")


# 用于获取特定用户信息的响应
class UserDetailResponse(BaseModel):
    """用户详情响应"""
    status: str = Field(description="响应状态")
    user: UserModel = Field(description="用户详细信息")
