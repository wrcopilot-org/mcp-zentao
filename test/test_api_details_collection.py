# -*- coding=utf-8 -*-
#!/usr/bin/env python3
"""
禅道API详情收集测试

根据task-checklist.md中的"待收集的API信息"，
逐一收集并分析各个API端点的详细响应结构。
"""

import os
import json
import logging
import httpx
import pytest
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 禅道客户端配置
ZENTAO_HOST = httpx.Client(base_url="http://192.168.2.84/zentao/")


class APICollector:
    """API响应数据收集器
    
    用于收集和分析禅道API的响应数据，
    为后续的数据模型设计提供依据。
    """
    
    def __init__(self):
        self.session_id: Optional[str] = None
        self.user_info: Optional[Dict[str, Any]] = None
        self.collected_data: Dict[str, Any] = {}
    
    def ensure_login(self) -> Dict[str, Any]:
        """确保已登录，返回用户信息"""
        if self.user_info is None:
            self.session_id = self._get_session_id()
            self.user_info = self._login_with_session()
        return self.user_info
    
    def _get_session_id(self) -> str:
        """获取会话ID"""
        resp = ZENTAO_HOST.get("/api-getSessionID.json")
        assert resp.status_code == 200
        result = resp.json()
        assert result["status"] == "success"
        assert "data" in result
        data = json.loads(result["data"])
        assert "sessionID" in data
        logger.info(f"获取会话ID成功: {data['sessionID']}")
        return data["sessionID"]
    
    def _login_with_session(self) -> Dict[str, Any]:
        """使用会话ID登录"""
        params = {
            "account": os.getenv("ZENTAO_ACCOUNT", "lianping"),
            "password": os.getenv("ZENTAO_PASSWORD", "123456"),
        }
        resp = ZENTAO_HOST.get(f"/user-login-{self.session_id}.json", params=params)
        assert resp.status_code == 200
        result = resp.json()
        assert result["status"] == "success"
        assert "user" in result
        logger.info(f"用户登录成功: {result['user']['realname']}")
        return result["user"]
    
    def collect_and_save(self, endpoint: str, data: Dict[str, Any], filename: str = None):
        """收集并保存API响应数据"""
        self.collected_data[endpoint] = data
        
        # 保存到文件（可选）
        if filename:
            output_dir = "test_outputs"
            os.makedirs(output_dir, exist_ok=True)
            with open(f"{output_dir}/{filename}.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已保存到: {output_dir}/{filename}.json")


# 全局收集器实例
collector = APICollector()


class TestUserLogout:
    """测试用户登出API"""
    
    def test_user_logout(self):
        """收集用户登出的API响应
        
        API: GET /user-logout.json
        目的: 了解登出响应结构
        """
        # 确保已登录
        collector.ensure_login()
        
        # 执行登出请求
        resp = ZENTAO_HOST.get("/user-logout.json")
        assert resp.status_code == 200
        
        result = resp.json()
        logger.info(f"登出响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 收集数据
        collector.collect_and_save("/user-logout.json", result, "user_logout_response")
        
        # 基本断言
        assert "status" in result
        
        # 重新登录以供后续测试使用
        collector.session_id = None
        collector.user_info = None
        collector.ensure_login()


class TestBugDetails:
    """测试缺陷详情API"""
    
    def test_get_bug_list_for_ids(self):
        """先获取缺陷列表，提取ID用于详情查询"""
        collector.ensure_login()
        
        # 获取我的缺陷列表
        resp = ZENTAO_HOST.get("/my-bug.json")
        assert resp.status_code == 200
        
        result = resp.json()
        assert result["status"] == "success"
        assert "data" in result
        
        data = json.loads(result["data"])
        assert "bugs" in data
        
        bugs = data["bugs"]
        if bugs:
            # 存储前几个缺陷ID用于详情测试（bugs是列表）
            bug_ids = [str(bug["id"]) for bug in bugs[:3]]
            logger.info(f"找到缺陷ID: {bug_ids}")
            # 存储到收集器中而不是返回
            collector.collected_data["bug_ids"] = bug_ids
        else:
            logger.warning("没有找到缺陷数据")
            collector.collected_data["bug_ids"] = []
    
    def test_bug_view_details(self):
        """收集缺陷详情的API响应
        
        API: GET /bug-view-{id}.json
        目的: 了解缺陷详情的完整数据结构
        """
        # 先调用获取ID的测试以确保数据已收集
        self.test_get_bug_list_for_ids()
        bug_ids = collector.collected_data.get("bug_ids", [])
        
        if not bug_ids:
            pytest.skip("没有可用的缺陷ID进行测试")
        
        for bug_id in bug_ids:
            resp = ZENTAO_HOST.get(f"/bug-view-{bug_id}.json")
            
            if resp.status_code == 200:
                result = resp.json()
                logger.info(f"缺陷 {bug_id} 详情响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 收集数据
                collector.collect_and_save(
                    f"/bug-view-{bug_id}.json", 
                    result, 
                    f"bug_view_{bug_id}_response"
                )
                
                # 基本断言
                assert "status" in result
                if result["status"] == "success":
                    assert "data" in result
                    break  # 成功收集一个就够了
            else:
                logger.warning(f"获取缺陷 {bug_id} 详情失败: {resp.status_code}")


class TestTaskDetails:
    """测试任务详情API"""
    
    def test_get_task_list_for_ids(self):
        """先获取任务列表，提取ID用于详情查询"""
        collector.ensure_login()
        
        # 获取我的任务列表
        resp = ZENTAO_HOST.get("/my-task.json")
        assert resp.status_code == 200
        
        result = resp.json()
        assert result["status"] == "success"
        assert "data" in result
        
        data = json.loads(result["data"])
        assert "tasks" in data
        
        tasks = data["tasks"]
        if tasks:
            # 存储前几个任务ID用于详情测试（tasks是列表）
            task_ids = [str(task["id"]) for task in tasks[:3]]
            logger.info(f"找到任务ID: {task_ids}")
            # 存储到收集器中而不是返回
            collector.collected_data["task_ids"] = task_ids
        else:
            logger.warning("没有找到任务数据")
            collector.collected_data["task_ids"] = []
    
    def test_task_view_details(self):
        """收集任务详情的API响应
        
        API: GET /task-view-{id}.json
        目的: 了解任务详情的完整数据结构
        """
        # 先调用获取ID的测试以确保数据已收集
        self.test_get_task_list_for_ids()
        task_ids = collector.collected_data.get("task_ids", [])
        
        if not task_ids:
            pytest.skip("没有可用的任务ID进行测试")
        
        for task_id in task_ids:
            resp = ZENTAO_HOST.get(f"/task-view-{task_id}.json")
            
            if resp.status_code == 200:
                result = resp.json()
                logger.info(f"任务 {task_id} 详情响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 收集数据
                collector.collect_and_save(
                    f"/task-view-{task_id}.json", 
                    result, 
                    f"task_view_{task_id}_response"
                )
                
                # 基本断言
                assert "status" in result
                if result["status"] == "success":
                    assert "data" in result
                    break  # 成功收集一个就够了
            else:
                logger.warning(f"获取任务 {task_id} 详情失败: {resp.status_code}")


class TestProjectDetails:
    """测试项目详情API"""
    
    def test_get_project_list_for_ids(self):
        """先获取项目列表，提取ID用于详情查询"""
        collector.ensure_login()
        
        # 获取我的项目列表
        resp = ZENTAO_HOST.get("/my-project.json")
        assert resp.status_code == 200
        
        result = resp.json()
        assert result["status"] == "success"
        assert "data" in result
        
        data = json.loads(result["data"])
        assert "projects" in data
        
        projects = data["projects"]
        if projects:
            # 存储前几个项目ID用于详情测试（projects是列表）
            project_ids = [str(project["id"]) for project in projects[:3]]
            logger.info(f"找到项目ID: {project_ids}")
            # 存储到收集器中而不是返回
            collector.collected_data["project_ids"] = project_ids
        else:
            logger.warning("没有找到项目数据")
            collector.collected_data["project_ids"] = []
    
    def test_project_task_details(self):
        """收集项目任务的API响应
        
        API: GET /project-task-{id}.json
        目的: 了解项目任务的完整数据结构
        """
        # 先调用获取ID的测试以确保数据已收集
        self.test_get_project_list_for_ids()
        project_ids = collector.collected_data.get("project_ids", [])
        
        if not project_ids:
            pytest.skip("没有可用的项目ID进行测试")
        
        for project_id in project_ids:
            resp = ZENTAO_HOST.get(f"/project-task-{project_id}.json")
            
            if resp.status_code == 200:
                result = resp.json()
                logger.info(f"项目 {project_id} 任务响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 收集数据
                collector.collect_and_save(
                    f"/project-task-{project_id}.json", 
                    result, 
                    f"project_task_{project_id}_response"
                )
                
                # 基本断言
                assert "status" in result
                if result["status"] == "success":
                    assert "data" in result
                    break  # 成功收集一个就够了
            else:
                logger.warning(f"获取项目 {project_id} 任务失败: {resp.status_code}")


class TestCollectionSummary:
    """测试结果汇总"""
    
    def test_print_collection_summary(self):
        """打印收集到的所有API数据摘要"""
        logger.info("=== API数据收集摘要 ===")
        
        for endpoint, data in collector.collected_data.items():
            logger.info(f"\n端点: {endpoint}")
            
            # 如果是ID列表，显示ID信息
            if endpoint.endswith("_ids") and isinstance(data, list):
                logger.info(f"收集到的ID数量: {len(data)}")
                logger.info(f"ID列表: {data}")
                continue
                
            # 如果是API响应数据，显示详细信息
            if isinstance(data, dict):
                logger.info(f"状态: {data.get('status', 'unknown')}")
                
                if 'data' in data:
                    if isinstance(data['data'], str):
                        try:
                            parsed_data = json.loads(data['data'])
                            logger.info(f"数据键: {list(parsed_data.keys())}")
                        except:
                            logger.info("数据: 字符串格式")
                    else:
                        logger.info(f"数据类型: {type(data['data'])}")
                
                if 'user' in data:
                    logger.info(f"用户信息键: {list(data['user'].keys())}")
            else:
                logger.info(f"数据类型: {type(data)}")
        
        logger.info(f"\n总共收集了 {len(collector.collected_data)} 个API端点的数据")


if __name__ == "__main__":
    # 可以直接运行此文件进行数据收集
    pytest.main([__file__, "-v", "-s"])
