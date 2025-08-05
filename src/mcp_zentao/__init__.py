"""
MCP-ZenTao: 禅道系统的 Model Context Protocol 服务器

这个包提供了将禅道项目管理系统与 AI 助手集成的 MCP 服务器实现。
通过 Semantic Kernel 框架，AI 助手可以直接与禅道系统交互，
实现智能化的项目管理协作。

主要功能:
- 会话管理（登录/登出）
- 用户信息管理
- 项目信息查询
- 任务管理
- 缺陷管理

使用方式:
    # 作为 MCP 服务器运行
    python -m mcp_zentao.sk_mcp_server
    
    # 或者直接调用
    mcp-zentao --base-url http://your-zentao-server.com
"""

from .sk_mcp_server import main, create_server, run, ZenTaoMCPServer
from .client.zentao_client import ZenTaoClient

__version__ = "0.1.0"
__author__ = "nblog"

__all__ = [
    "main",
    "create_server", 
    "run",
    "ZenTaoMCPServer",
    "ZenTaoClient"
]