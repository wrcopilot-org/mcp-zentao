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
import logging
from dataclasses import asdict, dataclass
from typing import Any, Optional

from pydantic import BaseModel, Field
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

from .client.zentao_client import ZenTaoClient
from .constants import (
    BUG_SORT_KEY_MAPPING,
    DEFAULT_PAGE_SIZE,
    MAX_PAGES_LIMIT,
    MAX_SINGLE_PAGE_SIZE,
    TASK_SORT_KEY_MAPPING,
)
from .models.user import UserModel


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ToolResult:
    """Structured tool result.

    Args:
        status: success or error.
        message: Optional message.
        data: Structured payload.
    """

    status: str
    message: str | None
    data: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dict."""

        result = asdict(self)
        return {key: value for key, value in result.items() if value is not None}


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

    def _ok(self, data: dict[str, Any], message: str | None = None) -> dict[str, Any]:
        """Return success result."""

        return ToolResult(status="success", message=message, data=data).to_dict()

    def _error(self, message: str) -> dict[str, Any]:
        """Return error result."""

        return ToolResult(status="error", message=message, data=None).to_dict()

    def _user_summary(self, user: UserModel) -> dict[str, Any]:
        """Extract user summary dict."""

        return {
            "account": user.account,
            "realname": user.realname,
            "email": user.email,
            "role": user.role,
        }

    def _status_text(self, status: str, entity: str) -> str:
        """Generate status description text."""

        return "所有状态" if status == "all" else f"状态为'{status}'"
    
    # ===============================
    # 会话管理函数
    # ===============================
    
    @kernel_function(
        description="登录禅道系统",
        name="login"
    )
    def login(self, username: str, password: str) -> dict[str, Any]:
        """登录禅道系统
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            登录结果
        """
        try:
            client = self._ensure_client()
            user = client.login(username, password)
            self.current_user = user
            
            logger.info(f"用户 {username} 登录成功")
            return self._ok({"user": self._user_summary(user)}, message="登录成功")
            
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return self._error(f"登录失败：{str(e)}")
    
    @kernel_function(
        description="登出禅道系统",
        name="logout"
    )
    def logout(self) -> dict[str, Any]:
        """登出禅道系统
        
        Returns:
            登出结果
        """
        try:
            if self.client and self.current_user:
                self.client.logout()
                username = self.current_user.account
                self.current_user = None
                
                logger.info(f"用户 {username} 登出成功")
                return self._ok({"account": username}, message="登出成功")
            return self._error("当前没有用户登录")
                
        except Exception as e:
            logger.error(f"登出失败: {e}")
            return self._error(f"登出失败：{str(e)}")
    
    @kernel_function(
        description="获取当前登录用户信息",
        name="get_current_user"
    )
    def get_current_user(self) -> dict[str, Any]:
        """获取当前登录用户信息
        
        Returns:
            当前用户信息
        """
        try:
            if self.current_user:
                return self._ok({"user": self._user_summary(self.current_user)})
            return self._error("当前没有用户登录")
                
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return self._error(f"获取用户信息失败：{str(e)}")
    
    # ===============================
    # 缺陷管理函数
    # ===============================
    
    @kernel_function(
        description="查询缺陷清单，默认获取所有分配给我的缺陷，支持按状态筛选和数量限制",
        name="query_bug_list"
    )
    def query_bug_list(
        self,
        limit: int = 0,
        status: str = "all",
        sort_order: str = "latest"
    ) -> dict[str, Any]:
        """查询缺陷清单
        
        Args:
            limit: 返回数量限制，0表示获取全部（默认）
            status: 缺陷状态筛选
                   - "all": 所有状态（默认）
                   - "active": 激活状态
                   - "resolved": 已解决
                   - "closed": 已关闭
            sort_order: 排序方式
                       - "latest": 最新优先（默认）
                       - "oldest": 最旧优先
                       - "priority": 优先级排序
            
        Returns:
            缺陷清单
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            # 根据状态参数确定查询参数
            status_param = None if status == "all" else status
            sort_key = BUG_SORT_KEY_MAPPING.get(sort_order, "id_desc")
            
            # 获取缺陷列表
            if limit > 0:
                # 如果指定了数量限制，先获取一页数据
                bugs = client.bugs.get_my_bugs(
                    status=status_param,
                    page=1,
                    per_page=min(limit, MAX_SINGLE_PAGE_SIZE),
                    sort_key=sort_key
                )
                bugs = bugs[:limit]  # 截取指定数量
            else:
                # 获取所有页面数据
                bugs = client.bugs.get_my_bugs_all_pages(
                    status=status_param,
                    per_page=DEFAULT_PAGE_SIZE,
                    sort_key=sort_key,
                    max_pages=MAX_PAGES_LIMIT
                )
            
            if not bugs:
                return self._ok(
                    {"items": [], "total": 0},
                    message=f"未找到{self._status_text(status, '缺陷')}的缺陷",
                )

            items = [
                {
                    "id": bug.id,
                    "title": bug.title,
                    "opened_date": bug.openedDate,
                    "severity": bug.severity,
                    "priority": bug.pri,
                    "status": bug.status,
                    "assigned_to": bug.assignedTo,
                    "resolved_by": bug.resolvedBy,
                    "resolution": bug.resolution,
                }
                for bug in bugs
            ]

            return self._ok(
                {
                    "items": items,
                    "total": len(items),
                    "page": 1,
                    "per_page": DEFAULT_PAGE_SIZE,
                }
            )
            
        except Exception as e:
            logger.error(f"查询缺陷清单失败: {e}")
            return self._error(f"查询缺陷清单失败：{str(e)}")
    
    @kernel_function(
        description="查询指定缺陷的详细信息，包含基本信息、重现步骤、附件和历史记录",
        name="query_bug_detail"
    )
    def query_bug_detail(self, bug_id: int) -> dict[str, Any]:
        """查询指定缺陷的详细信息
        
        Args:
            bug_id: 缺陷ID
            
        Returns:
            缺陷详细信息
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            # 获取缺陷详细数据
            bug_detail_response = client.bugs.get_bug_detail(bug_id)
            
            if not bug_detail_response:
                return self._error(f"未找到ID为 {bug_id} 的缺陷")
            
            # 解析详细数据
            bug_detail_data = bug_detail_response.get_bug_detail_data()
            bug = bug_detail_data.bug
            users = bug_detail_data.users

            def resolve_user(account: str | None) -> str | None:
                if not account:
                    return None
                return users.get(account, account)

            data = {
                "bug": {
                    "id": bug.id,
                    "title": bug.title,
                    "status": bug.status,
                    "severity": bug.severity,
                    "priority": bug.pri,
                    "type": bug.type,
                    "resolution": bug.resolution,
                    "assigned_to": resolve_user(bug.assignedTo),
                    "opened_by": resolve_user(bug.openedBy),
                    "opened_date": bug.openedDate,
                    "confirmed": bug.confirmed,
                },
                "product": {
                    "id": bug.product,
                    "name": bug_detail_data.products.get(
                        bug.product, f"产品ID-{bug.product}"
                    )
                    if bug.product
                    else None,
                },
                "module_path": [
                    module.get("name", "")
                    for module in bug_detail_data.modulePath
                    if module.get("name")
                ],
                "steps": bug.steps,
                "files": bug.files,
                "actions": [
                    {
                        "id": action_id,
                        "actor": resolve_user(action.actor),
                        "action": str(action.action),
                        "date": action.date,
                        "comment": action.comment,
                    }
                    for action_id, action in bug_detail_data.actions.items()
                ],
            }

            return self._ok(data)
            
        except Exception as e:
            logger.error(f"查询缺陷详情失败: {e}")
            return self._error(f"查询缺陷详情失败：{str(e)}")
    
    # ===============================
    # 任务管理函数
    # ===============================
    
    @kernel_function(
        description="查询任务清单，默认获取所有分配给我的任务，支持按状态筛选和数量限制",
        name="query_task_list"
    )
    def query_task_list(
        self,
        limit: int = 0,
        status: str = "all",
        sort_order: str = "latest"
    ) -> dict[str, Any]:
        """查询任务清单
        
        Args:
            limit: 返回数量限制，0表示获取全部（默认）
            status: 任务状态筛选
                   - "all": 所有状态（默认）
                   - "wait": 等待处理
                   - "doing": 进行中
                   - "done": 已完成
                   - "closed": 已关闭
            sort_order: 排序方式
                       - "latest": 最新优先（默认）
                       - "oldest": 最旧优先
                       - "deadline": 按截止时间排序
            
        Returns:
            任务清单
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            # 根据状态参数确定查询参数
            status_param = None if status == "all" else status
            sort_key = TASK_SORT_KEY_MAPPING.get(sort_order, "id_desc")
            
            # 获取任务列表
            if limit > 0:
                # 如果指定了数量限制，先获取一页数据
                tasks = client.tasks.get_my_tasks(
                    status=status_param,
                    page=1,
                    per_page=min(limit, MAX_SINGLE_PAGE_SIZE),
                    sort_key=sort_key
                )
                tasks = tasks[:limit]  # 截取指定数量
            else:
                # 获取所有页面数据
                tasks = client.tasks.get_my_tasks_all_pages(
                    status=status_param,
                    per_page=DEFAULT_PAGE_SIZE,
                    sort_key=sort_key,
                    max_pages=MAX_PAGES_LIMIT
                )
            
            if not tasks:
                return self._ok(
                    {"items": [], "total": 0},
                    message=f"未找到{self._status_text(status, '任务')}的任务",
                )

            items = [
                {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status,
                    "priority": task.pri,
                    "project": task.project,
                    "assigned_to": task.assignedTo,
                    "opened_by": task.openedBy,
                    "opened_date": task.openedDate,
                    "deadline": task.deadline,
                }
                for task in tasks
            ]

            return self._ok(
                {
                    "items": items,
                    "total": len(items),
                    "page": 1,
                    "per_page": DEFAULT_PAGE_SIZE,
                }
            )
            
        except Exception as e:
            logger.error(f"查询任务清单失败: {e}")
            return self._error(f"查询任务清单失败：{str(e)}")
    
    @kernel_function(
        description="查询指定任务的详细信息",
        name="query_task_detail"
    )
    def query_task_detail(self, task_id: int) -> dict[str, Any]:
        """查询指定任务的详细信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务详细信息
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            task = client.tasks.get_task_by_id(task_id)
            
            if not task:
                return self._error(f"未找到ID为 {task_id} 的任务")

            data = {
                "task": {
                    "id": task.id,
                    "name": task.name,
                    "status": task.status,
                    "priority": task.pri,
                    "project": task.project,
                    "assigned_to": task.assignedTo,
                    "opened_by": task.openedBy,
                    "opened_date": task.openedDate,
                    "deadline": task.deadline,
                    "finished_date": task.finishedDate,
                    "estimate": task.estimate,
                    "consumed": task.consumed,
                    "desc": task.desc,
                }
            }

            return self._ok(data)
            
        except Exception as e:
            logger.error(f"查询任务详情失败: {e}")
            return self._error(f"查询任务详情失败：{str(e)}")
    
    # ===============================
    # 项目管理函数
    # ===============================
    
    @kernel_function(
        description="查询我正在进行中的项目清单，基础的项目信息概览",
        name="query_project_list"
    )
    def query_project_list(
        self,
        limit: int = 20,
        status: str = "all",
        sort_order: str = "latest"
    ) -> str:
        """查询我正在进行中的项目清单
        
        Args:
            limit: 返回数量限制，默认20个项目
            status: 项目状态筛选
                   - "all": 所有状态（默认）
                   - "active": 激活状态
                   - "resolved": 已解决
                   - "closed": 已关闭
            sort_order: 排序方式
                   - "latest": 最新
                   - "oldest": 最旧
        Returns:
            项目清单信息
        """
        try:
            self._ensure_logged_in()
            client = self._ensure_client()
            
            raise NotImplementedError(f"📭 您当前没有参与任何项目")
            
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
            
            raise NotImplementedError(f"❌ 未找到ID为 {project_id} 的项目")
            
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
    transport: str = "stdio",
    port: int | None = None,
    base_url: str | None = None,
    timeout: float = 30.0,
) -> None:
    """运行禅道 MCP 服务器
    
    Args:
        transport: 传输协议，支持 "sse" 或 "stdio"
        port: SSE 服务器端口（仅在 transport="sse" 时使用）
        base_url: 禅道服务器基础URL，如果未提供则从环境变量ZENTAO_URL读取
        timeout: 请求超时时间
        auto_login: 是否在启动时自动登录（从环境变量读取用户名密码）
    """
    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv()
    
    # 从环境变量获取配置
    import os

    if base_url is None:
        base_url = os.getenv("ZENTAO_URL", '')
        if not base_url:
            logger.error("必须设置环境变量ZENTAO_URL")
            raise ValueError
    
    # 创建禅道 MCP 服务器
    zentao_server = create_server(base_url=base_url, timeout=timeout)
    
    # 尝试自动登录
    username = os.getenv("ZENTAO_ACCOUNT", '')
    password = os.getenv("ZENTAO_PASSWORD", '')
    
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
        help="禅道服务器基础URL（如未提供将从环境变量ZENTAO_URL读取）"
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
            timeout=args.timeout,
        )
    except KeyboardInterrupt:
        logger.info("服务器已停止")
        raise SystemExit(0)
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
