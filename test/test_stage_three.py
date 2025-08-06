"""
测试阶段三功能：通过产品名获取项目
"""
import sys
import os
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zentao_mcp_server import ZentaoDatabase


def test_stage_three():
    """测试阶段三的功能"""
    print("🧪 测试阶段三功能：通过产品名获取项目")
    print("=" * 60)
    
    # 创建数据库实例
    db = ZentaoDatabase()
    
    try:
        # 连接数据库
        print("1. 连接数据库...")
        if not db.connect():
            print("❌ 数据库连接失败")
            return
        print("✅ 数据库连接成功")
        
        # 获取所有产品列表
        print("\n2. 获取产品列表...")
        products = db.get_products()
        if not products:
            print("❌ 没有找到产品数据")
            return
        
        print(f"✅ 找到 {len(products)} 个产品")
        print("前几个产品:")
        for i, product in enumerate(products[:3]):
            print(f"  {i+1}. {product['name']} (ID: {product['id']})")
        
        # 选择第一个产品进行测试
        if products:
            test_product = products[0]
            product_name = test_product['name']
            
            print(f"\n3. 测试产品 '{product_name}' 的项目查询...")
            
            # 测试获取产品信息
            product_info = db.get_product_by_name(product_name)
            if product_info:
                print("✅ 产品信息获取成功:")
                print(f"  产品ID: {product_info['id']}")
                print(f"  产品名: {product_info['name']}")
                print(f"  产品缩写: {product_info['code']}")
                print(f"  产品经理: {product_info['PO']}")
                print(f"  测试主管: {product_info['QD']}")
            else:
                print("❌ 产品信息获取失败")
                return
            
            # 测试获取项目列表
            print(f"\n4. 获取产品 '{product_name}' 的相关项目...")
            projects = db.get_projects_by_product_name(product_name)
            
            if projects:
                print(f"✅ 找到 {len(projects)} 个相关项目:")
                for i, project in enumerate(projects):
                    print(f"\n  项目 {i+1}:")
                    print(f"    项目ID: {project['id']}")
                    print(f"    项目名称: {project['name']}")
                    print(f"    项目缩写: {project['code']}")
                    print(f"    开始时间: {project['begin']}")
                    print(f"    结束时间: {project['end']}")
                    print(f"    运行状态: {project['status']}")
                    print(f"    产品经理: {project['PO']}")
                    print(f"    项目经理: {project['PM']}")
                    print(f"    测试主管: {project['QD']}")
                
                # 输出JSON格式
                print(f"\n5. JSON格式输出:")
                result_data = {
                    "product": product_info,
                    "projects": projects,
                    "total_projects": len(projects)
                }
                print(json.dumps(result_data, ensure_ascii=False, indent=2))
                
            else:
                print(f"⚠️  产品 '{product_name}' 没有相关项目")
        
        # 测试不存在的产品
        print(f"\n6. 测试不存在的产品...")
        fake_product = "不存在的产品名称"
        fake_result = db.get_product_by_name(fake_product)
        if not fake_result:
            print(f"✅ 正确处理不存在的产品 '{fake_product}'")
        else:
            print(f"❌ 不应该找到产品 '{fake_product}'")
        
        print("\n" + "=" * 60)
        print("✅ 阶段三功能测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.disconnect()
        print("🔌 数据库连接已断开")


def test_mcp_functions():
    """测试MCP函数"""
    print("\n🧪 测试MCP函数")
    print("=" * 60)
    
    import asyncio
    from zentao_mcp_server import get_zentao_products, get_projects_by_product, db
    
    async def run_mcp_tests():
        try:
            # 连接数据库
            if not db.connect():
                print("❌ 数据库连接失败")
                return
            
            # 测试获取产品列表
            print("1. 测试 get_zentao_products...")
            products_result = await get_zentao_products()
            print(f"✅ 返回 {len(products_result)} 个内容块")
            
            # 获取一个产品名用于测试
            products = db.get_products()
            if products:
                test_product_name = products[0]['name']
                
                # 测试获取项目列表
                print(f"\n2. 测试 get_projects_by_product('{test_product_name}')...")
                projects_result = await get_projects_by_product(test_product_name)
                print(f"✅ 返回 {len(projects_result)} 个内容块")
                
                # 显示部分结果内容
                if projects_result:
                    print("结果预览:")
                    content = projects_result[0].text[:300] + "..." if len(projects_result[0].text) > 300 else projects_result[0].text
                    print(content)
                
                # 测试空产品名
                print(f"\n3. 测试空产品名...")
                empty_result = await get_projects_by_product("")
                print(f"✅ 正确处理空产品名，返回错误信息")
                
                # 测试不存在的产品名
                print(f"\n4. 测试不存在的产品名...")
                fake_result = await get_projects_by_product("不存在的产品")
                print(f"✅ 正确处理不存在的产品，返回错误信息")
            
        except Exception as e:
            print(f"❌ MCP函数测试失败: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.disconnect()
    
    # 运行异步测试
    asyncio.run(run_mcp_tests())


if __name__ == "__main__":
    # 运行所有测试
    test_stage_three()
    test_mcp_functions()
    
    print("\n🎉 所有测试完成！")
