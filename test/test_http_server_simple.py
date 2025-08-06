"""
简单的HTTP服务器，用于测试禅道数据库连接
"""
import json
import pymysql
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class ZentaoDatabase:
    """禅道数据库连接类"""
    
    def __init__(self):
        self.connection_params = {
            'host': '192.168.2.84',
            'port': 3306,
            'user': 'dev',
            'passwd': '123456',
            'db': 'zentao',
            'charset': 'utf8'
        }
        self.connection = None
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(**self.connection_params)
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def get_products(self):
        """获取产品列表"""
        if not self.connection:
            if not self.connect():
                return {"error": "数据库连接失败"}
        
        try:
            with self.connection.cursor() as cursor:
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
                        'id': row[0],
                        'name': row[1],
                        'code': row[2],
                        'PO': row[3],
                        'QD': row[4],
                        'createdBy': row[5],
                        'createdDate': str(row[6]) if row[6] else None
                    }
                    products.append(product)
                
                return {"products": products, "count": len(products)}
                
        except Exception as e:
            return {"error": f"查询失败: {str(e)}"}


# 全局数据库实例
db = ZentaoDatabase()


class ZentaoHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_html_response(self.get_index_html())
        elif parsed_path.path == '/api/products':
            self.send_json_response(db.get_products())
        elif parsed_path.path == '/api/test':
            self.send_json_response({"status": "ok", "message": "服务器运行正常"})
        else:
            self.send_error_response(404, "Not Found")
    
    def send_html_response(self, html):
        """发送HTML响应"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json_response(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def send_error_response(self, code, message):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        error_data = json.dumps({"error": message}, ensure_ascii=False)
        self.wfile.write(error_data.encode('utf-8'))
    
    def get_index_html(self):
        """获取首页HTML"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>禅道MCP服务器测试</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .button { padding: 10px 20px; margin: 10px; background: #007cba; color: white; border: none; cursor: pointer; }
        .button:hover { background: #005a87; }
        .result { margin: 20px 0; padding: 15px; background: #f5f5f5; border-left: 4px solid #007cba; }
        pre { background: #f9f9f9; padding: 10px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 禅道MCP服务器测试</h1>
        
        <h2>功能测试</h2>
        <button class="button" onclick="testConnection()">测试连接</button>
        <button class="button" onclick="getProducts()">获取产品列表</button>
        
        <div id="result" class="result" style="display:none;">
            <h3>结果:</h3>
            <pre id="resultContent"></pre>
        </div>
        
        <h2>API端点</h2>
        <ul>
            <li><a href="/api/test">/api/test</a> - 测试服务器状态</li>
            <li><a href="/api/products">/api/products</a> - 获取产品列表</li>
        </ul>
    </div>

    <script>
        function showResult(data) {
            document.getElementById('result').style.display = 'block';
            document.getElementById('resultContent').textContent = JSON.stringify(data, null, 2);
        }
        
        async function testConnection() {
            try {
                const response = await fetch('/api/test');
                const data = await response.json();
                showResult(data);
            } catch (error) {
                showResult({error: error.message});
            }
        }
        
        async function getProducts() {
            try {
                const response = await fetch('/api/products');
                const data = await response.json();
                showResult(data);
            } catch (error) {
                showResult({error: error.message});
            }
        }
    </script>
</body>
</html>
        """


def main():
    """主函数"""
    print("启动禅道HTTP测试服务器...")
    
    # 测试数据库连接
    if db.connect():
        print("✅ 数据库连接成功")
    else:
        print("⚠️  数据库连接失败，服务器仍会启动")
    
    # 启动HTTP服务器
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, ZentaoHandler)
    
    print(f"🌐 服务器启动在 http://localhost:8080")
    print("API端点:")
    print("  - http://localhost:8080/api/test")
    print("  - http://localhost:8080/api/products")
    print("\n按 Ctrl+C 停止服务器")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        if db.connection:
            db.connection.close()


if __name__ == "__main__":
    main()
