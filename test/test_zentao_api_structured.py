# -*- coding=utf-8 -*-
#!/usr/bin/env python3
"""
重构后的禅道 API 测试
使用结构化数据模型进行测试
"""

import os
import json
import logging
import httpx
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_zentao.models import (
    SessionResponse, SessionData, LoginRequest,
    UserModel, ProjectListResponse, TaskListResponse, BugListResponse
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ZENTAO_HOST = httpx.Client(base_url="http://192.168.2.84/zentao/")


def test_get_session_id_structured():
    """获取 SessionID - 使用结构化模型"""
    logger.info("获取 SessionID...")
    
    resp = ZENTAO_HOST.get("/api-getSessionID.json")
    assert resp.status_code == 200
    
    # 使用结构化模型解析响应
    session_response = SessionResponse.model_validate(resp.json())
    assert session_response.status.value == "success"
    
    # 获取解析后的会话数据
    session_data = session_response.get_session_data()
    assert session_data.sessionID
    
    logger.info(f"✅ 会话ID获取成功: {session_data.sessionID}")
    logger.info(f"   会话名称: {session_data.sessionName}")
    logger.info(f"   随机数: {session_data.rand}")
    
    return session_data.sessionID


def test_user_login_structured():
    """用户登录 - 使用结构化模型"""
    logger.info("用户登录...")
    
    # 先获取会话ID
    session_id = test_get_session_id_structured()
    
    # 构建登录请求参数
    login_params = LoginRequest(
        account=os.getenv("ZENTAO_ACCOUNT", "lianping"),
        password=os.getenv("ZENTAO_PASSWORD", "123456")
    )
    
    resp = ZENTAO_HOST.get(
        f"/user-login-{session_id}.json", 
        params=login_params.model_dump(exclude_none=True)
    )
    assert resp.status_code == 200
    
    result = resp.json()
    assert result["status"] == "success"
    assert "user" in result
    
    # 使用用户模型验证用户数据
    user = UserModel.model_validate(result["user"])
    
    logger.info(f"✅ 用户登录成功: {user.realname} ({user.account})")
    logger.info(f"   用户ID: {user.id}")
    logger.info(f"   角色: {user.role}")
    logger.info(f"   公司: {user.company}")
    logger.info(f"   部门: {user.dept}")
    
    return user


def test_get_projects_structured():
    """获取项目列表 - 使用结构化模型"""
    logger.info("获取项目列表...")
    
    # 确保已登录
    user = test_user_login_structured()
    
    resp = ZENTAO_HOST.get("/my-project.json")
    assert resp.status_code == 200
    
    # 使用结构化模型解析响应
    project_response = ProjectListResponse.model_validate(resp.json())
    assert project_response.status == "success"
    
    # 获取解析后的项目数据
    project_data = project_response.get_project_data()
    
    logger.info(f"✅ 项目列表获取成功，共 {len(project_data.projects)} 个项目")
    
    for i, project in enumerate(project_data.projects[:3]):  # 只显示前3个
        logger.info(f"   项目 {i+1}: {project.name} (ID: {project.id})")
        logger.info(f"      类型: {project.type}, 状态: {project.status}")
        logger.info(f"      开始: {project.begin}, 结束: {project.end}")
        logger.info(f"      角色: {project.role}")
    
    return project_data.projects


def test_get_tasks_structured():
    """获取任务列表 - 使用结构化模型"""
    logger.info("获取任务列表...")
    
    # 确保已登录
    user = test_user_login_structured()
    
    resp = ZENTAO_HOST.get("/my-task.json")
    assert resp.status_code == 200
    
    # 使用结构化模型解析响应
    task_response = TaskListResponse.model_validate(resp.json())
    assert task_response.status == "success"
    
    # 获取解析后的任务数据
    task_data = task_response.get_task_data()
    
    logger.info(f"✅ 任务列表获取成功，共 {len(task_data.tasks)} 个任务")
    
    for i, task in enumerate(task_data.tasks[:3]):  # 只显示前3个
        logger.info(f"   任务 {i+1}: {task.name} (ID: {task.id})")
        logger.info(f"      类型: {task.type}, 状态: {task.status}")
        logger.info(f"      项目: {task.projectName} (ID: {task.project})")
        logger.info(f"      进度: {task.progress}%")
        logger.info(f"      指派给: {task.assignedTo}")
    
    return task_data.tasks


def test_get_bugs_structured():
    """获取缺陷列表 - 使用结构化模型"""
    logger.info("获取缺陷列表...")
    
    # 确保已登录
    user = test_user_login_structured()
    
    resp = ZENTAO_HOST.get("/my-bug.json")
    assert resp.status_code == 200
    
    # 使用结构化模型解析响应
    bug_response = BugListResponse.model_validate(resp.json())
    assert bug_response.status == "success"
    
    # 获取解析后的缺陷数据
    bug_data = bug_response.get_bug_data()
    
    logger.info(f"✅ 缺陷列表获取成功，共 {len(bug_data.bugs)} 个缺陷")
    
    if bug_data.bugs:
        for i, bug in enumerate(bug_data.bugs[:3]):  # 只显示前3个
            logger.info(f"   缺陷 {i+1}: {bug.title} (ID: {bug.id})")
            logger.info(f"      类型: {bug.type}, 状态: {bug.status}")
            logger.info(f"      严重程度: {bug.severity}, 优先级: {bug.pri}")
    else:
        logger.info("   当前没有缺陷")
    
    return bug_data.bugs


def test_full_workflow():
    """完整工作流测试"""
    logger.info("=" * 60)
    logger.info("开始完整工作流测试")
    logger.info("=" * 60)
    
    try:
        # 1. 会话管理
        logger.info("\n📍 步骤 1: 会话管理")
        session_id = test_get_session_id_structured()
        
        # 2. 用户登录
        logger.info("\n📍 步骤 2: 用户登录")  
        user = test_user_login_structured()
        
        # 3. 获取项目
        logger.info("\n📍 步骤 3: 获取项目列表")
        projects = test_get_projects_structured()
        
        # 4. 获取任务
        logger.info("\n📍 步骤 4: 获取任务列表")
        tasks = test_get_tasks_structured()
        
        # 5. 获取缺陷
        logger.info("\n📍 步骤 5: 获取缺陷列表")
        bugs = test_get_bugs_structured()
        
        # 总结
        logger.info("\n" + "=" * 60)
        logger.info("🎉 完整工作流测试成功!")
        logger.info(f"   用户: {user.realname} ({user.account})")
        logger.info(f"   项目数: {len(projects)}")
        logger.info(f"   任务数: {len(tasks)}")
        logger.info(f"   缺陷数: {len(bugs)}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 工作流测试失败: {e}")
        return False


if __name__ == "__main__":
    test_full_workflow()
