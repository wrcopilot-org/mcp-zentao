"""
测试分页客户端功能

验证新的分页API客户端是否正常工作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from mcp_zentao.client import ZenTaoClient


def test_paginated_client():
    """测试分页客户端功能"""
    
    # 创建客户端
    with ZenTaoClient("http://192.168.2.84/zentao/") as client:
        # 登录
        print("=== 登录 ===")
        user = client.login(
            os.getenv("ZENTAO_ACCOUNT", "lianping"), 
            os.getenv("ZENTAO_PASSWORD", "123456")
        )
        print(f"登录用户: {user.realname} ({user.account})")
        
        # 测试任务分页
        print("\n=== 测试任务分页 ===")
        
        # 获取第一页任务
        tasks_page1 = client.tasks.get_my_tasks(page=1, per_page=10)
        print(f"第一页任务数量: {len(tasks_page1)}")
        if tasks_page1:
            print(f"第一个任务: {tasks_page1[0].name}")
        
        # 获取第二页任务
        try:
            tasks_page2 = client.tasks.get_my_tasks(page=2, per_page=10)
            print(f"第二页任务数量: {len(tasks_page2)}")
            if tasks_page2:
                print(f"第二页第一个任务: {tasks_page2[0].name}")
        except Exception as e:
            print(f"获取第二页任务失败: {e}")
        
        # 获取所有任务（限制最大3页）
        print("\n--- 获取所有任务（限制3页）---")
        try:
            all_tasks = client.tasks.get_my_tasks_all_pages(per_page=10, max_pages=3)
            print(f"所有任务总数: {len(all_tasks)}")
        except Exception as e:
            print(f"获取所有任务失败: {e}")
        
        # 测试缺陷分页
        print("\n=== 测试缺陷分页 ===")
        
        # 获取第一页缺陷
        bugs_page1 = client.bugs.get_my_bugs(page=1, per_page=10)
        print(f"第一页缺陷数量: {len(bugs_page1)}")
        if bugs_page1:
            print(f"第一个缺陷: {bugs_page1[0].title}")
        
        # 获取第二页缺陷
        try:
            bugs_page2 = client.bugs.get_my_bugs(page=2, per_page=10)
            print(f"第二页缺陷数量: {len(bugs_page2)}")
            if bugs_page2:
                print(f"第二页第一个缺陷: {bugs_page2[0].title}")
        except Exception as e:
            print(f"获取第二页缺陷失败: {e}")
        
        # 测试项目分页（通常项目数量较少）
        print("\n=== 测试项目分页 ===")
        
        projects_page1 = client.projects.get_my_projects(page=1, per_page=10)
        print(f"第一页项目数量: {len(projects_page1)}")
        if projects_page1:
            print(f"第一个项目: {projects_page1[0].name}")
        
        # 测试带状态过滤的分页
        print("\n=== 测试状态过滤分页 ===")
        
        # 获取进行中的任务
        doing_tasks = client.tasks.get_my_tasks(status='doing', page=1, per_page=10)
        print(f"进行中的任务数量: {len(doing_tasks)}")
        
        # 获取活跃的缺陷
        active_bugs = client.bugs.get_my_bugs(status='active', page=1, per_page=10)
        print(f"活跃缺陷数量: {len(active_bugs)}")
        
        print("\n=== 分页测试完成 ===")


if __name__ == "__main__":
    test_paginated_client()
