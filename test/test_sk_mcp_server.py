"""
测试 Semantic Kernel MCP Server 实现

本测试文件用于验证基于 Semantic Kernel 的禅道 MCP 服务器的核心功能。
"""

import os
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from mcp_zentao.sk_mcp_server import ZenTaoMCPServer, create_server, ZenTaoServerConfig
from mcp_zentao.models.user import UserModel
from mcp_zentao.models.bug import BugModel, BugDetailData, BugDetailResponse, BugStatus, BugSeverity, BugPriority, BugType
from mcp_zentao.models.task import TaskModel, TaskStatus, TaskPriority, TaskType
from mcp_zentao.models.project import ProjectModel

# 从环境变量或 .env 文件加载配置
def load_test_config():
    """加载测试配置"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # 如果没有 python-dotenv，继续使用环境变量
    
    return {
        'base_url': os.getenv('ZENTAO_HOST', 'http://192.168.2.84/zentao'),
        'account': os.getenv('ZENTAO_ACCOUNT', 'lianping'),
        'password': os.getenv('ZENTAO_PASSWORD', '123456')
    }

# 测试配置
TEST_CONFIG = load_test_config()


class TestZenTaoMCPServer:
    """测试禅道 MCP 服务器核心功能"""
    
    @pytest.fixture
    def server_config(self):
        """创建测试用的服务器配置"""
        return ZenTaoServerConfig(
            base_url=TEST_CONFIG['base_url'],
            timeout=30.0
        )
    
    @pytest.fixture
    def mcp_server(self, server_config):
        """创建测试用的 MCP 服务器实例"""
        return ZenTaoMCPServer(server_config)
    
    @pytest.fixture
    def mock_user(self):
        """创建测试用的用户模型"""
        from mcp_zentao.models.user import UserRole, UserGender, UserStatus, UserRights, UserView
        
        return UserModel(
            id="1",
            account="testuser",
            realname="测试用户",
            email="test@example.com",
            role=UserRole.DEV,
            dept="1",
            gender=UserGender.UNKNOWN,
            visits="10",
            ip="192.168.1.100",
            last="2023-08-05 10:00:00",
            fails="0",
            locked="0000-00-00 00:00:00",
            score="100",
            scoreLevel="1",  
            status=UserStatus.ONLINE,
            clientLang="zh-cn",
            clientStatus=UserStatus.ONLINE,
            lastTime="1691200000",
            admin=False,
            modifyPassword=False,
            rights=UserRights(),
            groups={},
            view=UserView(account="testuser"),
            company="测试公司"
        )
    
    def test_server_initialization(self, mcp_server, server_config):
        """测试服务器初始化"""
        assert mcp_server.config == server_config
        assert mcp_server.client is None
        assert mcp_server.current_user is None
        assert mcp_server.kernel is not None
    
    def test_create_server(self):
        """测试服务器创建函数"""
        server = create_server(
            base_url="http://test.com",
            timeout=60.0
        )
        assert isinstance(server, ZenTaoMCPServer)
        assert server.config.base_url == "http://test.com"
        assert server.config.timeout == 60.0
    
    def test_get_current_user_not_logged_in(self, mcp_server):
        """测试获取当前用户信息（未登录）"""
        result = mcp_server.get_current_user()
        assert "当前没有用户登录" in result
    
    def test_ensure_logged_in_failure(self, mcp_server):
        """测试未登录时访问需要登录的功能"""
        with pytest.raises(ValueError, match="请先登录禅道系统"):
            mcp_server._ensure_logged_in()
    
    def test_close(self, mcp_server, mock_user):
        """测试关闭客户端"""
        # 设置状态
        mcp_server.current_user = mock_user
        mcp_server.client = Mock()
        
        mcp_server.close()
        
        assert mcp_server.current_user is None
        assert mcp_server.client is None
    
    def test_as_mcp_server(self, mcp_server):
        """测试转换为 MCP 服务器"""
        mcp_server_instance = mcp_server.as_mcp_server("test-server")
        assert mcp_server_instance is not None
    
    @pytest.fixture
    def mock_bugs(self):
        """创建测试用的缺陷列表"""
        return [
            BugModel(
                # 基本标识
                id="1",
                product="1",
                branch="0",
                module="1",
                project="1",
                plan="0",
                
                # 需求关联
                story="0",
                storyVersion="1",
                task="0",
                toTask="0",
                toStory="0",
                
                # 缺陷基本信息
                title="测试缺陷1",
                severity=BugSeverity.NORMAL,
                pri=BugPriority.HIGH,
                type=BugType.CODEERROR,
                
                # 重现信息
                status=BugStatus.ACTIVE,
                confirmed="1",
                
                # 创建信息
                openedBy="admin",
                openedDate="2024-01-01 10:00:00",
                openedBuild="1",
                
                # 分配信息
                assignedTo="testuser",
                assignedDate="2024-01-01 10:30:00",
                
                # 解决信息
                resolvedDate="0000-00-00 00:00:00",
                
                # 关闭信息
                closedDate="0000-00-00 00:00:00",
                
                # 激活信息
                activatedDate="2024-01-01 11:00:00",
                activatedCount="1",
                
                # 编辑信息
                lastEditedBy="admin",
                lastEditedDate="2024-01-01 15:00:00",
                
                # 删除标识
                deleted="0",
                
                # 重复缺陷
                duplicateBug="0",
                linkBug="0",
                
                # 用例关联
                case="0",
                caseVersion="1",
                result="0"
            ),
            BugModel(
                # 基本标识
                id="2",
                product="1",
                branch="0",
                module="1",
                project="1",
                plan="0",
                
                # 需求关联
                story="0",
                storyVersion="1",
                task="0",
                toTask="0",
                toStory="0",
                
                # 缺陷基本信息
                title="测试缺陷2",
                severity=BugSeverity.NORMAL,
                pri=BugPriority.NORMAL,
                type=BugType.CODEERROR,
                
                # 重现信息
                status=BugStatus.RESOLVED,
                confirmed="1",
                
                # 创建信息
                openedBy="admin",
                openedDate="2024-01-02 10:00:00",
                openedBuild="1",
                
                # 分配信息
                assignedTo="testuser",
                assignedDate="2024-01-02 10:30:00",
                
                # 解决信息
                resolvedDate="2024-01-02 15:00:00",
                
                # 关闭信息
                closedDate="0000-00-00 00:00:00",
                
                # 激活信息
                activatedDate="0000-00-00 00:00:00",
                activatedCount="0",
                
                # 编辑信息
                lastEditedBy="admin",
                lastEditedDate="2024-01-02 15:00:00",
                
                # 删除标识
                deleted="0",
                
                # 重复缺陷
                duplicateBug="0",
                linkBug="0",
                
                # 用例关联
                case="0",
                caseVersion="1",
                result="0"
            )
        ]
    
    @pytest.fixture
    def mock_tasks(self):
        """创建测试用的任务列表"""
        return [
            TaskModel(
                # 基本标识
                id="1",
                parent="0",
                project="1",
                module="1",
                
                # 需求关联
                story="0",
                storyVersion="1",
                fromBug="0",
                
                # 任务基本信息
                name="测试任务1",
                type=TaskType.DEVEL,
                pri=TaskPriority.NORMAL,
                desc="这是一个测试任务的详细描述",
                
                # 工时信息
                estimate="8.0",
                consumed="3.0",
                left="5.0",
                
                # 时间信息
                estStarted="2024-01-01 09:00:00",
                realStarted="2024-01-01 09:30:00",
                
                # 状态信息
                status=TaskStatus.DOING,
                
                # 创建信息
                openedBy="admin",
                openedDate="2024-01-01 09:00:00",
                
                # 分配信息
                assignedTo="testuser",
                assignedDate="2024-01-01 09:30:00",
                
                # 完成信息
                finishedDate="0000-00-00 00:00:00",
                
                # 取消信息
                canceledDate="0000-00-00 00:00:00",
                
                # 关闭信息
                closedDate="0000-00-00 00:00:00",
                
                # 编辑信息
                lastEditedBy="admin",
                lastEditedDate="2024-01-01 12:00:00",
                
                # 删除标识
                deleted="0",
                
                # 项目关联信息
                projectID="1",
                projectName="测试项目",
                
                # 需求关联信息
                needConfirm=False,
                
                # 进度计算
                progress=37  # 3/8 * 100 ≈ 37%
            ),
            TaskModel(
                # 基本标识
                id="2",
                parent="0",
                project="1",
                module="1",
                
                # 需求关联
                story="0",
                storyVersion="1",
                fromBug="0",
                
                # 任务基本信息
                name="测试任务2",
                type=TaskType.TEST,
                pri=TaskPriority.HIGH,
                desc="这是另一个测试任务的详细描述",
                
                # 工时信息
                estimate="4.0",
                consumed="4.0",
                left="0.0",
                
                # 时间信息
                estStarted="2024-01-02 09:00:00",
                realStarted="2024-01-02 09:00:00",
                
                # 状态信息
                status=TaskStatus.DONE,
                
                # 创建信息
                openedBy="admin",
                openedDate="2024-01-02 09:00:00",
                
                # 分配信息
                assignedTo="testuser",
                assignedDate="2024-01-02 09:00:00",
                
                # 完成信息
                finishedDate="2024-01-02 17:00:00",
                
                # 取消信息
                canceledDate="0000-00-00 00:00:00",
                
                # 关闭信息
                closedDate="0000-00-00 00:00:00",
                
                # 编辑信息
                lastEditedBy="testuser",
                lastEditedDate="2024-01-02 17:00:00",
                
                # 删除标识
                deleted="0",
                
                # 项目关联信息
                projectID="1",
                projectName="测试项目",
                
                # 需求关联信息
                needConfirm=False,
                
                # 进度计算
                progress=100  # 完成
            )
        ]
    
    def test_server_initialization(self, mcp_server, server_config):
        """测试服务器初始化"""
        assert mcp_server.config == server_config
        assert mcp_server.client is None
        assert mcp_server.current_user is None
        assert mcp_server.kernel is not None
    
    def test_create_server(self):
        """测试服务器创建函数"""
        server = create_server(
            base_url="http://test.com",
            timeout=60.0
        )
        assert isinstance(server, ZenTaoMCPServer)
        assert server.config.base_url == "http://test.com"
        assert server.config.timeout == 60.0
    
    @patch('mcp_zentao.sk_mcp_server.ZenTaoClient')
    def test_login_success(self, mock_client_class, mcp_server, mock_user):
        """测试登录成功"""
        # 模拟客户端登录成功
        mock_client = Mock()
        mock_client.login.return_value = mock_user
        mock_client_class.return_value = mock_client
        
        result = mcp_server.login("testuser", "password")
        
        assert "登录成功" in result
        assert "测试用户" in result
        assert mcp_server.current_user == mock_user
        mock_client.login.assert_called_once_with("testuser", "password")
    
    @patch('mcp_zentao.sk_mcp_server.ZenTaoClient')
    def test_login_failure(self, mock_client_class, mcp_server):
        """测试登录失败"""
        # 模拟客户端登录失败
        mock_client = Mock()
        mock_client.login.side_effect = Exception("登录失败：用户名或密码错误")
        mock_client_class.return_value = mock_client
        
        result = mcp_server.login("testuser", "wrongpassword")
        
        assert "登录失败" in result
        assert mcp_server.current_user is None
    
    def test_logout_success(self, mcp_server, mock_user):
        """测试登出成功"""
        # 设置已登录状态
        mcp_server.current_user = mock_user
        mcp_server.client = Mock()
        
        result = mcp_server.logout()
        
        assert "已成功登出" in result
        assert mcp_server.current_user is None
        mcp_server.client.logout.assert_called_once()
    
    def test_logout_not_logged_in(self, mcp_server):
        """测试未登录状态下登出"""
        result = mcp_server.logout()
        assert "当前没有用户登录" in result
    
    def test_get_current_user_logged_in(self, mcp_server, mock_user):
        """测试获取当前用户信息（已登录）"""
        mcp_server.current_user = mock_user
        
        result = mcp_server.get_current_user()
        
        assert "当前用户：测试用户" in result
        assert "testuser" in result
        assert "test@example.com" in result
    
    def test_get_current_user_not_logged_in(self, mcp_server):
        """测试获取当前用户信息（未登录）"""
        result = mcp_server.get_current_user()
        assert "当前没有用户登录" in result
    
    @patch('mcp_zentao.sk_mcp_server.ZenTaoClient')
    def test_query_bug_list_all(self, mock_client_class, mcp_server, mock_user, mock_bugs):
        """测试查询所有缺陷列表"""
        # 设置已登录状态
        mcp_server.current_user = mock_user
        
        # 模拟客户端返回缺陷列表
        mock_client = Mock()
        mock_client.bugs.get_my_bugs_all_pages.return_value = mock_bugs
        mock_client_class.return_value = mock_client
        mcp_server.client = mock_client
        
        result = mcp_server.query_bug_list()
        
        assert "缺陷清单（共 2 个）" in result
        assert "测试缺陷1" in result
        assert "测试缺陷2" in result
        assert "🔴激活" in result
        assert "🟡已解决" in result
    
    @patch('mcp_zentao.sk_mcp_server.ZenTaoClient')
    def test_query_bug_list_with_limit(self, mock_client_class, mcp_server, mock_user, mock_bugs):
        """测试查询限定数量的缺陷列表"""
        # 设置已登录状态
        mcp_server.current_user = mock_user
        
        # 模拟客户端返回缺陷列表
        mock_client = Mock()
        mock_client.bugs.get_my_bugs.return_value = mock_bugs[:1]  # 只返回第一个
        mock_client_class.return_value = mock_client
        mcp_server.client = mock_client
        
        result = mcp_server.query_bug_list(limit=1)
        
        assert "缺陷清单（共 1 个）" in result
        assert "测试缺陷1" in result
        assert "测试缺陷2" not in result
    
    @patch('mcp_zentao.sk_mcp_server.ZenTaoClient')
    def test_query_bug_detail(self, mock_client_class, mcp_server, mock_user, mock_bugs):
        """测试查询缺陷详情"""
        # 设置已登录状态
        mcp_server.current_user = mock_user
        
        # 创建模拟的 BugDetailResponse
        from mcp_zentao.models.bug import BugDetailResponse, BugDetailData
        import json
        
        # 创建模拟的详情数据
        mock_detail_data = BugDetailData(
            title="缺陷详情页面",
            products={"1": "测试产品"},
            productID="1",
            productName="测试产品",
            branches=[],
            modulePath=[{"name": "测试模块", "id": "1"}],
            bugModule={"name": "测试模块"},
            bug=mock_bugs[0],  # 使用第一个bug
            branchName="主分支",
            users={"admin": "管理员", "testuser": "测试用户"},
            actions={},
            builds={"1": "版本1"},
            preAndNext={}
        )
        
        # 创建模拟的响应
        mock_response = Mock()
        mock_response.get_bug_detail_data.return_value = mock_detail_data
        
        # 模拟客户端
        mock_client = Mock()
        mock_client.bugs.get_bug_detail_by_id.return_value = mock_response
        mock_client_class.return_value = mock_client
        mcp_server.client = mock_client
        
        result = mcp_server.query_bug_detail(1)
        
        assert "缺陷详细信息 - #1" in result
        assert "测试缺陷1" in result
        assert "🔴激活" in result
        assert "⚡一般" in result
        assert "📝低" in result
        assert "暂无重现步骤描述" in result
    
    @patch('mcp_zentao.sk_mcp_server.ZenTaoClient')
    def test_query_task_list_all(self, mock_client_class, mcp_server, mock_user, mock_tasks):
        """测试查询所有任务列表"""
        # 设置已登录状态  
        mcp_server.current_user = mock_user
        
        # 模拟客户端返回任务列表
        mock_client = Mock()
        mock_client.tasks.get_my_tasks_all_pages.return_value = mock_tasks
        mock_client_class.return_value = mock_client
        mcp_server.client = mock_client
        
        result = mcp_server.query_task_list()
        
        assert "任务清单（共 2 个）" in result
        assert "测试任务1" in result
        assert "测试任务2" in result
        assert "🔄进行中" in result
        assert "✅已完成" in result
    
    @patch('mcp_zentao.sk_mcp_server.ZenTaoClient')
    def test_query_task_detail(self, mock_client_class, mcp_server, mock_user, mock_tasks):
        """测试查询任务详情"""
        # 设置已登录状态
        mcp_server.current_user = mock_user
        
        # 模拟客户端返回任务详情
        mock_client = Mock()
        mock_client.tasks.get_task_by_id.return_value = mock_tasks[0]
        mock_client_class.return_value = mock_client
        mcp_server.client = mock_client
        
        result = mcp_server.query_task_detail(1)
        
        assert "任务详细信息 - #1" in result
        assert "测试任务1" in result
        assert "🔄进行中" in result
        assert "🟡中优先级" in result
        assert "预估工时: 8.0 小时" in result
        assert "已用工时: 3.0 小时" in result
        assert "剩余工时: 5.0 小时" in result
    
    def test_ensure_logged_in_failure(self, mcp_server):
        """测试未登录时访问需要登录的功能"""
        with pytest.raises(ValueError, match="请先登录禅道系统"):
            mcp_server._ensure_logged_in()
    
    def test_close(self, mcp_server, mock_user):
        """测试关闭客户端"""
        # 设置状态
        mcp_server.current_user = mock_user
        mcp_server.client = Mock()
        
        mcp_server.close()
        
        assert mcp_server.current_user is None
        assert mcp_server.client is None
    
    def test_as_mcp_server(self, mcp_server):
        """测试转换为 MCP 服务器"""
        mcp_server_instance = mcp_server.as_mcp_server("test-server")
        assert mcp_server_instance is not None


class TestMCPServerIntegration:
    """集成测试，测试完整的 MCP 服务器流程"""
    
    @pytest.fixture
    def server(self):
        """创建集成测试用的服务器"""
        return create_server(
            base_url="http://test-zentao.com",
            timeout=30.0
        )
    
    @patch('mcp_zentao.sk_mcp_server.ZenTaoClient')
    def test_full_workflow(self, mock_client_class, server):
        """测试完整的工作流程：登录 -> 查询缺陷 -> 查询任务 -> 登出"""
        # 模拟客户端和数据
        mock_client = Mock()
        from mcp_zentao.models.user import UserRole, UserGender, UserStatus, UserRights, UserView
        
        mock_user = UserModel(
            id="1",
            account="testuser", 
            realname="测试用户",
            email="test@example.com",
            role=UserRole.DEV,
            dept="1",
            gender=UserGender.UNKNOWN,
            visits="10",
            ip="192.168.1.100",
            last="2023-08-05 10:00:00",
            fails="0",
            locked="0000-00-00 00:00:00",
            score="100",
            scoreLevel="1",
            status=UserStatus.ONLINE,
            clientLang="zh-cn",
            clientStatus=UserStatus.ONLINE,
            lastTime="1691200000",
            admin=False,
            modifyPassword=False,
            rights=UserRights(),
            groups={},
            view=UserView(account="testuser"),
            company="测试公司"
        )
        mock_bugs = [
            BugModel(
                # 基本标识
                id="1",
                product="1",
                branch="0",
                module="1",
                project="1",
                plan="0",
                
                # 需求关联
                story="0",
                storyVersion="1",
                task="0",
                toTask="0",
                toStory="0",
                
                # 缺陷基本信息
                title="集成测试缺陷",
                severity=BugSeverity.HIGH,
                pri=BugPriority.HIGH,
                type=BugType.CODEERROR,
                
                # 重现信息
                status=BugStatus.ACTIVE,
                confirmed="1",
                
                # 创建信息
                openedBy="admin",
                openedDate="2024-01-01 09:00:00",
                openedBuild="1",
                
                # 分配信息
                assignedTo="testuser",
                assignedDate="2024-01-01 09:30:00",
                
                # 解决信息
                resolvedDate="0000-00-00 00:00:00",
                
                # 关闭信息
                closedDate="0000-00-00 00:00:00",
                
                # 激活信息
                activatedDate="0000-00-00 00:00:00",
                activatedCount="0",
                
                # 编辑信息
                lastEditedBy="admin",
                lastEditedDate="2024-01-01 09:00:00",
                
                # 删除标识
                deleted="0",
                
                # 重复缺陷
                duplicateBug="0",
                linkBug="0",
                
                # 用例关联
                case="0",
                caseVersion="1",
                result="0"
            )
        ]
        mock_tasks = [
            TaskModel(
                # 基本标识
                id="1",
                parent="0",
                project="1",
                module="1",
                
                # 需求关联
                story="0",
                storyVersion="1",
                fromBug="0",
                
                # 任务基本信息
                name="集成测试任务",
                type=TaskType.DEVEL,
                pri=TaskPriority.HIGH,
                desc="集成测试任务描述",
                
                # 工时信息
                estimate="8.0",
                consumed="4.0",
                left="4.0",
                
                # 时间信息
                estStarted="2024-01-01 09:00:00",
                realStarted="2024-01-01 09:30:00",
                
                # 状态信息
                status=TaskStatus.DOING,
                
                # 创建信息
                openedBy="admin",
                openedDate="2024-01-01 09:00:00",
                
                # 分配信息
                assignedTo="testuser",
                assignedDate="2024-01-01 09:30:00",
                
                # 完成信息
                finishedDate="0000-00-00 00:00:00",
                
                # 取消信息
                canceledDate="0000-00-00 00:00:00",
                
                # 关闭信息
                closedDate="0000-00-00 00:00:00",
                
                # 编辑信息
                lastEditedBy="admin",
                lastEditedDate="2024-01-01 12:00:00",
                
                # 删除标识
                deleted="0",
                
                # 项目关联信息
                projectID="1",
                projectName="测试项目",
                
                # 需求关联信息
                needConfirm=False,
                
                # 进度计算
                progress=50  # 4/8 * 100 = 50%
            )
        ]
        
        mock_client.login.return_value = mock_user
        mock_client.bugs.get_my_bugs_all_pages.return_value = mock_bugs
        mock_client.tasks.get_my_tasks_all_pages.return_value = mock_tasks
        mock_client_class.return_value = mock_client
        
        # 1. 登录
        login_result = server.login("testuser", "password")
        assert "登录成功" in login_result
        
        # 2. 查询缺陷
        bug_result = server.query_bug_list()
        assert "集成测试缺陷" in bug_result
        
        # 3. 查询任务
        task_result = server.query_task_list()
        assert "集成测试任务" in task_result
        
        # 4. 登出
        logout_result = server.logout()
        assert "已成功登出" in logout_result
        
        # 清理
        server.close()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
