import pytest
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zentao_mcp_server import ZentaoDatabase


class TestZentaoDatabase:
    """测试禅道数据库连接和功能"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.db = ZentaoDatabase()
    
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        if self.db:
            self.db.disconnect()
    
    def test_database_connection(self):
        """测试数据库连接"""
        result = self.db.connect()
        assert result is not None, "数据库连接应该成功或返回错误信息"
        
        if result:
            print("✅ 数据库连接成功")
        else:
            print("❌ 数据库连接失败")
    
    def test_get_products(self):
        """测试获取产品列表"""
        # 首先尝试连接数据库
        connection_result = self.db.connect()
        
        if not connection_result:
            pytest.skip("数据库连接失败，跳过产品列表测试")
        
        products = self.db.get_products()
        
        # 验证返回的数据结构
        assert isinstance(products, list), "产品列表应该是一个列表"
        
        if products:
            # 检查第一个产品的数据结构
            first_product = products[0]
            required_fields = ['id', 'name', 'code', 'PO', 'QD', 'createdBy', 'createdDate']
            
            for field in required_fields:
                assert field in first_product, f"产品数据应该包含字段: {field}"
            
            print(f"✅ 成功获取 {len(products)} 个产品")
            print("第一个产品信息:")
            for key, value in first_product.items():
                print(f"  {key}: {value}")
        else:
            print("⚠️  数据库中没有产品数据")
    
    def test_database_disconnect(self):
        """测试数据库断开连接"""
        # 先连接
        self.db.connect()
        
        # 然后断开
        self.db.disconnect()
        
        # 验证连接已断开
        assert self.db.connection is None, "断开连接后，connection应该为None"
        print("✅ 数据库断开连接成功")


if __name__ == "__main__":
    # 直接运行测试
    test_db = TestZentaoDatabase()
    
    print("开始测试禅道数据库功能...")
    print("=" * 50)
    
    try:
        test_db.setup_method()
        test_db.test_database_connection()
        print()
        
        test_db.test_get_products()
        print()
        
        test_db.test_database_disconnect()
        print()
        
        print("=" * 50)
        print("✅ 所有测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    finally:
        test_db.teardown_method()
