"""
阶段三功能的HTTP测试服务器
"""
import json
import pymysql
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from zentao_mcp_server import ZentaoDatabase


# 全局数据库实例
db = ZentaoDatabase()


class StageThreeHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if parsed_path.path == '/':
            self.send_html_response(self.get_index_html())
        elif parsed_path.path == '/api/products':
            self.send_json_response(self.get_products())
        elif parsed_path.path == '/api/projects':
            product_name = query_params.get('product_name', [''])[0]
            self.send_json_response(self.get_projects_by_product(product_name))
        elif parsed_path.path == '/api/test':
            self.send_json_response({"status": "ok", "message": "阶段三服务器运行正常"})
        else:
            self.send_error_response(404, "Not Found")
    
    def get_products(self):
        """获取产品列表"""
        try:
            products = db.get_products()
            return {
                "success": True,
                "data": products,
                "count": len(products),
                "message": f"成功获取 {len(products)} 个产品"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "获取产品列表失败"
            }
    
    def get_projects_by_product(self, product_name):
        """通过产品名获取项目"""
        if not product_name:
            return {
                "success": False,
                "error": "产品名称不能为空",
                "message": "请提供产品名称参数"
            }
        
        try:
            # 获取产品信息
            product = db.get_product_by_name(product_name)
            if not product:
                return {
                    "success": False,
                    "error": f"未找到产品 '{product_name}'",
                    "message": "请检查产品名称是否正确"
                }
            
            # 获取项目列表
            projects = db.get_projects_by_product_name(product_name)
            
            return {
                "success": True,
                "data": {
                    "product": product,
                    "projects": projects,
                    "total_projects": len(projects)
                },
                "message": f"产品 '{product_name}' 有 {len(projects)} 个相关项目"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "获取项目列表失败"
            }
    
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
    <title>禅道MCP阶段三功能测试</title>
    <style>
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 40px; 
            background-color: #f5f7fa;
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #007cba;
        }
        .button { 
            padding: 12px 24px; 
            margin: 10px; 
            background: #007cba; 
            color: white; 
            border: none; 
            cursor: pointer; 
            border-radius: 5px;
            font-size: 14px;
        }
        .button:hover { background: #005a87; }
        .button.secondary { background: #28a745; }
        .button.secondary:hover { background: #1e7e34; }
        .result { 
            margin: 20px 0; 
            padding: 20px; 
            background: #f8f9fa; 
            border-left: 4px solid #007cba; 
            border-radius: 5px;
        }
        pre { 
            background: #f4f4f4; 
            padding: 15px; 
            overflow-x: auto; 
            border-radius: 5px;
            font-size: 12px;
        }
        .form-group {
            margin: 15px 0;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .product-list {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin: 10px 0;
        }
        .product-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
        }
        .product-item:hover {
            background-color: #f0f0f0;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .status.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 禅道MCP阶段三功能测试</h1>
            <p>通过产品名获取相关项目</p>
        </div>
        
        <div id="status" class="status" style="display:none;"></div>
        
        <h2>📋 基本功能测试</h2>
        <button class="button" onclick="testConnection()">测试连接</button>
        <button class="button" onclick="loadProducts()">加载产品列表</button>
        
        <h2>🔍 项目查询功能</h2>
        <div class="form-group">
            <label for="productSelect">选择产品:</label>
            <select id="productSelect" onchange="updateProductName()">
                <option value="">请选择产品...</option>
            </select>
        </div>
        
        <div class="form-group">
            <label for="productName">或手动输入产品名:</label>
            <input type="text" id="productName" placeholder="请输入产品名称">
        </div>
        
        <button class="button secondary" onclick="getProjectsByProduct()">获取相关项目</button>
        
        <div id="productsList" class="result" style="display:none;">
            <h3>产品列表:</h3>
            <div id="productsContent"></div>
        </div>
        
        <div id="result" class="result" style="display:none;">
            <h3>查询结果:</h3>
            <pre id="resultContent"></pre>
        </div>
        
        <h2>📡 API端点</h2>
        <ul>
            <li><a href="/api/test" target="_blank">/api/test</a> - 测试服务器状态</li>
            <li><a href="/api/products" target="_blank">/api/products</a> - 获取产品列表</li>
            <li><a href="/api/projects?product_name=示例产品" target="_blank">/api/projects?product_name=产品名</a> - 获取项目列表</li>
        </ul>
    </div>

    <script>
        let productsData = [];
        
        function showStatus(message, type = 'success') {
            const statusDiv = document.getElementById('status');
            statusDiv.className = `status ${type}`;
            statusDiv.textContent = message;
            statusDiv.style.display = 'block';
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }
        
        function showResult(data, title = '结果') {
            document.getElementById('result').style.display = 'block';
            document.getElementById('resultContent').textContent = JSON.stringify(data, null, 2);
        }
        
        async function testConnection() {
            try {
                showStatus('正在测试连接...', 'success');
                const response = await fetch('/api/test');
                const data = await response.json();
                showResult(data, '连接测试');
                showStatus('连接测试成功', 'success');
            } catch (error) {
                showResult({error: error.message}, '连接测试');
                showStatus('连接测试失败', 'error');
            }
        }
        
        async function loadProducts() {
            try {
                showStatus('正在加载产品列表...', 'success');
                const response = await fetch('/api/products');
                const data = await response.json();
                
                if (data.success) {
                    productsData = data.data;
                    updateProductSelect();
                    showProductsList(data.data);
                    showStatus(`成功加载 ${data.count} 个产品`, 'success');
                } else {
                    showStatus(`加载失败: ${data.error}`, 'error');
                }
                
                showResult(data, '产品列表');
            } catch (error) {
                showResult({error: error.message}, '产品列表');
                showStatus('加载产品列表失败', 'error');
            }
        }
        
        function updateProductSelect() {
            const select = document.getElementById('productSelect');
            select.innerHTML = '<option value="">请选择产品...</option>';
            
            productsData.forEach(product => {
                const option = document.createElement('option');
                option.value = product.name;
                option.textContent = `${product.name} (${product.code})`;
                select.appendChild(option);
            });
        }
        
        function updateProductName() {
            const select = document.getElementById('productSelect');
            const input = document.getElementById('productName');
            input.value = select.value;
        }
        
        function showProductsList(products) {
            const div = document.getElementById('productsList');
            const content = document.getElementById('productsContent');
            
            let html = '<div class="product-list">';
            products.forEach((product, index) => {
                html += `
                    <div class="product-item" onclick="selectProduct('${product.name}')">
                        <strong>${product.name}</strong> (${product.code})
                        <br><small>产品经理: ${product.PO} | 测试主管: ${product.QD}</small>
                    </div>
                `;
            });
            html += '</div>';
            
            content.innerHTML = html;
            div.style.display = 'block';
        }
        
        function selectProduct(productName) {
            document.getElementById('productName').value = productName;
            document.getElementById('productSelect').value = productName;
        }
        
        async function getProjectsByProduct() {
            const productName = document.getElementById('productName').value.trim();
            
            if (!productName) {
                showStatus('请输入或选择产品名称', 'error');
                return;
            }
            
            try {
                showStatus(`正在查询产品 "${productName}" 的相关项目...`, 'success');
                const response = await fetch(`/api/projects?product_name=${encodeURIComponent(productName)}`);
                const data = await response.json();
                
                if (data.success) {
                    showStatus(data.message, 'success');
                } else {
                    showStatus(`查询失败: ${data.error}`, 'error');
                }
                
                showResult(data, '项目查询');
            } catch (error) {
                showResult({error: error.message}, '项目查询');
                showStatus('查询项目失败', 'error');
            }
        }
        
        // 页面加载时自动测试连接
        window.onload = function() {
            testConnection();
        };
    </script>
</body>
</html>
        """


def main():
    """主函数"""
    print("启动禅道MCP阶段三测试服务器...")
    
    # 测试数据库连接
    if db.connect():
        print("✅ 数据库连接成功")
        
        # 测试产品查询
        products = db.get_products()
        print(f"✅ 找到 {len(products)} 个产品")
        
        # 测试项目查询（如果有产品的话）
        if products:
            test_product = products[0]['name']
            projects = db.get_projects_by_product_name(test_product)
            print(f"✅ 产品 '{test_product}' 有 {len(projects)} 个相关项目")
    else:
        print("⚠️  数据库连接失败，服务器仍会启动")
    
    # 启动HTTP服务器
    server_address = ('', 8081)
    httpd = HTTPServer(server_address, StageThreeHandler)
    
    print(f"🌐 阶段三测试服务器启动在 http://localhost:8081")
    print("功能:")
    print("  - 产品列表查询")
    print("  - 通过产品名获取相关项目")
    print("  - 可视化测试界面")
    print("\nAPI端点:")
    print("  - http://localhost:8081/api/test")
    print("  - http://localhost:8081/api/products")
    print("  - http://localhost:8081/api/projects?product_name=产品名")
    print("\n按 Ctrl+C 停止服务器")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        if db.connection:
            db.connection.close()


if __name__ == "__main__":
    main()
