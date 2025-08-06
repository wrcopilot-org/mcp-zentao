"""
阶段四功能的HTTP测试服务器 - Bug管理
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


class StageFourHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if parsed_path.path == '/':
            self.send_html_response(self.get_index_html())
        elif parsed_path.path == '/api/bugs':
            self.send_json_response(self.get_bugs(query_params))        elif parsed_path.path == '/api/users':
            self.send_json_response(self.get_users())
        elif parsed_path.path == '/api/modules':
            product_id = query_params.get('product_id', [None])[0]
            if product_id:
                product_id = int(product_id)
            self.send_json_response(self.get_modules(product_id))
        elif parsed_path.path == '/api/products':
            self.send_json_response(self.get_products())
        elif parsed_path.path == '/api/test':
            self.send_json_response({"status": "ok", "message": "阶段四Bug管理服务器运行正常"})
        else:
            self.send_error_response(404, "Not Found")
    
    def get_bugs(self, query_params):
        """获取bug列表"""
        try:
            # 解析查询参数
            limit = int(query_params.get('limit', [50])[0])
            product_id = query_params.get('product_id', [None])[0]
            project_id = query_params.get('project_id', [None])[0]
            status = query_params.get('status', [None])[0]
            user_realname = query_params.get('user_realname', [None])[0]  # 新增：用户真实姓名参数
            
            if product_id:
                product_id = int(product_id)
            if project_id:
                project_id = int(project_id)
            
            # 限制查询数量
            if limit <= 0 or limit > 200:
                limit = 50
            
            bugs = db.get_bugs(limit=limit, product_id=product_id, project_id=project_id, 
                              status=status, user_realname=user_realname)
            
            return {
                "success": True,
                "data": bugs,
                "count": len(bugs),
                "filters": {
                    "limit": limit,
                    "product_id": product_id,
                    "project_id": project_id,
                    "status": status,
                    "user_realname": user_realname
                },
                "message": f"成功获取 {len(bugs)} 个Bug记录"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "获取Bug列表失败"
            }
    
    def get_users(self):
        """获取用户列表"""
        try:
            users = db.get_users()
            return {
                "success": True,
                "data": users,
                "count": len(users),
                "message": f"成功获取 {len(users)} 个用户"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "获取用户列表失败"
            }
    
    def get_modules(self, product_id=None):
        """获取功能模块列表"""
        try:
            modules = db.get_modules(product_id=product_id)
            filter_text = f" (产品ID: {product_id})" if product_id else ""
            return {
                "success": True,
                "data": modules,
                "count": len(modules),
                "product_id": product_id,
                "message": f"成功获取{filter_text} {len(modules)} 个功能模块"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "获取功能模块列表失败"
            }
    
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
    <title>禅道MCP阶段四功能测试 - Bug管理</title>
    <style>
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 40px; 
            background-color: #f5f7fa;
        }
        .container { 
            max-width: 1200px; 
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
            border-bottom: 2px solid #dc3545;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #f8f9fa;
        }
        .button { 
            padding: 12px 24px; 
            margin: 10px; 
            background: #dc3545; 
            color: white; 
            border: none; 
            cursor: pointer; 
            border-radius: 5px;
            font-size: 14px;
        }
        .button:hover { background: #c82333; }
        .button.secondary { background: #28a745; }
        .button.secondary:hover { background: #1e7e34; }
        .button.info { background: #17a2b8; }
        .button.info:hover { background: #138496; }
        .result { 
            margin: 20px 0; 
            padding: 20px; 
            background: #f8f9fa; 
            border-left: 4px solid #dc3545; 
            border-radius: 5px;
            max-height: 400px;
            overflow-y: auto;
        }
        pre { 
            background: #f4f4f4; 
            padding: 15px; 
            overflow-x: auto; 
            border-radius: 5px;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
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
        .form-row {
            display: flex;
            gap: 15px;
            margin: 15px 0;
        }
        .form-row .form-group {
            flex: 1;
            margin: 0;
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
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }
        .stat-item {
            text-align: center;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #dc3545;
        }
        .stat-label {
            color: #6c757d;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐛 禅道MCP阶段四功能测试</h1>
            <p>Bug管理、用户管理、模块管理</p>
        </div>
        
        <div id="status" class="status" style="display:none;"></div>
        
        <div class="stats" id="statsContainer" style="display:none;">
            <div class="stat-item">
                <div class="stat-number" id="bugCount">-</div>
                <div class="stat-label">Bug总数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="userCount">-</div>
                <div class="stat-label">用户总数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="moduleCount">-</div>
                <div class="stat-label">模块总数</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="productCount">-</div>
                <div class="stat-label">产品总数</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 基本功能测试</h2>
            <button class="button" onclick="testConnection()">测试连接</button>
            <button class="button secondary" onclick="loadUsers()">加载用户列表</button>
            <button class="button info" onclick="loadAllData()">加载所有统计</button>
        </div>
          <div class="section">
            <h2>🐛 Bug查询功能</h2>
            <div class="form-row">
                <div class="form-group">
                    <label for="bugLimit">返回数量:</label>
                    <input type="number" id="bugLimit" value="20" min="1" max="200">
                </div>
                <div class="form-group">
                    <label for="bugProductId">产品ID:</label>
                    <input type="number" id="bugProductId" placeholder="可选">
                </div>
                <div class="form-group">
                    <label for="bugProjectId">项目ID:</label>
                    <input type="number" id="bugProjectId" placeholder="可选">
                </div>
                <div class="form-group">
                    <label for="bugStatus">状态:</label>
                    <select id="bugStatus">
                        <option value="">全部状态</option>
                        <option value="active">活跃</option>
                        <option value="resolved">已解决</option>
                        <option value="closed">已关闭</option>
                        <option value="wait">等待</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="bugUserRealname">用户姓名:</label>
                    <input type="text" id="bugUserRealname" placeholder="如：韦家鹏">
                </div>
            </div>
            <button class="button" onclick="getBugs()">查询Bug列表</button>
        </div>
        
        <div class="section">
            <h2>📂 模块查询功能</h2>
            <div class="form-group">
                <label for="moduleProductId">产品ID (可选):</label>
                <input type="number" id="moduleProductId" placeholder="留空查询所有模块">
            </div>
            <button class="button secondary" onclick="getModules()">查询功能模块</button>
        </div>
        
        <div id="result" class="result" style="display:none;">
            <h3>查询结果:</h3>
            <pre id="resultContent"></pre>
        </div>
        
        <div class="section">
            <h2>📡 API端点</h2>
            <ul>
                <li><a href="/api/test" target="_blank">/api/test</a> - 测试服务器状态</li>
                <li><a href="/api/bugs?limit=10" target="_blank">/api/bugs?limit=10</a> - 获取Bug列表</li>
                <li><a href="/api/users" target="_blank">/api/users</a> - 获取用户列表</li>
                <li><a href="/api/modules" target="_blank">/api/modules</a> - 获取功能模块列表</li>
                <li><a href="/api/products" target="_blank">/api/products</a> - 获取产品列表</li>
            </ul>
        </div>
    </div>

    <script>
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
        
        function updateStats(bugs, users, modules, products) {
            document.getElementById('bugCount').textContent = bugs || '-';
            document.getElementById('userCount').textContent = users || '-';
            document.getElementById('moduleCount').textContent = modules || '-';
            document.getElementById('productCount').textContent = products || '-';
            document.getElementById('statsContainer').style.display = 'flex';
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
          async function getBugs() {
            try {
                const limit = document.getElementById('bugLimit').value || 20;
                const productId = document.getElementById('bugProductId').value;
                const projectId = document.getElementById('bugProjectId').value;
                const status = document.getElementById('bugStatus').value;
                const userRealname = document.getElementById('bugUserRealname').value;
                
                let url = `/api/bugs?limit=${limit}`;
                if (productId) url += `&product_id=${productId}`;
                if (projectId) url += `&project_id=${projectId}`;
                if (status) url += `&status=${status}`;
                if (userRealname) url += `&user_realname=${encodeURIComponent(userRealname)}`;
                
                showStatus('正在查询Bug列表...', 'success');
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.success) {
                    showStatus(data.message, 'success');
                    updateStats(data.count, null, null, null);
                } else {
                    showStatus(`查询失败: ${data.error}`, 'error');
                }
                
                showResult(data, 'Bug查询');
            } catch (error) {
                showResult({error: error.message}, 'Bug查询');
                showStatus('查询Bug失败', 'error');
            }
        }
        
        async function loadUsers() {
            try {
                showStatus('正在加载用户列表...', 'success');
                const response = await fetch('/api/users');
                const data = await response.json();
                
                if (data.success) {
                    showStatus(data.message, 'success');
                    updateStats(null, data.count, null, null);
                } else {
                    showStatus(`加载失败: ${data.error}`, 'error');
                }
                
                showResult(data, '用户列表');
            } catch (error) {
                showResult({error: error.message}, '用户列表');
                showStatus('加载用户列表失败', 'error');
            }
        }
        
        async function getModules() {
            try {
                const productId = document.getElementById('moduleProductId').value;
                let url = '/api/modules';
                if (productId) url += `?product_id=${productId}`;
                
                showStatus('正在查询功能模块...', 'success');
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.success) {
                    showStatus(data.message, 'success');
                    updateStats(null, null, data.count, null);
                } else {
                    showStatus(`查询失败: ${data.error}`, 'error');
                }
                
                showResult(data, '功能模块');
            } catch (error) {
                showResult({error: error.message}, '功能模块');
                showStatus('查询功能模块失败', 'error');
            }
        }
        
        async function loadAllData() {
            try {
                showStatus('正在加载所有统计数据...', 'success');
                
                // 并行加载所有数据
                const [bugsRes, usersRes, modulesRes, productsRes] = await Promise.all([
                    fetch('/api/bugs?limit=200'),
                    fetch('/api/users'),
                    fetch('/api/modules'),
                    fetch('/api/products')
                ]);
                
                const bugs = await bugsRes.json();
                const users = await usersRes.json();
                const modules = await modulesRes.json();
                const products = await productsRes.json();
                
                updateStats(
                    bugs.success ? bugs.count : 0,
                    users.success ? users.count : 0,
                    modules.success ? modules.count : 0,
                    products.success ? products.count : 0
                );
                
                showStatus('统计数据加载完成', 'success');
                showResult({
                    bugs: bugs.success ? bugs.count : 0,
                    users: users.success ? users.count : 0,
                    modules: modules.success ? modules.count : 0,
                    products: products.success ? products.count : 0
                }, '统计数据');
                
            } catch (error) {
                showResult({error: error.message}, '统计数据');
                showStatus('加载统计数据失败', 'error');
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
    print("启动禅道MCP阶段四Bug管理测试服务器...")
    
    # 测试数据库连接
    if db.connect():
        print("✅ 数据库连接成功")
        
        # 测试各项功能
        print("\n🧪 测试阶段四功能...")
        
        # 测试Bug查询
        bugs = db.get_bugs(limit=5)
        print(f"✅ Bug查询测试: 找到 {len(bugs)} 个Bug")
        
        # 测试用户查询
        users = db.get_users()
        print(f"✅ 用户查询测试: 找到 {len(users)} 个用户")
        
        # 测试模块查询
        modules = db.get_modules()
        print(f"✅ 模块查询测试: 找到 {len(modules)} 个功能模块")
        
    else:
        print("⚠️  数据库连接失败，服务器仍会启动")
    
    # 启动HTTP服务器
    server_address = ('', 8082)
    httpd = HTTPServer(server_address, StageFourHandler)
    
    print(f"\n🌐 阶段四Bug管理测试服务器启动在 http://localhost:8082")
    print("功能特性:")
    print("  - Bug列表查询 (支持按产品、项目、状态过滤)")
    print("  - 用户列表查询")
    print("  - 功能模块查询 (支持按产品过滤)")
    print("  - 数据统计展示")
    print("  - 可视化测试界面")
    print("\nAPI端点:")
    print("  - http://localhost:8082/api/test")
    print("  - http://localhost:8082/api/bugs?limit=20&status=active")
    print("  - http://localhost:8082/api/users")
    print("  - http://localhost:8082/api/modules?product_id=1")
    print("  - http://localhost:8082/api/products")
    print("\n按 Ctrl+C 停止服务器")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        if db.connection:
            db.connection.close()


if __name__ == "__main__":
    main()
