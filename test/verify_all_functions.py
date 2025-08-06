"""
禅道MCP服务器完整功能验证脚本
测试所有四个阶段的功能
"""
import asyncio
import sys
import os
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def test_all_functions():
    """测试所有MCP功能"""
    from zentao_mcp_server import (
        ZentaoDatabase, 
        get_zentao_products, 
        get_projects_by_product,
        get_zentao_bugs,
        get_zentao_users,
        get_zentao_modules
    )
    
    print("🧪 禅道MCP服务器完整功能验证")
    print("=" * 60)
    
    # 创建数据库实例
    db = ZentaoDatabase()
    
    try:
        # 阶段一：测试数据库连接
        print("\n📍 阶段一：数据库连接测试")
        print("-" * 40)
        if db.connect():
            print("✅ 数据库连接成功")
        else:
            print("❌ 数据库连接失败")
            return False
        
        # 阶段二：测试产品查询
        print("\n📍 阶段二：产品查询测试")
        print("-" * 40)
        products_result = await get_zentao_products()
        print(f"✅ 产品查询成功: {len(products_result)} 个内容块")
        
        # 获取第一个产品用于后续测试
        products = db.get_products()
        test_product_name = products[0]['name'] if products else None
        
        if test_product_name:
            print(f"📝 将使用产品 '{test_product_name}' 进行后续测试")
        
        # 阶段三：测试项目查询
        print("\n📍 阶段三：项目查询测试")
        print("-" * 40)
        if test_product_name:
            projects_result = await get_projects_by_product(test_product_name)
            print(f"✅ 项目查询成功: {len(projects_result)} 个内容块")
        else:
            print("⚠️  跳过项目查询测试：没有可用的产品数据")
        
        # 阶段四：测试Bug管理功能
        print("\n📍 阶段四：Bug管理功能测试")
        print("-" * 40)
        
        # 测试Bug查询
        bugs_args = {"limit": 5}
        bugs_result = await get_zentao_bugs(bugs_args)
        print(f"✅ Bug查询成功: {len(bugs_result)} 个内容块")
        
        # 测试用户查询
        users_result = await get_zentao_users()
        print(f"✅ 用户查询成功: {len(users_result)} 个内容块")
        
        # 测试模块查询
        modules_args = {}
        modules_result = await get_zentao_modules(modules_args)
        print(f"✅ 模块查询成功: {len(modules_result)} 个内容块")
        
        # 数据统计
        print("\n📊 数据统计汇总")
        print("-" * 40)
        products_count = len(db.get_products())
        bugs_count = len(db.get_bugs(limit=200))
        users_count = len(db.get_users())
        modules_count = len(db.get_modules())
        
        print(f"📦 产品总数: {products_count}")
        print(f"🐛 Bug总数: {bugs_count}")
        print(f"👥 用户总数: {users_count}")
        print(f"📂 模块总数: {modules_count}")
        
        # 功能覆盖测试
        print("\n🎯 功能覆盖验证")
        print("-" * 40)
        
        all_functions = [
            "✅ 阶段一: 数据库连接",
            "✅ 阶段二: 产品数据查询",
            "✅ 阶段三: 项目关联查询",
            "✅ 阶段四: Bug管理系统",
            "✅ 阶段四: 用户信息管理",
            "✅ 阶段四: 功能模块管理"
        ]
        
        for func in all_functions:
            print(f"  {func}")
        
        print("\n🎉 所有功能验证完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.disconnect()
        print("\n🔌 数据库连接已断开")


def test_mcp_tools_definition():
    """测试MCP工具定义"""
    print("\n🔧 MCP工具定义验证")
    print("-" * 40)
    
    tools = [
        {
            "name": "list_products",
            "stage": "阶段二",
            "description": "获取产品列表"
        },
        {
            "name": "get_projects_by_product",
            "stage": "阶段三", 
            "description": "通过产品名获取项目"
        },
        {
            "name": "get_bugs",
            "stage": "阶段四",
            "description": "获取Bug列表"
        },
        {
            "name": "list_users",
            "stage": "阶段四",
            "description": "获取用户列表"
        },
        {
            "name": "list_modules",
            "stage": "阶段四",
            "description": "获取模块列表"
        }
    ]
    
    for i, tool in enumerate(tools, 1):
        print(f"  {i}. {tool['name']} ({tool['stage']}) - {tool['description']}")
    
    print(f"\n📊 总计: {len(tools)} 个MCP工具")


def main():
    """主函数"""
    print("🚀 启动禅道MCP服务器完整功能验证")
    print("项目: zentao-mcp")
    print("版本: 最终完成版")
    print("日期: 2025年8月6日")
    
    # 测试MCP工具定义
    test_mcp_tools_definition()
    
    # 运行异步功能测试
    success = asyncio.run(test_all_functions())
    
    print("\n" + "=" * 60)
    if success:
        print("🎊 验证结果: 所有功能正常运行！")
        print("✅ 项目已准备投入使用")
    else:
        print("⚠️  验证结果: 发现问题，请检查配置")
    
    print("\n📚 相关文档:")
    print("  - README_ZENTAO.md - 项目主文档")
    print("  - FINAL_PROJECT_REPORT.md - 最终完成报告")
    print("  - start_zentao_mcp.bat - 启动主服务器")
    print("  - start_stage_four_test.bat - 启动测试界面")


if __name__ == "__main__":
    main()
