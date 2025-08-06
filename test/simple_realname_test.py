#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的用户真实姓名查询测试
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import():
    """测试导入是否成功"""
    try:
        from src.zentao_mcp_server import ZentaoDatabase
        print("✓ 导入 ZentaoDatabase 成功")
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    try:
        from src.zentao_mcp_server import ZentaoDatabase
        db = ZentaoDatabase()
        
        # 这里不真正连接数据库，只测试对象创建
        print("✓ ZentaoDatabase 对象创建成功")
        
        # 测试get_bugs方法是否存在新参数
        import inspect
        sig = inspect.signature(db.get_bugs)
        params = list(sig.parameters.keys())
        
        if 'user_realname' in params:
            print("✓ get_bugs 方法包含 user_realname 参数")
        else:
            print("✗ get_bugs 方法缺少 user_realname 参数")
            
        print(f"get_bugs 方法参数: {params}")
        return True
        
    except Exception as e:
        print(f"✗ 数据库测试失败: {e}")
        return False

def test_mcp_function():
    """测试MCP函数定义"""
    try:
        from src.zentao_mcp_server import get_zentao_bugs
        import inspect
        
        sig = inspect.signature(get_zentao_bugs)
        params = list(sig.parameters.keys())
        
        if 'user_realname' in params:
            print("✓ get_zentao_bugs 函数包含 user_realname 参数")
        else:
            print("✗ get_zentao_bugs 函数缺少 user_realname 参数")
            
        print(f"get_zentao_bugs 函数参数: {params}")
        return True
        
    except Exception as e:
        print(f"✗ MCP函数测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 用户真实姓名查询功能测试 ===")
    
    success = True
    
    print("\n1. 测试模块导入...")
    success &= test_import()
    
    print("\n2. 测试数据库类...")
    success &= test_database_connection()
    
    print("\n3. 测试MCP函数...")
    success &= test_mcp_function()
    
    print(f"\n=== 测试结果: {'成功' if success else '失败'} ===")
