# -*- coding=utf-8 -*-
#!/usr/bin/env python3
"""
测试Bug详情显示功能

测试BugModel的display_summary方法，
用于生成易于阅读的markdown格式的Bug摘要。
"""

import os
import json
import logging
import httpx
import pytest
from typing import Dict, Any, Optional

from mcp_zentao.models.bug import BugDetailResponse, BugDetailData, BugListResponse, BugModel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 禅道客户端配置
ZENTAO_HOST = httpx.Client(base_url="http://192.168.2.84/zentao/")


class TestBugDisplaySummary:
    """测试Bug显示摘要功能"""
    
    def test_get_bug_36151_details(self):
        """获取Bug的详细信息进行测试"""
        # 获取会话ID
        resp = ZENTAO_HOST.get("/api-getSessionID.json")
        assert resp.status_code == 200
        result = resp.json()
        session_id = json.loads(result["data"])["sessionID"]
        
        # 登录
        params = {
            "account": os.getenv("ZENTAO_ACCOUNT", "lianping"),
            "password": os.getenv("ZENTAO_PASSWORD", "123456"),
        }
        resp = ZENTAO_HOST.get(f"/user-login-{session_id}.json", params=params)
        assert resp.status_code == 200
        
        # 获取Bug详情 36151
        bug_id = "36151"
        resp = ZENTAO_HOST.get(f"/bug-view-{bug_id}.json")
        assert resp.status_code == 200
        result = resp.json()
        
        # 验证响应结构
        assert result["status"] == "success"
        assert "data" in result
        
        # 解析为BugDetailResponse
        bug_detail_response = BugDetailResponse(**result)
        bug_detail_data = bug_detail_response.get_bug_detail_data()
        
        # 测试新的display_summary方法
        summary = bug_detail_data.display_summary(
            session_id=session_id,
            zentao_base_url=ZENTAO_HOST.base_url
        )
        print("\n" + "="*60)
        print(f"{resp.url}")
        print("="*60)
        print(summary)
        print("="*60)
        
        # 保存原始数据用于分析
        os.makedirs("test_outputs", exist_ok=True)
        with open(f"test_outputs/bug_{bug_id}_detail.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 保存详情数据对象用于分析
        with open(f"test_outputs/bug_{bug_id}_parsed.json", "w", encoding="utf-8") as f:
            json.dump(bug_detail_data.model_dump(), f, ensure_ascii=False, indent=2)
        
        # 基本断言
        assert summary is not None
        assert "基本信息" in summary
        assert "重现步骤" in summary
        assert "历史记录" in summary
        
        return bug_detail_data
    
    def test_my_bug_list_display_summary(self):
        """测试我的Bug列表的display_summary方法"""
        # 获取会话ID
        resp = ZENTAO_HOST.get("/api-getSessionID.json")
        assert resp.status_code == 200
        result = resp.json()
        session_id = json.loads(result["data"])["sessionID"]
        
        # 登录
        params = {
            "account": os.getenv("ZENTAO_ACCOUNT", "lianping"),
            "password": os.getenv("ZENTAO_PASSWORD", "123456"),
        }
        resp = ZENTAO_HOST.get(f"/user-login-{session_id}.json", params=params)
        assert resp.status_code == 200
        
        # 获取我的Bug列表
        resp = ZENTAO_HOST.get("/my-bug.json")
        assert resp.status_code == 200
        result = resp.json()
        
        # 验证响应结构
        assert result["status"] == "success"
        assert "data" in result
        
        # 解析为BugListResponse
        bug_list_response = BugListResponse(**result)
        bug_list = bug_list_response.get_bug_list()
        
        print("\n" + "="*60)
        print(f"{resp.url} (当前页共 {len(bug_list)} 个Bug):")
        print("="*60)
        
        # 显示前5个Bug的摘要
        for i, bug in enumerate(bug_list[:5]):
            print(f"\n--- Bug #{bug.id} ---")
            summary = bug.display_summary()
            print(summary)
            
            if i < 4 and i < len(bug_list) - 1:
                print("\n" + "-"*40)
        
        if len(bug_list) > 5:
            print(f"\n... 还有 {len(bug_list) - 5} 个Bug未显示")
        
        print("="*60)
        
        # 保存列表数据用于分析
        os.makedirs("test_outputs", exist_ok=True)
        with open("test_outputs/my_bug_list.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # 基本断言
        assert len(bug_list) > 0
        if bug_list:
            first_bug_summary = bug_list[0].display_summary()
            assert first_bug_summary is not None
            assert "Bug详情" in first_bug_summary
            assert bug_list[0].title in first_bug_summary
        
        return bug_list


if __name__ == "__main__":
    test = TestBugDisplaySummary()
    
    print("\n\n=== 测试Bug列表显示摘要 ===")
    test.test_my_bug_list_display_summary()
    
    print("=== 测试Bug详情显示摘要 ===")
    test.test_get_bug_36151_details()
