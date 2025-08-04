# -*- coding=utf-8 -*-
#!/usr/bin/env python3
"""
数据模型验证测试
验证定义的Pydantic模型能正确解析禅道API响应数据
"""

import os
import json
import logging
import httpx
from typing import Dict, Any

# 导入我们定义的数据模型
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_zentao.models import (
    SessionResponse, SessionData,
    LoginResponse, UserModel,
    ProjectListResponse, ProjectListData,
    TaskListResponse, TaskListData,
    BugListResponse, BugListData
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ZENTAO_HOST = httpx.Client(base_url="http://192.168.2.84/zentao/")

def test_session_model():
    """测试会话模型"""
    logger.info("=" * 60)
    logger.info("测试会话管理数据模型")
    logger.info("=" * 60)
    
    # 获取SessionID API响应
    resp = ZENTAO_HOST.get("/api-getSessionID.json")
    raw_data = resp.json()
    
    try:
        # 验证SessionResponse模型
        session_response = SessionResponse.model_validate(raw_data)
        logger.info(f"✅ SessionResponse 模型验证成功")
        logger.info(f"   状态: {session_response.status}")
        
        # 验证SessionData模型
        session_data = session_response.get_session_data()
        logger.info(f"✅ SessionData 模型验证成功")
        logger.info(f"   会话ID: {session_data.sessionID}")
        logger.info(f"   会话名称: {session_data.sessionName}")
        logger.info(f"   随机数: {session_data.rand}")
        
        return session_data.sessionID
    except Exception as e:
        logger.error(f"❌ 会话模型验证失败: {e}")
        return None


def test_user_model(session_id: str):
    """测试用户模型"""
    logger.info("=" * 60)
    logger.info("测试用户管理数据模型")
    logger.info("=" * 60)
    
    # 用户登录API响应
    params = {
        "account": os.getenv("ZENTAO_ACCOUNT", "lianping"),
        "password": os.getenv("ZENTAO_PASSWORD", "123456"),
    }
    resp = ZENTAO_HOST.get(f"/user-login-{session_id}.json", params=params)
    raw_data = resp.json()
    
    try:
        # 这里我们需要单独验证user字段，因为LoginResponse中的user是dict
        user_data = raw_data["user"]
        user_model = UserModel.model_validate(user_data)
        logger.info(f"✅ UserModel 模型验证成功")
        logger.info(f"   用户ID: {user_model.id}")
        logger.info(f"   账号: {user_model.account}")
        logger.info(f"   真实姓名: {user_model.realname}")
        logger.info(f"   角色: {user_model.role}")
        logger.info(f"   公司: {user_model.company}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 用户模型验证失败: {e}")
        logger.error(f"   错误详情: {type(e).__name__}")
        return False


def test_project_model():
    """测试项目模型"""
    logger.info("=" * 60)
    logger.info("测试项目管理数据模型")
    logger.info("=" * 60)
    
    # 获取项目列表API响应
    resp = ZENTAO_HOST.get("/my-project.json")
    raw_data = resp.json()
    
    try:
        # 验证ProjectListResponse模型
        project_response = ProjectListResponse.model_validate(raw_data)
        logger.info(f"✅ ProjectListResponse 模型验证成功")
        
        # 验证ProjectListData模型
        project_data = project_response.get_project_data()
        logger.info(f"✅ ProjectListData 模型验证成功")
        logger.info(f"   项目数量: {len(project_data.projects)}")
        
        if project_data.projects:
            first_project = project_data.projects[0]
            logger.info(f"   第一个项目ID: {first_project.id}")
            logger.info(f"   项目名称: {first_project.name}")
            logger.info(f"   项目类型: {first_project.type}")
            logger.info(f"   项目状态: {first_project.status}")
        
        return True
    except Exception as e:
        logger.error(f"❌ 项目模型验证失败: {e}")
        logger.error(f"   错误详情: {type(e).__name__}")
        return False


def test_task_model():
    """测试任务模型"""
    logger.info("=" * 60)
    logger.info("测试任务管理数据模型")
    logger.info("=" * 60)
    
    # 获取任务列表API响应
    resp = ZENTAO_HOST.get("/my-task.json")
    raw_data = resp.json()
    
    try:
        # 验证TaskListResponse模型
        task_response = TaskListResponse.model_validate(raw_data)
        logger.info(f"✅ TaskListResponse 模型验证成功")
        
        # 验证TaskListData模型
        task_data = task_response.get_task_data()
        logger.info(f"✅ TaskListData 模型验证成功")
        logger.info(f"   任务数量: {len(task_data.tasks)}")
        
        if task_data.tasks:
            first_task = task_data.tasks[0]
            logger.info(f"   第一个任务ID: {first_task.id}")
            logger.info(f"   任务名称: {first_task.name}")
            logger.info(f"   任务类型: {first_task.type}")
            logger.info(f"   任务状态: {first_task.status}")
            logger.info(f"   任务进度: {first_task.progress}%")
        
        return True
    except Exception as e:
        logger.error(f"❌ 任务模型验证失败: {e}")
        logger.error(f"   错误详情: {type(e).__name__}")
        return False


def test_bug_model():
    """测试缺陷模型"""
    logger.info("=" * 60)
    logger.info("测试缺陷管理数据模型")
    logger.info("=" * 60)
    
    # 获取缺陷列表API响应
    resp = ZENTAO_HOST.get("/my-bug.json")
    raw_data = resp.json()
    
    try:
        # 验证BugListResponse模型
        bug_response = BugListResponse.model_validate(raw_data)
        logger.info(f"✅ BugListResponse 模型验证成功")
        
        # 验证BugListData模型
        bug_data = bug_response.get_bug_data()
        logger.info(f"✅ BugListData 模型验证成功")
        logger.info(f"   缺陷数量: {len(bug_data.bugs)}")
        
        if bug_data.bugs:
            first_bug = bug_data.bugs[0]
            logger.info(f"   第一个缺陷ID: {first_bug.id}")
            logger.info(f"   缺陷标题: {first_bug.title}")
            logger.info(f"   缺陷类型: {first_bug.type}")
            logger.info(f"   缺陷状态: {first_bug.status}")
        else:
            logger.info("   当前没有缺陷数据")
        
        return True
    except Exception as e:
        logger.error(f"❌ 缺陷模型验证失败: {e}")
        logger.error(f"   错误详情: {type(e).__name__}")
        return False


def main():
    """主测试函数"""
    logger.info("🚀 开始数据模型验证测试")
    logger.info("=" * 60)
    
    # 1. 测试会话模型
    session_id = test_session_model()
    if not session_id:
        logger.error("❌ 会话模型测试失败，终止后续测试")
        return
    
    # 2. 测试用户模型
    user_ok = test_user_model(session_id)
    
    # 3. 测试项目模型
    project_ok = test_project_model()
    
    # 4. 测试任务模型
    task_ok = test_task_model()
    
    # 5. 测试缺陷模型
    bug_ok = test_bug_model()
    
    # 总结
    logger.info("=" * 60)
    logger.info("测试结果总结")
    logger.info("=" * 60)
    logger.info(f"会话模型: {'✅ 通过' if session_id else '❌ 失败'}")
    logger.info(f"用户模型: {'✅ 通过' if user_ok else '❌ 失败'}")
    logger.info(f"项目模型: {'✅ 通过' if project_ok else '❌ 失败'}")
    logger.info(f"任务模型: {'✅ 通过' if task_ok else '❌ 失败'}")
    logger.info(f"缺陷模型: {'✅ 通过' if bug_ok else '❌ 失败'}")
    
    all_passed = all([session_id, user_ok, project_ok, task_ok, bug_ok])
    logger.info("=" * 60)
    logger.info(f"🎉 所有模型验证: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")


if __name__ == "__main__":
    main()
