"""
禅道数据库连接测试（简化版本）
不依赖MCP包，直接测试数据库功能
"""
import pymysql
import json
from typing import List, Dict, Any


class ZentaoDatabase:
    """禅道数据库连接管理类"""
    
    def __init__(self, host: str = '192.168.2.84', port: int = 3306, 
                 user: str = 'dev', password: str = '123456', 
                 database: str = 'zentao', charset: str = 'utf8'):
        self.connection_params = {
            'host': host,
            'port': port,
            'user': user,
            'passwd': password,
            'db': database,
            'charset': charset
        }
        self.connection = None
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(**self.connection_params)
            print(f"✅ 数据库连接成功: {self.connection_params['host']}:{self.connection_params['port']}")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            print("✅ 数据库连接已断开")
    
    def test_connection(self):
        """测试数据库连接"""
        if not self.connection:
            if not self.connect():
                return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print(f"✅ 数据库连接测试成功: {result}")
                return True
        except Exception as e:
            print(f"❌ 数据库连接测试失败: {e}")
            return False
    
    def get_products(self) -> List[Dict[str, Any]]:
        """获取产品列表"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor() as cursor:
                # 先检查表是否存在
                cursor.execute("SHOW TABLES LIKE 'zt_product'")
                if not cursor.fetchone():
                    print("⚠️  表 zt_product 不存在")
                    return []
                
                # 查询产品数据
                sql = """
                SELECT id, name, code, PO, QD, createdBy, createdDate 
                FROM zt_product 
                WHERE deleted = '0'
                ORDER BY id
                LIMIT 10
                """
                cursor.execute(sql)
                results = cursor.fetchall()
                
                products = []
                for row in results:
                    product = {
                        'id': row[0],  # 产品唯一编号
                        'name': row[1],  # 产品名
                        'code': row[2],  # 产品缩写名
                        'PO': row[3],  # 负责的产品经理
                        'QD': row[4],  # 负责的测试主管
                        'createdBy': row[5],  # 此记录的创建人
                        'createdDate': str(row[6]) if row[6] else None  # 此记录的创建日期
                    }
                    products.append(product)
                
                print(f"✅ 成功获取 {len(products)} 个产品")
                return products
                
        except Exception as e:
            print(f"❌ 查询产品列表失败: {e}")
            return []
    
    def show_database_info(self):
        """显示数据库信息"""
        if not self.connection:
            if not self.connect():
                return
        
        try:
            with self.connection.cursor() as cursor:
                # 显示数据库版本
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                print(f"数据库版本: {version}")
                
                # 显示当前数据库
                cursor.execute("SELECT DATABASE()")
                db_name = cursor.fetchone()[0]
                print(f"当前数据库: {db_name}")
                
                # 显示表列表
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"数据库表数量: {len(tables)}")
                
                # 检查zt_product表结构
                cursor.execute("SHOW TABLES LIKE 'zt_product'")
                if cursor.fetchone():
                    cursor.execute("DESCRIBE zt_product")
                    columns = cursor.fetchall()
                    print("\nzt_product 表结构:")
                    for col in columns:
                        print(f"  {col[0]} - {col[1]}")
                else:
                    print("⚠️  zt_product 表不存在")
                    
        except Exception as e:
            print(f"❌ 获取数据库信息失败: {e}")


def main():
    """主测试函数"""
    print("禅道数据库连接测试")
    print("=" * 60)
    
    # 创建数据库实例
    db = ZentaoDatabase()
    
    try:
        # 测试连接
        print("1. 测试数据库连接...")
        if not db.connect():
            print("❌ 无法连接到数据库，请检查配置")
            return
        
        # 测试基本查询
        print("\n2. 测试基本查询...")
        db.test_connection()
        
        # 显示数据库信息
        print("\n3. 显示数据库信息...")
        db.show_database_info()
        
        # 获取产品列表
        print("\n4. 获取产品列表...")
        products = db.get_products()
        
        if products:
            print(f"\n前 {min(3, len(products))} 个产品详情:")
            for i, product in enumerate(products[:3]):
                print(f"\n产品 {i+1}:")
                for key, value in product.items():
                    print(f"  {key}: {value}")
            
            # 输出JSON格式
            print(f"\n所有产品 JSON 格式:")
            print(json.dumps(products, ensure_ascii=False, indent=2))
        else:
            print("⚠️  没有找到产品数据")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    finally:
        # 断开连接
        print("\n5. 断开数据库连接...")
        db.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")


if __name__ == "__main__":
    main()
