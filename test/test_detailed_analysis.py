# -*- coding=utf-8 -*-
#!/usr/bin/env python3
"""
详细数据分析脚本
分析项目、任务、缺陷的详细结构
"""

import json
import logging
import httpx
from typing import Dict, Any, List

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ZENTAO_HOST = httpx.Client(base_url="http://192.168.2.84/zentao/")

def setup_session() -> str:
    """建立会话并登录"""
    # 获取 SessionID
    resp = ZENTAO_HOST.get("/api-getSessionID.json")
    result = resp.json()
    data = json.loads(result["data"])
    session_id = data["sessionID"]
    
    # 用户登录
    params = {"account": "lianping", "password": "123456"}
    resp = ZENTAO_HOST.get(f"/user-login-{session_id}.json", params=params)
    
    return session_id

def analyze_detailed_structure():
    """分析详细的数据结构"""
    logger.info("建立会话...")
    session_id = setup_session()
    
    logger.info("=" * 60)
    logger.info("分析项目详细结构")
    logger.info("=" * 60)
    
    # 分析项目结构
    resp = ZENTAO_HOST.get("/my-project.json")
    result = resp.json()
    data = json.loads(result["data"])
    projects = data.get("projects", [])
    
    logger.info(f"项目总数: {len(projects)}")
    if projects:
        logger.info("第一个项目的详细结构:")
        first_project = projects[0]
        for key, value in first_project.items():
            logger.info(f"  - {key}: {type(value).__name__} = {value}")
    
    logger.info("=" * 60)
    logger.info("分析任务详细结构")
    logger.info("=" * 60)
    
    # 分析任务结构
    resp = ZENTAO_HOST.get("/my-task.json")
    result = resp.json()
    data = json.loads(result["data"])
    tasks = data.get("tasks", [])
    
    logger.info(f"任务总数: {len(tasks)}")
    if tasks:
        logger.info("第一个任务的详细结构:")
        first_task = tasks[0]
        for key, value in first_task.items():
            logger.info(f"  - {key}: {type(value).__name__} = {value}")
    
    logger.info("=" * 60)
    logger.info("分析缺陷详细结构")
    logger.info("=" * 60)
    
    # 分析缺陷结构
    resp = ZENTAO_HOST.get("/my-bug.json")
    result = resp.json()
    data = json.loads(result["data"])
    bugs = data.get("bugs", [])
    
    logger.info(f"缺陷总数: {len(bugs)}")
    if bugs:
        logger.info("第一个缺陷的详细结构:")
        first_bug = bugs[0]
        for key, value in first_bug.items():
            logger.info(f"  - {key}: {type(value).__name__} = {value}")

if __name__ == "__main__":
    analyze_detailed_structure()
