#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通过用户真实姓名查询Bug功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.zentao_mcp_server import ZentaoDatabase

def test_user_realname_bug_query():
    """测试通过用户真实姓名查询Bug功能"""
    print("🧪 测试通过用户真实姓名查询Bug功能")
    print("=" * 50)
    
    # 初始化数据库连接
    db = ZentaoDatabase()
    
    # 测试1: 查询所有用户，了解数据库中有哪些用户
    print("\n1. 查询所有用户:")
    users = db.get_users()
    if users:
        print(f"找到 {len(users)} 个用户:")
        for i, user in enumerate(users[:5], 1):  # 只显示前5个
            print(f"  {i}. {user['realname']} ({user['account']}) - {user['role']}")
        if len(users) > 5:
            print(f"  ... 还有 {len(users) - 5} 个用户")
    else:
        print("❌ 没有找到用户数据")
        return
    
    # 测试2: 使用第一个用户的真实姓名查询Bug
    if users:
        test_realname = users[0]['realname']
        print(f"\n2. 查询用户 '{test_realname}' 相关的Bug:")
        
        bugs = db.get_bugs(limit=10, user_realname=test_realname)
        if bugs:
            print(f"✅ 找到 {len(bugs)} 个相关Bug:")
            for i, bug in enumerate(bugs, 1):
                print(f"  Bug {i}:")
                print(f"    ID: {bug['id']}")
                print(f"    标题: {bug['title']}")
                print(f"    状态: {bug['status']}")
                print(f"    开启人: {bug['opened_by_name']} ({bug['openedBy']})")
                if bug['assignedTo']:
                    print(f"    指派给: {bug['assigned_to_name']} ({bug['assignedTo']})")
                if bug['resolvedBy']:
                    print(f"    解决人: {bug['resolved_by_name']} ({bug['resolvedBy']})")
                if bug['closedBy']:
                    print(f"    关闭人: {bug['closed_by_name']} ({bug['closedBy']})")
                print()
        else:
            print(f"❌ 用户 '{test_realname}' 没有相关的Bug")
    
    # 测试3: 使用不存在的用户名
    print("\n3. 查询不存在的用户 '不存在的用户' 相关的Bug:")
    bugs = db.get_bugs(limit=10, user_realname="不存在的用户")
    if not bugs:
        print("✅ 正确返回空结果（用户不存在）")
    else:
        print("❌ 应该返回空结果，但返回了数据")
    
    # 测试4: 如果有"韦家鹏"这个用户，专门测试
    weijiapeng_bugs = db.get_bugs(limit=10, user_realname="韦家鹏")
    if weijiapeng_bugs:
        print(f"\n4. 查询用户 '韦家鹏' 相关的Bug:")
        print(f"✅ 找到 {len(weijiapeng_bugs)} 个相关Bug:")
        for i, bug in enumerate(weijiapeng_bugs, 1):
            print(f"  Bug {i}: {bug['title']} (ID: {bug['id']})")
    else:
        print(f"\n4. 查询用户 '韦家鹏' 相关的Bug:")
        print("ℹ️ 用户 '韦家鹏' 没有相关的Bug或用户不存在")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    test_user_realname_bug_query()
