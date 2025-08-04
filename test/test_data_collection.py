# -*- coding=utf-8 -*-
#!/usr/bin/env python3
"""
数据收集测试脚本
用于收集禅道 API 的响应数据，为数据建模提供基础
"""

import os
import json
import logging
import httpx
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ZENTAO_HOST = httpx.Client(base_url="http://192.168.2.84/zentao/")

def collect_session_id_response() -> Dict[str, Any]:
    """收集获取SessionID的API响应数据"""
    logger.info("正在收集 SessionID API 响应数据...")
    
    resp = ZENTAO_HOST.get("/api-getSessionID.json")
    assert resp.status_code == 200
    
    result = resp.json()
    logger.info(f"SessionID API 响应结构:")
    logger.info(f"  - status: {result.get('status')}")
    logger.info(f"  - data 类型: {type(result.get('data'))}")
    
    # 解析 data 字段
    if "data" in result and isinstance(result["data"], str):
        data = json.loads(result["data"])
        logger.info(f"  - 解析后的 data 内容: {data}")
        logger.info(f"  - sessionID: {data.get('sessionID')}")
        return {"raw_response": result, "parsed_data": data}
    
    return {"raw_response": result}


def collect_user_login_response(session_id: str) -> Dict[str, Any]:
    """收集用户登录的API响应数据"""
    logger.info("正在收集用户登录 API 响应数据...")
    
    params = {
        "account": os.getenv("ZENTAO_ACCOUNT", "lianping"),
        "password": os.getenv("ZENTAO_PASSWORD", "123456"),
    }
    
    resp = ZENTAO_HOST.get(f"/user-login-{session_id}.json", params=params)
    assert resp.status_code == 200
    
    result = resp.json()
    logger.info(f"用户登录 API 响应结构:")
    logger.info(f"  - status: {result.get('status')}")
    logger.info(f"  - user 字段类型: {type(result.get('user'))}")
    
    # 分析用户信息结构
    if "user" in result:
        user = result["user"]
        logger.info(f"  - 用户信息字段:")
        for key, value in user.items():
            logger.info(f"    - {key}: {type(value).__name__} = {value}")
    
    return {"raw_response": result}


def collect_project_response() -> Dict[str, Any]:
    """收集项目列表的API响应数据"""
    logger.info("正在收集项目列表 API 响应数据...")
    
    resp = ZENTAO_HOST.get("/my-project.json")
    assert resp.status_code == 200
    
    result = resp.json()
    logger.info(f"项目列表 API 响应结构:")
    logger.info(f"  - status: {result.get('status')}")
    logger.info(f"  - data 类型: {type(result.get('data'))}")
    
    # 解析 data 字段
    if "data" in result and isinstance(result["data"], str):
        data = json.loads(result["data"])
        logger.info(f"  - 项目数据结构:")
        
        if "projects" in data:
            projects = data["projects"]
            logger.info(f"    - projects 类型: {type(projects)}")
            
            if isinstance(projects, list) and projects:
                # 分析第一个项目的结构
                first_project = projects[0]
                logger.info(f"    - 项目示例:")
                for key, value in first_project.items():
                    logger.info(f"      - {key}: {type(value).__name__} = {value}")
        
        return {"raw_response": result, "parsed_data": data}
    
    return {"raw_response": result}


def collect_task_response() -> Dict[str, Any]:
    """收集任务列表的API响应数据"""
    logger.info("正在收集任务列表 API 响应数据...")
    
    resp = ZENTAO_HOST.get("/my-task.json")
    assert resp.status_code == 200
    
    result = resp.json()
    logger.info(f"任务列表 API 响应结构:")
    logger.info(f"  - status: {result.get('status')}")
    logger.info(f"  - data 类型: {type(result.get('data'))}")
    
    # 解析 data 字段
    if "data" in result and isinstance(result["data"], str):
        data = json.loads(result["data"])
        logger.info(f"  - 任务数据结构:")
        
        if "tasks" in data:
            tasks = data["tasks"]
            logger.info(f"    - tasks 类型: {type(tasks)}")
            
            if isinstance(tasks, list) and tasks:
                # 分析第一个任务的结构
                first_task = tasks[0]
                logger.info(f"    - 任务示例:")
                for key, value in first_task.items():
                    logger.info(f"      - {key}: {type(value).__name__} = {value}")
        
        return {"raw_response": result, "parsed_data": data}
    
    return {"raw_response": result}


def collect_bug_response() -> Dict[str, Any]:
    """收集缺陷列表的API响应数据"""
    logger.info("正在收集缺陷列表 API 响应数据...")
    
    resp = ZENTAO_HOST.get("/my-bug.json")
    assert resp.status_code == 200
    
    result = resp.json()
    logger.info(f"缺陷列表 API 响应结构:")
    logger.info(f"  - status: {result.get('status')}")
    logger.info(f"  - data 类型: {type(result.get('data'))}")
    
    # 解析 data 字段
    if "data" in result and isinstance(result["data"], str):
        data = json.loads(result["data"])
        logger.info(f"  - 缺陷数据结构:")
        
        if "bugs" in data:
            bugs = data["bugs"]
            logger.info(f"    - bugs 类型: {type(bugs)}")
            
            if isinstance(bugs, list) and bugs:
                # 分析第一个缺陷的结构
                first_bug = bugs[0]
                logger.info(f"    - 缺陷示例:")
                for key, value in first_bug.items():
                    logger.info(f"      - {key}: {type(value).__name__} = {value}")
        
        return {"raw_response": result, "parsed_data": data}
    
    return {"raw_response": result}


def test_collect_all_api_data():
    """测试：收集所有API的响应数据"""
    logger.info("=" * 60)
    logger.info("开始收集禅道 API 响应数据")
    logger.info("=" * 60)
    
    # 1. 收集 SessionID 数据
    session_data = collect_session_id_response()
    session_id = session_data.get("parsed_data", {}).get("sessionID")
    
    if not session_id:
        logger.error("无法获取 SessionID，停止后续测试")
        return
    
    logger.info("")
    
    # 2. 收集用户登录数据
    login_data = collect_user_login_response(session_id)
    
    logger.info("")
    
    # 3. 收集项目数据
    project_data = collect_project_response()
    
    logger.info("")
    
    # 4. 收集任务数据
    task_data = collect_task_response()
    
    logger.info("")
    
    # 5. 收集缺陷数据
    bug_data = collect_bug_response()
    
    logger.info("=" * 60)
    logger.info("数据收集完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_collect_all_api_data()
