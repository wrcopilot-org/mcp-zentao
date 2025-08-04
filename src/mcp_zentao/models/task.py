"""
任务管理数据模型
定义禅道任务相关的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from collections import OrderedDict


class TaskType(str, Enum):
    """任务类型枚举"""
    DESIGN = "design"      # 设计
    DEVEL = "devel"        # 开发
    TEST = "test"          # 测试
    STUDY = "study"        # 研究
    DISCUSS = "discuss"    # 讨论
    UI = "ui"             # 界面
    AFFAIR = "affair"      # 事务
    MISC = "misc"         # 其他


class TaskStatus(str, Enum):
    """任务状态枚举"""
    WAIT = "wait"          # 未开始
    DOING = "doing"        # 进行中
    DONE = "done"          # 已完成
    PAUSE = "pause"        # 已暂停
    CANCEL = "cancel"      # 已取消
    CLOSED = "closed"      # 已关闭


class TaskPriority(int, Enum):
    """任务优先级枚举"""
    LOWEST = 0    # 最低
    LOW = 1       # 低
    NORMAL = 2    # 正常  
    HIGH = 3      # 高
    HIGHEST = 4   # 最高


class TaskModel(BaseModel):
    """任务信息模型"""
    # 基本标识
    id: str = Field(description="任务ID")
    parent: str = Field(description="父任务ID，0表示顶级任务")
    project: str = Field(description="所属项目ID")
    module: str = Field(description="所属模块ID")
    
    # 需求关联
    story: str = Field(description="关联需求ID")
    storyVersion: str = Field(description="需求版本")
    fromBug: str = Field(description="来源缺陷ID")
    
    # 任务基本信息
    name: str = Field(description="任务名称")
    type: TaskType = Field(description="任务类型")
    pri: TaskPriority = Field(description="优先级")
    desc: Optional[str] = Field(default="", description="任务描述")
    
    # 工时信息
    estimate: str = Field(description="预估工时")
    consumed: str = Field(description="已消耗工时")
    left: str = Field(description="剩余工时")
    
    # 时间信息
    deadline: Optional[str] = Field(default="", description="截止日期")
    estStarted: str = Field(description="预计开始时间")
    realStarted: str = Field(description="实际开始时间")
    
    # 状态信息
    status: TaskStatus = Field(description="任务状态")
    subStatus: Optional[str] = Field(default="", description="子状态")
    color: Optional[str] = Field(default="", description="颜色标识")
    
    # 邮件通知
    mailto: Optional[str] = Field(default=None, description="邮件通知列表")
    
    # 创建信息
    openedBy: str = Field(description="创建者")
    openedDate: str = Field(description="创建时间")
    
    # 分配信息
    assignedTo: str = Field(description="指派给")
    assignedDate: str = Field(description="指派时间")
    
    # 完成信息
    finishedBy: Optional[str] = Field(default="", description="完成者")
    finishedDate: str = Field(description="完成时间")
    finishedList: Optional[str] = Field(default="", description="完成列表")
    
    # 取消信息
    canceledBy: Optional[str] = Field(default="", description="取消者")
    canceledDate: str = Field(description="取消时间")
    
    # 关闭信息
    closedBy: Optional[str] = Field(default="", description="关闭者")
    closedDate: str = Field(description="关闭时间")
    closedReason: Optional[str] = Field(default="", description="关闭原因")
    
    # 编辑信息
    lastEditedBy: str = Field(description="最后编辑者")
    lastEditedDate: str = Field(description="最后编辑时间")
    
    # 删除标识
    deleted: str = Field(description="是否删除，0=未删除")
    
    # 项目关联信息
    projectID: str = Field(description="项目ID（冗余字段）")
    projectName: str = Field(description="项目名称")
    
    # 需求关联信息（可能为空）
    storyID: Optional[str] = Field(default=None, description="需求ID")
    storyTitle: Optional[str] = Field(default=None, description="需求标题")
    storyStatus: Optional[str] = Field(default=None, description="需求状态")
    latestStoryVersion: Optional[str] = Field(default=None, description="最新需求版本")
    needConfirm: bool = Field(description="是否需要确认")
    
    # 进度计算
    progress: int = Field(description="完成进度百分比")

    def __repr__(self) -> str:
        """简洁的字符串表示"""
        return f"Task({self.id}: {self.name} - {self.status.value})"

    def display_fields(self) -> OrderedDict[str, Any]:
        """返回与禅道界面字段匹配的有序字典"""
        return OrderedDict([
            ("ID", self.id),
            ("P", self.pri.value),  # P 很可能是 Priority 的缩写
            ("所属项目", self.projectName),
            ("任务名称", self.name),
            ("创建", self.openedBy),
            ("指派给", self.assignedTo),
            ("由谁完成", self.finishedBy or ""),
            ("预计", self.estimate),
            ("消耗", self.consumed),
            ("剩余", self.left),
            ("截止", self.deadline or ""),
            ("状态", self._get_status_display()),
        ])

    def _get_status_display(self) -> str:
        """获取状态的中文显示"""
        status_map = {
            TaskStatus.WAIT: "未开始",
            TaskStatus.DOING: "进行中", 
            TaskStatus.DONE: "已完成",
            TaskStatus.PAUSE: "已暂停",
            TaskStatus.CANCEL: "已取消",
            TaskStatus.CLOSED: "已关闭"
        }
        return status_map.get(self.status, self.status.value)

    def available_actions(self) -> Dict[str, bool]:
        """返回可用操作的状态"""
        return {
            "开始": self.status == TaskStatus.WAIT,
            "关闭": self.status in [TaskStatus.DOING, TaskStatus.PAUSE],
            "完成": self.status == TaskStatus.DOING
        }

    def display_summary(self) -> str:
        """格式化的展示摘要"""
        fields = self.display_fields()
        actions = self.available_actions()
        
        lines = []
        lines.append("=" * 50)
        lines.append(f"任务详情: {fields['任务名称']}")
        lines.append("=" * 50)
        
        # 基本信息
        for key, value in fields.items():
            lines.append(f"{key:8}: {value}")
        
        # 可用操作
        lines.append("\n可用操作:")
        for action, available in actions.items():
            status = "✓" if available else "✗"
            lines.append(f"  {status} {action}")
        
        return "\n".join(lines)


class TaskListData(BaseModel):
    """任务列表数据结构"""
    tasks: List[TaskModel] = Field(description="任务列表")


class TaskListResponse(BaseModel):
    """获取任务列表的API响应"""
    status: str = Field(description="响应状态")
    data: str = Field(description="JSON字符串格式的任务数据")
    
    def get_task_data(self) -> TaskListData:
        """解析data字段并返回TaskListData对象"""
        import json
        parsed_data = json.loads(self.data)
        return TaskListData.model_validate(parsed_data)


class TaskDetailResponse(BaseModel):
    """任务详情响应"""
    status: str = Field(description="响应状态")
    task: TaskModel = Field(description="任务详细信息")


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    project: str = Field(description="项目ID")
    name: str = Field(description="任务名称")
    type: TaskType = Field(description="任务类型")
    assignedTo: str = Field(description="指派给")
    estimate: Optional[str] = Field(default="0", description="预估工时")
    deadline: Optional[str] = Field(default="", description="截止日期")
    desc: Optional[str] = Field(default="", description="任务描述")
    pri: TaskPriority = Field(default=TaskPriority.NORMAL, description="优先级")
    story: Optional[str] = Field(default="0", description="关联需求ID")


class TaskEditRequest(BaseModel):
    """编辑任务请求"""
    name: Optional[str] = Field(default=None, description="任务名称")
    type: Optional[TaskType] = Field(default=None, description="任务类型")
    assignedTo: Optional[str] = Field(default=None, description="指派给")
    estimate: Optional[str] = Field(default=None, description="预估工时")
    deadline: Optional[str] = Field(default=None, description="截止日期")
    desc: Optional[str] = Field(default=None, description="任务描述")
    pri: Optional[TaskPriority] = Field(default=None, description="优先级")
    status: Optional[TaskStatus] = Field(default=None, description="任务状态")


class TaskFinishRequest(BaseModel):
    """完成任务请求"""
    consumed: str = Field(description="实际消耗工时")
    left: str = Field(default="0", description="剩余工时")
    comment: Optional[str] = Field(default="", description="完成备注")


class TaskAssignRequest(BaseModel):
    """任务指派请求"""
    assignedTo: str = Field(description="指派给")
    comment: Optional[str] = Field(default="", description="指派备注")
