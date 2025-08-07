"""
基于 Semantic Kernel 的 MCP Server 实现

这是一个将禅道 API 封装为 MCP（Model Context Protocol）服务器的实现，
使用 Semantic Kernel 框架来提供 AI 助手与禅道系统的交互功能。

主要功能：
- 禅道会话管理（登录/登出）
- 用户信息管理
- 缺陷管理
- 任务管理
- 项目管理
"""
import os
import sys
import logging
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

from .client.zentao_client import ZenTaoClient
from .models.user import UserModel
from .models.bug import BugStatus, BugResolution
from .models.task import TaskStatus, TaskPriority
from .models.project import ProjectStatus
from .constants import *


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ZenTaoServerConfig(BaseModel):
    """禅道服务器配置"""
    base_url: str = Field(..., description="禅道服务器基础URL")
    timeout: float = Field(default=30.0, description="请求超时时间（秒）")


class ZenTaoMCPServer:
    """基于 Semantic Kernel 的禅道 MCP 服务器
    
    提供禅道系统的核心功能，包括：
    - 会话管理（登录/登出）
    - 用户信息管理 
    - 项目信息查询
    - 任务管理
    - 缺陷管理
    """
    
    def __init__(self, config: ZenTaoServerConfig):
        """初始化禅道 MCP 服务器
        
        Args:
            config: 禅道服务器配置
        """
        self.config = config
        self.client: Optional[ZenTaoClient] = None
        self.current_user: Optional[UserModel] = None
        
        # 初始化 Semantic Kernel
        self.kernel = Kernel()
        self._register_functions()
        
    def _register_functions(self) -> None:
        """注册所有可用的 kernel 函数"""
        # 会话管理函数
        self.kernel.add_function("zentao_session", self.login)
        self.kernel.add_function("zentao_session", self.logout)
        self.kernel.add_function("zentao_session", self.get_current_user)
        
        # 缺陷管理函数
        self.kernel.add_function("zentao_bugs", self.query_bug_list)
        self.kernel.add_function("zentao_bugs", self.query_bug_detail)
        
        # 任务管理函数
        self.kernel.add_function("zentao_tasks", self.query_task_list)
        self.kernel.add_function("zentao_tasks", self.query_task_detail)

        # # 项目管理函数
        # self.kernel.add_function("zentao_projects", self.query_project_list)
        # self.kernel.add_function("zentao_projects", self.query_project_detail)
        
    def _ensure_client(self) -> ZenTaoClient:
        """确保客户端已初始化"""
        if self.client is None:
            self.client = ZenTaoClient(
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )
        return self.client
        
    def _ensure_logged_in(self) -> None:
        """确保用户已登录"""
        if self.current_user is None:
            raise ValueError("请先登录禅道系统。请使用 login 函数进行登录。")
    
    # ===============================
    # 会话管理函数
    # ===============================
    
    @kernel_function(
        description="登录禅道系统",
        name="login"
    )
    def login(self, username: str, password: str) -> str:
        """登录禅道系统
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            登录结果信息
        """
        try:
            client = self._ensure_client()
            user = client.login(username, password)
            self.current_user = user
            
            logger.info(f"用户 {username} 登录成功")
            return f"登录成功！欢迎，{user.realname}（{user.account}）"
            
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return f"登录失败：{str(e)}"
    
    @kernel_function(
        description="登出禅道系统",
        name="logout"
    )
    def logout(self) -> str:
        """登出禅道系统
        
        Returns:
            登出结果信息
        """
        try:
            if self.client and self.current_user:
                self.client.logout()
                username = self.current_user.account
                self.current_user = None
                
                logger.info(f"用户 {username} 登出成功")
                return f"用户 {username} 已成功登出"
            else:
                return "当前没有用户登录"
                
        except Exception as e:
            logger.error(f"登出失败: {e}")
            return f"登出失败：{str(e)}"
    
    @kernel_function(
        description="获取当前登录用户信息",
        name="get_current_user"
    )
    def get_current_user(self) -> str:
        """获取当前登录用户信息
        
        Returns:
            当前用户信息的字符串表示
        """
        try:
            if self.current_user:
                user = self.current_user
                return f"当前用户：{user.realname}（{user.account}），邮箱：{user.email}，角色：{user.role}"
            else:
                return "当前没有用户登录"
                
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return f"获取用户信息失败：{str(e)}"
    
    # ===============================
    # 缺陷管理函数
    # ===============================
    
    @kernel_function(
        description="查询缺陷清单，默认获取所有分配给我的缺陷，支持按状态筛选和数量限制",
        name="query_bug_list"
    )
    def query_bug_list(
        self, 
        status: str = "all", 
        limit: int = 0,
        sort_order: str = "latest"
    ) -> str:
        """查询缺陷清单
        
        Args:
            status: 缺陷状态筛选
                   - "all": 所有状态（默认）
                   - "active": 激活状态
                   - "resolved": 已解决
                   - "closed": 已关闭
            limit: 返回数量限制，0表示获取全部（默认）
            sort_order: 排序方式
                       - "latest": 最新优先（默认）
                       - "oldest": 最旧优先
                       - "priority": 优先级排序
            
        Returns:
            缺陷清单的格式化字符串
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            # 根据状态参数确定查询参数
            status_param = None if status == "all" else status
            
            # 使用常量配置的排序映射
            sort_key = BUG_SORT_KEY_MAPPING.get(sort_order, "id_desc")
            
            # 获取缺陷列表
            if limit > 0:
                # 如果指定了数量限制，先获取一页数据
                bugs = client.bugs.get_my_bugs(
                    status=status_param,
                    page=1,
                    per_page=min(limit, MAX_SINGLE_PAGE_SIZE),  # 使用常量
                    sort_key=sort_key
                )
                bugs = bugs[:limit]  # 截取指定数量
            else:
                # 获取所有页面数据
                bugs = client.bugs.get_my_bugs_all_pages(
                    status=status_param,
                    per_page=DEFAULT_PAGE_SIZE,  # 使用常量
                    sort_key=sort_key,
                    max_pages=MAX_PAGES_LIMIT  # 使用常量
                )
            
            if not bugs:
                status_text = "所有状态" if status == "all" else f"状态为'{status}'"
                return f"未找到{status_text}的缺陷"
            
            # 格式化输出
            result = f"缺陷清单（共 {len(bugs)} 个）\n"
            result += SECTION_SEPARATOR + "\n"
            
            for i, bug in enumerate(bugs, 1):
                # 使用模型的显示方法
                result += f"🏷️ {i}. **[{bug.id}]**: {bug.title}\n"
                result += f"📅 创建时间: {bug.openedDate}\n"
                result += f"🎯 级别: {bug.get_severity_display()}\n"
                result += f"⭐ 优先级: {bug.get_priority_display_with_emoji()}\n"
                result += f"👤 指派给: {bug.assignedTo or '未指派'}\n"
                result += f"👨‍💻 解决: {bug.resolvedBy or ''}\n"
                result += f"🔧 方案: {bug.get_resolution_display()}\n"
                result += f" {ITEM_SEPARATOR}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"查询缺陷清单失败: {e}")
            return f"查询缺陷清单失败：{str(e)}"
    
    @kernel_function(
        description="查询指定缺陷的详细信息，包含基本信息、重现步骤、附件和历史记录",
        name="query_bug_detail"
    )
    def query_bug_detail(self, bug_id: int) -> str:
        """查询指定缺陷的详细信息
        
        Args:
            bug_id: 缺陷ID
            
        Returns:
            缺陷详细信息的格式化字符串
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            # 获取缺陷详细数据
            bug_detail_response = client.bugs.get_bug_detail(bug_id)
            
            if not bug_detail_response:
                return f"❌ 未找到ID为 {bug_id} 的缺陷"
            
            # 解析详细数据
            bug_detail_data = bug_detail_response.get_bug_detail_data()
            bug = bug_detail_data.bug
            
            # 构建详细信息，参考 BugDetailData.display_summary 的结构
            result = f"缺陷详细信息 - #{bug.id}\n"
            result += SECTION_SEPARATOR + "\n"
            result += f"📋 标题: {bug.title}\n\n"
            
            # ===============================
            # 基本信息部分
            # ===============================
            result += "## 📊 基本信息\n"
            result += SUBSECTION_SEPARATOR + "\n"
            
            # 使用模型的显示方法，避免重复维护映射
            status_text = bug.get_status_display_with_emoji()
            severity_text = bug.get_severity_display_with_emoji()
            priority_text = bug.get_priority_display_with_emoji()
            type_text = bug.get_type_display()
            resolution_text = bug.get_resolution_display()
            
            # 获取产品名称
            product_name = bug_detail_data.products.get(bug.product, f"产品ID-{bug.product}") if bug.product else "未指定"
            
            # 获取模块路径
            module_path = " > ".join([m.get("name", "") for m in bug_detail_data.modulePath if m.get("name")]) if bug_detail_data.modulePath else "未指定"
            
            # 用户名映射 - 统一的用户名获取逻辑
            def get_user_name(username: str) -> str:
                if not username:
                    return "未指定"
                return bug_detail_data.users.get(username, username)
            
            result += f"🏷️ 所属产品: {product_name}\n"
            result += f"📂 所属模块: {module_path}\n"
            result += f"📊 状态: {status_text}\n"
            result += f"🎯 严重程度: {severity_text}\n"
            result += f"⭐ 优先级: {priority_text}\n"
            result += f"🔧 Bug类型: {type_text}\n"
            if resolution_text:
                result += f"✅ 解决方案: {resolution_text}\n"
            result += f"👤 当前指派: {get_user_name(bug.assignedTo)}\n"
            result += f"👨‍💻 创建者: {get_user_name(bug.openedBy)}\n"
            result += f"📅 创建时间: {bug.openedDate or '未知'}\n"
            result += f"🔄 激活次数: {bug.activatedCount or 0}\n"
            result += f"✅ 确认状态: {'已确认' if bug.confirmed == '1' else '未确认'}\n"
            
            if bug.os:
                result += f"💻 操作系统: {bug.os}\n"
            if bug.assignedDate:
                result += f"⏰ 指派时间: {bug.assignedDate}\n"
                
            result += "\n"
            
            # ===============================
            # 重现步骤部分
            # ===============================
            result += "## 🔄 重现步骤\n"
            result += SUBSECTION_SEPARATOR + "\n"
            
            if bug.steps:
                import re
                html_content = bug.steps
                
                # 处理图片标签，转换为markdown格式，参考BugDetailData.display_summary的方式
                zentao_base_url = client.base_url
                
                # 先处理以/zentao/开头的相对路径图片
                html_content = re.sub(
                    r'<img[^>]*src="/zentao/([^"]*)"[^>]*>', 
                    f'![图片]({zentao_base_url}\\1)', 
                    html_content
                )
                
                # 使用BugDetailData的静态方法清理HTML内容
                from mcp_zentao.models.bug import BugDetailData
                cleaned_steps = BugDetailData._clean_html_content(html_content)
                
                # 分割为行并添加到输出
                for line in cleaned_steps.split("\n"):
                    line = line.strip()
                    if line:
                        result += f"{line}\n"
            else:
                result += "暂无重现步骤描述\n"
            result += "\n"
            
            # ===============================  
            # 附件部分
            # ===============================
            if bug.files:
                result += "## 📎 附件信息\n"
                result += SUBSECTION_SEPARATOR + "\n"
                
                zentao_base_url = client.base_url
                session_id = client.session_id or ""
                
                for file_id, file_info in bug.files.items():
                    title = file_info.get("title", "未知文件")
                    extension = file_info.get("extension", "").lower()
                    size = file_info.get("size", "0")
                    size_kb = round(int(size) / 1024, 2) if size.isdigit() else "未知"
                    
                    # 文件类型图标
                    file_icon = "🖼️" if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'] else "📄"
                    
                    # 构建下载链接
                    download_url = f"{zentao_base_url}file-download-{file_id}.html?zentaosid={session_id}"
                    
                    result += f"{file_icon} {title}\n"
                    result += f"   💾 大小: {size_kb}KB | 📎 格式: {extension.upper() or '未知'}\n"
                    result += f"   🔗 下载: {download_url}\n\n"
            
            # ===============================
            # 历史记录部分  
            # ===============================
            if bug_detail_data.actions:
                result += "## 📋 历史记录\n"
                result += SUBSECTION_SEPARATOR + "\n"
                
                # 按日期排序操作历史
                sorted_actions = sorted(
                    bug_detail_data.actions.items(), 
                    key=lambda x: x[1].date, 
                    reverse=True
                )
                
                # 只显示最近的几条记录，避免过长 - 使用常量
                recent_actions = sorted_actions[:MAX_HISTORY_RECORDS]
                
                for action_id, action in recent_actions:
                    date = action.date or '未知时间'
                    actor = get_user_name(action.actor)
                    comment = action.comment
                    
                    # 使用枚举的显示方法获取图标和中文显示
                    action_icon = action.action.emoji
                    action_display = str(action.action)
                    
                    result += f"{action_icon} {date} - {actor} {action_display}\n"
                    
                    # 显示历史变更
                    if action.history:
                        for change in action.history:
                            if change.field == "resolution":
                                result += f"   🔄 解决方案: {str(BugResolution(change.new))}\n"
                            if change.field == "resolvedDate":
                                result += f"   🔄 解决时间: {change.new}\n"
                            if change.field == "resolvedBy":
                                result += f"   🔄 解决人: {get_user_name(change.new)}\n"
                            if change.field == "assignedTo":
                                result += f"   🔄 任务指派: {get_user_name(change.old)} → {get_user_name(change.new)}\n"
                        result += "\n"
                    if comment:
                        # 清理评论中的HTML
                        clean_comment = re.sub(r'<[^>]+>', '', comment).strip()
                        if clean_comment:
                            result += f"   💭 {clean_comment}\n"
                    result += "\n"
                
                if len(sorted_actions) > MAX_HISTORY_RECORDS:
                    result += f"... 还有 {len(sorted_actions) - MAX_HISTORY_RECORDS} 条历史记录\n\n"
            
            return result
            
        except Exception as e:
            logger.error(f"查询缺陷详情失败: {e}")
            return f"查询缺陷详情失败：{str(e)}"
    
    # ===============================
    # 任务管理函数
    # ===============================
    
    @kernel_function(
        description="查询任务清单，默认获取所有分配给我的任务，支持按状态筛选和数量限制",
        name="query_task_list"
    )
    def query_task_list(
        self, 
        status: str = "all", 
        limit: int = 0,
        sort_order: str = "latest"
    ) -> str:
        """查询任务清单
        
        Args:
            status: 任务状态筛选
                   - "all": 所有状态（默认）
                   - "wait": 等待处理
                   - "doing": 进行中
                   - "done": 已完成
                   - "closed": 已关闭
            limit: 返回数量限制，0表示获取全部（默认）
            sort_order: 排序方式
                       - "latest": 最新优先（默认）
                       - "oldest": 最旧优先
                       - "deadline": 按截止时间排序
            
        Returns:
            任务清单的格式化字符串
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            # 根据状态参数确定查询参数
            status_param = None if status == "all" else status
            
            # 使用常量配置的排序映射
            sort_key = TASK_SORT_KEY_MAPPING.get(sort_order, "id_desc")
            
            # 获取任务列表
            if limit > 0:
                # 如果指定了数量限制，先获取一页数据
                tasks = client.tasks.get_my_tasks(
                    status=status_param,
                    page=1,
                    per_page=min(limit, MAX_SINGLE_PAGE_SIZE),  # 使用常量
                    sort_key=sort_key
                )
                tasks = tasks[:limit]  # 截取指定数量
            else:
                # 获取所有页面数据
                tasks = client.tasks.get_my_tasks_all_pages(
                    status=status_param,
                    per_page=DEFAULT_PAGE_SIZE,  # 使用常量
                    sort_key=sort_key,
                    max_pages=MAX_PAGES_LIMIT  # 使用常量
                )
            
            if not tasks:
                status_text = "所有状态" if status == "all" else f"状态为'{status}'"
                return f"未找到{status_text}的任务"
            
            # 格式化输出
            result = f"任务清单（共 {len(tasks)} 个）\n"
            result += SECTION_SEPARATOR + "\n"
            
            for i, task in enumerate(tasks, 1):
                # 使用模型的显示方法，避免硬编码映射
                status_text = task.get_status_display_with_emoji()
                pri_text = task.get_priority_display_with_emoji()
                
                result += f"{i:3d}. [{task.id:>6}] {task.name}\n"
                result += f"     状态: {status_text:<15} | 优先级: {pri_text:<15}\n"
                result += f"     项目: {task.project or '未指定':<20} | 指派给: {task.assignedTo or '未指派'}\n"
                
                # 工时信息
                estimate = f"{task.estimate}h" if task.estimate else "未估算"
                consumed = f"{task.consumed}h" if task.consumed else "0h"
                result += f"     预估: {estimate:<8} | 已用: {consumed:<8}"
                
                if task.deadline:
                    result += f" | 截止: {task.deadline}"
                result += "\n"
                result += f"     {ITEM_SEPARATOR}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"查询任务清单失败: {e}")
            return f"查询任务清单失败：{str(e)}"
    
    @kernel_function(
        description="查询指定任务的详细信息",
        name="query_task_detail"
    )
    def query_task_detail(self, task_id: int) -> str:
        """查询指定任务的详细信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务详细信息的格式化字符串
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            task = client.tasks.get_task_by_id(task_id)
            
            if not task:
                return f"❌ 未找到ID为 {task_id} 的任务"
            
            # 使用模型的显示方法，避免硬编码映射
            status_text = task.get_status_display_with_emoji()
            pri_text = task.get_priority_display_with_emoji()
            
            result = f"任务详细信息 - #{task.id}\n"
            result += SECTION_SEPARATOR + "\n"
            result += f"📋 任务名称: {task.name}\n"
            result += f"📊 状态: {status_text}\n"
            result += f"🎯 优先级: {pri_text}\n"
            result += f"🏗️ 所属项目: {task.project or '未指定'}\n"
            result += f"👤 指派给: {task.assignedTo or '未指派'}\n"
            result += f"👨‍💻 创建者: {task.openedBy or '未知'}\n"
            
            # 时间信息
            if task.openedDate:
                result += f"📅 创建时间: {task.openedDate}\n"
            if task.deadline:
                result += f"⏰ 截止时间: {task.deadline}\n"
            if task.finishedDate and task.finishedDate != "0000-00-00 00:00:00" and task.status in ["done", "closed"]:
                result += f"✅ 完成时间: {task.finishedDate}\n"
            
            # 工时信息
            result += f"\n⏱️ 工时信息:\n"
            result += f"   预估工时: {task.estimate or 0} 小时\n"
            result += f"   已用工时: {task.consumed or 0} 小时\n"
            
            try:
                estimate_hours = float(task.estimate or 0)
                consumed_hours = float(task.consumed or 0)
                if estimate_hours > 0:
                    remaining = max(0, estimate_hours - consumed_hours)
                    result += f"   剩余工时: {remaining} 小时\n"
                    progress = min(100, consumed_hours / estimate_hours * 100)
                    result += f"   完成进度: {progress:.1f}%\n"
            except (ValueError, TypeError):
                # 如果转换失败，跳过计算
                pass
                
            result += "\n📝 详细描述:\n"
            result += SUBSECTION_SEPARATOR + "\n"
            result += f"{task.desc or '无详细描述'}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"查询任务详情失败: {e}")
            return f"查询任务详情失败：{str(e)}"
    
    # ===============================
    # 项目管理函数
    # ===============================
    
    @kernel_function(
        description="查询我参与的项目清单，基础的项目信息概览",
        name="query_project_list"
    )
    def query_project_list(self, limit: int = 20) -> str:
        """查询我参与的项目清单
        
        Args:
            limit: 返回数量限制，默认20个项目
            
        Returns:
            项目清单的格式化字符串
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            projects = client.projects.get_my_projects(
                page=1,
                per_page=limit,
                sort_key="id_desc"
            )
            
            if not projects:
                return "📭 您当前没有参与任何项目"
            
            result = f"我参与的项目（共 {len(projects)} 个）\n"
            result += SECTION_SEPARATOR + "\n"
            
            for i, project in enumerate(projects, 1):
                # 使用模型的显示方法，避免硬编码映射
                status_text = project.get_status_display_with_emoji()
                
                result += f"{i:2d}. [{project.id:>4}] {project.name}\n"
                result += f"    状态: {status_text}\n"
                if project.begin and project.end:
                    result += f"    时间: {project.begin} ~ {project.end}\n"
                result += f"    {SUBSECTION_SEPARATOR}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"查询项目列表失败: {e}")
            return f"查询项目列表失败：{str(e)}"
    
    @kernel_function(
        description="查询指定项目的详细信息",
        name="query_project_detail"
    )
    def query_project_detail(self, project_id: int) -> str:
        """查询指定项目的详细信息
        
        Args:
            project_id: 项目ID
            
        Returns:
            项目详细信息的格式化字符串
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            project = client.projects.get_project_by_id(project_id)
            
            if not project:
                return f"❌ 未找到ID为 {project_id} 的项目"
            
            # 使用模型的显示方法，避免硬编码映射
            status_text = project.get_status_display_with_emoji()
            
            result = f"项目详细信息 - #{project.id}\n"
            result += SECTION_SEPARATOR + "\n"
            result += f"📋 项目名称: {project.name}\n"
            result += f"📊 状态: {status_text}\n"
            result += f"👨‍💼 项目经理: {project.PM or '未指定'}\n"
            
            if project.begin and project.end:
                result += f"📅 项目周期: {project.begin} ~ {project.end}\n"
            elif project.begin:
                result += f"📅 开始时间: {project.begin}\n"
                
            if hasattr(project, 'team') and project.team:
                result += f"👥 团队成员: {project.team}\n"
                
            result += "\n📝 项目描述:\n"
            result += SUBSECTION_SEPARATOR + "\n"
            result += f"{project.desc or '无项目描述'}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"查询项目详情失败: {e}")
            return f"查询项目详情失败：{str(e)}"
    
    def as_mcp_server(self, server_name: str = "zentao-mcp-server"):
        """将当前实例转换为 MCP 服务器
        
        Args:
            server_name: 服务器名称
            
        Returns:
            配置好的 MCP 服务器实例
        """
        return self.kernel.as_mcp_server(server_name=server_name)
    
    def close(self) -> None:
        """关闭客户端连接"""
        if self.client:
            self.client.close()
            self.client = None
        self.current_user = None


def create_server(base_url: str, timeout: float = 30.0) -> ZenTaoMCPServer:
    """创建禅道 MCP 服务器实例
    
    Args:
        base_url: 禅道服务器基础URL
        timeout: 请求超时时间
        
    Returns:
        配置好的禅道 MCP 服务器实例
    """
    config = ZenTaoServerConfig(base_url=base_url, timeout=timeout)
    return ZenTaoMCPServer(config)


def run(
    transport: Literal["sse", "stdio"] = "stdio", 
    port: Optional[int] = None,
    base_url: str = None,
    timeout: float = 30.0
) -> None:
    """运行禅道 MCP 服务器
    
    Args:
        transport: 传输协议，支持 "sse" 或 "stdio"
        port: SSE 服务器端口（仅在 transport="sse" 时使用）
        base_url: 禅道服务器基础URL，如果未提供则从环境变量ZENTAO_HOST读取
        timeout: 请求超时时间
        auto_login: 是否在启动时自动登录（从环境变量读取用户名密码）
    """
    # 加载环境变量
    load_dotenv()
    
    # 从环境变量获取配置
    if base_url is None:
        base_url = os.getenv("ZENTAO_HOST")
        if not base_url:
            logger.error("未提供base_url参数，且环境变量ZENTAO_HOST也未设置")
            raise ValueError("必须提供base_url参数或设置环境变量ZENTAO_HOST")
    
    # 创建禅道 MCP 服务器
    zentao_server = create_server(base_url=base_url, timeout=timeout)
    
    # 尝试自动登录
    username = os.getenv("ZENTAO_ACCOUNT")
    password = os.getenv("ZENTAO_PASSWORD")
    
    if username and password:
        try:
            login_result = zentao_server.login(username, password)
            logger.info(f"自动登录结果: {login_result}")
        except Exception as e:
            logger.warning(f"自动登录失败: {e}，服务器将正常启动但需要手动登录")
    else:
        logger.info("未找到登录凭据环境变量(ZENTAO_ACCOUNT/ZENTAO_PASSWORD)，跳过自动登录")
    
    mcp_server = zentao_server.as_mcp_server("zentao-mcp-server")
    
    logger.info(f"启动禅道 MCP 服务器，传输协议: {transport}")
    logger.info(f"禅道服务器地址: {base_url}")
    
    if transport == "sse" and port is not None:
        # SSE 服务器模式
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route
        from starlette.responses import JSONResponse
        # 创建 Starlette 应用
        async def get_info(request):
            return JSONResponse({
                "name": "mcp-zentao",
                "version": "1.0.0",
                "description": "禅道系统 MCP 服务器，提供缺陷管理、任务跟踪和项目管理功能"
            })

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
                await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())
        
        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/", get_info),
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        uvicorn.run(starlette_app, host="0.0.0.0", port=port)  # nosec
        
    elif transport == "stdio":
        # STDIO 服务器模式
        import anyio
        from mcp.server.stdio import stdio_server
        
        # 创建并运行 stdio 服务器
        async def handle_stdin():
            async with stdio_server() as (read_stream, write_stream):
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options()
                )
        
        logger.info("启动 STDIO 服务器")
        anyio.run(handle_stdin)
        
    else:
        raise ValueError(f"不支持的传输协议: {transport}")


def main() -> None:
    """主函数，解析命令行参数并启动服务器"""
    import argparse
    
    parser = argparse.ArgumentParser(description="禅道 MCP 服务器")
    parser.add_argument(
        "--transport", 
        type=str, 
        choices=["sse", "stdio"], 
        default="stdio",
        help="传输协议（默认: stdio）"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080,
        help="SSE 服务器端口（默认: 8080）"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        help="禅道服务器基础URL（如未提供将从环境变量ZENTAO_HOST读取）"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="请求超时时间（默认: 30.0秒）"
    )
    
    args = parser.parse_args()
    
    try:
        run(
            transport=args.transport,
            port=args.port if args.transport == "sse" else None,
            base_url=args.base_url,
            timeout=args.timeout
        )
    except KeyboardInterrupt:
        logger.info("服务器已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
