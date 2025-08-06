"""
简化的禅道数据库测试
"""
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_import():
    """测试模块导入"""
    try:
        from zentao_mcp_server import ZentaoDatabase
        print("✅ 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_database_creation():
    """测试数据库对象创建"""
    try:
        from zentao_mcp_server import ZentaoDatabase
        db = ZentaoDatabase()
        print("✅ 数据库对象创建成功")
        return True
    except Exception as e:
        print(f"❌ 数据库对象创建失败: {e}")
        return False

def test_database_connection():
    """测试数据库连接"""
    try:
        from zentao_mcp_server import ZentaoDatabase
        db = ZentaoDatabase()
        result = db.connect()
        
        if result:
            print("✅ 数据库连接成功")
            # 测试获取产品
            products = db.get_products()
            print(f"✅ 获取到 {len(products)} 个产品")
            
            if products:
                print("第一个产品信息:")
                for key, value in products[0].items():
                    print(f"  {key}: {value}")
            
            db.disconnect()
            return True
        else:
            print("⚠️  数据库连接失败（可能是网络或配置问题）")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始禅道数据库测试...")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_import),
        ("数据库对象创建", test_database_creation),
        ("数据库连接", test_database_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n运行测试: {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败")

if __name__ == "__main__":
    main()
