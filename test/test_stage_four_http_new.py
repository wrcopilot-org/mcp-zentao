#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段四功能的HTTP测试服务器 - 支持用户姓名Bug查询
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
            self.send_json_response(self.get_bugs(query_params))
        elif parsed_path.path == '/api/users':
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
        """获取模块列表"""
        try:
            modules = db.get_modules(product_id)
            return {
                "success": True,
                "data": modules,
                "count": len(modules),
                "product_id": product_id,
                "message": f"成功获取 {len(modules)} 个模块"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "获取模块列表失败"
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
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def send_error_response(self, code, message):
        """发送错误响应"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        error_data = {"error": message, "code": code}
        self.wfile.write(json.dumps(error_data).encode('utf-8'))
    
    def get_index_html(self):
        """获取首页HTML"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>禅道MCP阶段四功能测试 - 支持用户姓名查询</title>
    <style>
        body { 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.95); 
            padding: 30px; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            color: #333;
        }
        .header h1 { 
            margin: 0; 
            color: #4a47a3; 
            font-size: 28px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        .section { 
            margin: 30px 0; 
            padding: 20px; 
            border: 1px solid #e0e0e0; 
            border-radius: 10px; 
            background: #fafafa;
        }
        .section h2 { 
            color: #333; 
            margin-top: 0; 
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        .button { 
            padding: 12px 24px; 
            margin: 10px; 
            background: #667eea; 
            color: white; 
            border: none; 
            cursor: pointer; 
            border-radius: 5px;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        .button:hover { 
            background: #5a67d8; 
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .button.secondary { background: #48bb78; }
        .button.secondary:hover { background: #38a169; }
        .button.info { background: #ed8936; }
        .button.info:hover { background: #dd6b20; }
        .result { 
            margin: 20px 0; 
            padding: 20px; 
            background: #f8f9fa; 
            border-left: 4px solid #667eea; 
            border-radius: 5px;
            display: none;
        }
        pre { 
            background: #f4f4f4; 
            padding: 15px; 
            overflow-x: auto; 
            border-radius: 5px;
            font-size: 12px;
        }
        .form-row {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin: 20px 0;
        }
        .form-group {
            flex: 1;
            min-width: 200px;
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
        .stats-container {
            display: none;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
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
        .new-feature {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐛 禅道MCP阶段四功能测试</h1>
            <p>Bug管理、用户管理、模块管理 <span class="new-feature">支持用户姓名查询</span></p>
        </div>
        
        <div id="status" class="status" style="display:none;"></div>
        
        <div id="statsContainer" class="stats-container">
            <div class="stat-item">
                <div class="stat-number" id="bugCount">-</div>
                <div class="stat-label">Bug数量</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="userCount">-</div>
                <div class="stat-label">用户数量</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="moduleCount">-</div>
                <div class="stat-label">模块数量</div>
            </div>
            <div class="stat-item">
                <div class="stat-number" id="productCount">-</div>
                <div class="stat-label">产品数量</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📋 基本功能测试</h2>
            <button class="button" onclick="testConnection()">测试连接</button>
            <button class="button secondary" onclick="loadUsers()">加载用户列表</button>
            <button class="button info" onclick="loadAllData()">加载所有统计</button>
        </div>
        
        <div class="section">
            <h2>🐛 Bug查询功能 <span class="new-feature">支持用户姓名</span></h2>
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
                    <label for="bugUserRealname">🆕 用户姓名:</label>
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
            <button class="button" onclick="getModules()">查询模块列表</button>
        </div>
        
        <div class="section">
            <h2>📊 API端点列表</h2>
            <ul>
                <li><a href="/api/bugs" target="_blank">/api/bugs</a> - 获取Bug列表</li>
                <li><a href="/api/bugs?user_realname=韦家鹏" target="_blank">/api/bugs?user_realname=韦家鹏</a> - 🆕 按用户姓名查询</li>
                <li><a href="/api/users" target="_blank">/api/users</a> - 获取用户列表</li>
                <li><a href="/api/modules" target="_blank">/api/modules</a> - 获取功能模块列表</li>
                <li><a href="/api/products" target="_blank">/api/products</a> - 获取产品列表</li>
            </ul>
        </div>
        
        <div id="result" class="result">
            <h3>响应结果:</h3>
            <pre id="resultContent"></pre>
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
            if (bugs !== null) document.getElementById('bugCount').textContent = bugs || '-';
            if (users !== null) document.getElementById('userCount').textContent = users || '-';
            if (modules !== null) document.getElementById('moduleCount').textContent = modules || '-';
            if (products !== null) document.getElementById('productCount').textContent = products || '-';
            document.getElementById('statsContainer').style.display = 'grid';
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
                
                showStatus('正在查询模块列表...', 'success');
                const response = await fetch(url);
                const data = await response.json();
                
                if (data.success) {
                    showStatus(data.message, 'success');
                    updateStats(null, null, data.count, null);
                } else {
                    showStatus(`查询失败: ${data.error}`, 'error');
                }
                
                showResult(data, '模块查询');
            } catch (error) {
                showResult({error: error.message}, '模块查询');
                showStatus('查询模块失败', 'error');
            }
        }
        
        async function loadAllData() {
            try {
                showStatus('正在加载所有数据...', 'success');
                
                const [bugsRes, usersRes, modulesRes, productsRes] = await Promise.all([
                    fetch('/api/bugs?limit=10'),
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
                
                showStatus('数据加载完成', 'success');
                showResult({bugs, users, modules, products}, '全部数据');
            } catch (error) {
                showResult({error: error.message}, '数据加载');
                showStatus('数据加载失败', 'error');
            }
        }
    </script>
</body>
</html>'''

def run_server():
    """启动HTTP服务器"""
    print("🚀 启动禅道MCP阶段四功能测试服务器...")
    print("📍 访问地址: http://localhost:8082")
    print("✨ 新功能: 支持通过用户真实姓名查询Bug")
    print("🔍 示例: 查询用户'韦家鹏'相关的Bug")
    print("=" * 50)
    
    try:
        # 测试数据库连接
        if db.connect():
            print("✅ 数据库连接成功")
        else:
            print("❌ 数据库连接失败")
            return
        
        # 启动服务器
        server = HTTPServer(('localhost', 8082), StageFourHandler)
        print("🎉 服务器启动成功，按Ctrl+C停止服务")
        server.serve_forever()
        
    except KeyboardInterrupt:
        print("\n⏹️ 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    run_server()
