import anyio
import click
import pymysql
import json
from typing import List, Dict, Any
import mcp.types as types
from mcp.server.lowlevel import Server


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
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def get_products(self) -> List[Dict[str, Any]]:
        """获取产品列表"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor() as cursor:
                sql = """
                SELECT id, name, code, PO, QD, createdBy, createdDate 
                FROM zt_product 
                WHERE deleted = '0'
                ORDER BY id
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
                
                return products
        except Exception as e:
            print(f"查询产品列表失败: {e}")
            return []
    
    def get_projects_by_product_name(self, product_name: str) -> List[Dict[str, Any]]:
        """通过产品名获取产品相关的项目"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor() as cursor:
                # 首先通过产品名获取产品ID
                product_sql = """
                SELECT id FROM zt_product 
                WHERE name = %s AND deleted = '0'
                """
                cursor.execute(product_sql, (product_name,))
                product_result = cursor.fetchone()
                
                if not product_result:
                    return []
                
                product_id = product_result[0]
                
                # 然后通过产品ID从关联表获取项目ID，再查询项目详情
                project_sql = """
                SELECT DISTINCT 
                    p.id, p.name, p.code, p.begin, p.end, p.status, p.PO, p.PM, p.QD
                FROM zt_project p
                INNER JOIN zt_projectproduct pp ON p.id = pp.project
                WHERE pp.product = %s AND p.deleted = '0'
                ORDER BY p.id
                """
                cursor.execute(project_sql, (product_id,))
                results = cursor.fetchall()
                
                projects = []
                for row in results:
                    project = {
                        'id': row[0],  # 项目唯一编号
                        'name': row[1],  # 项目名称
                        'code': row[2],  # 项目缩写名
                        'begin': str(row[3]) if row[3] else None,  # 项目开始时间
                        'end': str(row[4]) if row[4] else None,  # 项目结束时间
                        'status': row[5],  # 项目运行状态
                        'PO': row[6],  # 产品经理
                        'PM': row[7],  # 项目经理
                        'QD': row[8],  # 测试主管
                        'product_id': product_id,  # 关联的产品ID
                        'product_name': product_name  # 产品名称
                    }
                    projects.append(project)
                
                return projects
                
        except Exception as e:
            print(f"查询项目列表失败: {e}")
            return []
    
    def get_product_by_name(self, product_name: str) -> Dict[str, Any]:
        """通过产品名获取产品信息"""
        if not self.connection:
            if not self.connect():
                return {}
        
        try:
            with self.connection.cursor() as cursor:
                sql = """
                SELECT id, name, code, PO, QD, createdBy, createdDate 
                FROM zt_product 
                WHERE name = %s AND deleted = '0'
                """
                cursor.execute(sql, (product_name,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'name': result[1],
                        'code': result[2],
                        'PO': result[3],
                        'QD': result[4],
                        'createdBy': result[5],                    'createdDate': str(result[6]) if result[6] else None
                    }
                return {}
                
        except Exception as e:
            print(f"查询产品信息失败: {e}")
            return {}
    
    def get_bugs(self, limit: int = 50, product_id: int = None, project_id: int = None, 
                 status: str = None, user_realname: str = None) -> List[Dict[str, Any]]:
        """获取bug列表"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor() as cursor:
                # 如果指定了用户真实姓名，先查找对应的account
                user_account = None
                if user_realname:
                    user_sql = "SELECT account FROM zt_user WHERE realname = %s"
                    cursor.execute(user_sql, (user_realname,))
                    user_result = cursor.fetchone()
                    if user_result:
                        user_account = user_result[0]
                    else:
                        # 如果没有找到对应的用户，返回空结果
                        return []
                
                # 构建查询条件
                where_conditions = ["b.deleted = '0'"]
                params = []
                
                if product_id:
                    where_conditions.append("b.product = %s")
                    params.append(product_id)
                
                if project_id:
                    where_conditions.append("b.project = %s")
                    params.append(project_id)
                
                if status:
                    where_conditions.append("b.status = %s")
                    params.append(status)
                
                # 如果指定了用户账号，添加相关条件（查找该用户参与的所有bug）
                if user_account:
                    user_conditions = [
                        "b.openedBy = %s",
                        "b.assignedTo = %s", 
                        "b.resolvedBy = %s",
                        "b.closedBy = %s"
                    ]
                    where_conditions.append(f"({' OR '.join(user_conditions)})")
                    # 为每个用户条件添加相同的参数
                    params.extend([user_account, user_account, user_account, user_account])
                
                where_clause = " AND ".join(where_conditions)
                
                # 主查询 - 包含用户信息和模块信息的JOIN
                sql = f"""
                SELECT 
                    b.id, b.product, b.project, b.module, b.title, b.severity, b.pri,
                    b.steps, b.status, b.openedBy, b.openedDate, b.assignedTo, b.assignedDate,
                    b.resolvedBy, b.resolvedDate, b.closedBy, b.closedDate,
                    p.name as product_name,
                    proj.name as project_name,
                    m.name as module_name,
                    u_opened.realname as opened_by_name,
                    u_assigned.realname as assigned_to_name,
                    u_resolved.realname as resolved_by_name,
                    u_closed.realname as closed_by_name
                FROM zt_bug b
                LEFT JOIN zt_product p ON b.product = p.id
                LEFT JOIN zt_project proj ON b.project = proj.id
                LEFT JOIN zt_module m ON b.module = m.id
                LEFT JOIN zt_user u_opened ON b.openedBy = u_opened.account
                LEFT JOIN zt_user u_assigned ON b.assignedTo = u_assigned.account
                LEFT JOIN zt_user u_resolved ON b.resolvedBy = u_resolved.account
                LEFT JOIN zt_user u_closed ON b.closedBy = u_closed.account
                WHERE {where_clause}
                ORDER BY b.id DESC
                LIMIT %s
                """
                
                params.append(limit)
                cursor.execute(sql, params)
                results = cursor.fetchall()
                
                bugs = []
                for row in results:
                    bug = {
                        'id': row[0],  # bug唯一编号
                        'product': row[1],  # bug对应的产品ID
                        'project': row[2],  # bug对应的项目ID
                        'module': row[3],  # bug对应的功能模块ID
                        'title': row[4],  # bug标题描述
                        'severity': row[5],  # bug严重程度
                        'pri': row[6],  # bug需要处理的优先级
                        'steps': row[7],  # bug产生的过程描述
                        'status': row[8],  # bug的状态
                        'openedBy': row[9],  # 修改status为Open的人员
                        'openedDate': str(row[10]) if row[10] else None,  # 修改status为Open的时间
                        'assignedTo': row[11],  # 当前负责人
                        'assignedDate': str(row[12]) if row[12] else None,  # 最近的指派时间
                        'resolvedBy': row[13],  # 解决bug的人员
                        'resolvedDate': str(row[14]) if row[14] else None,  # 解决的时间
                        'closedBy': row[15],  # 关闭bug的人员
                        'closedDate': str(row[16]) if row[16] else None,  # 关闭bug的时间
                        # 关联信息
                        'product_name': row[17],  # 产品名称
                        'project_name': row[18],  # 项目名称
                        'module_name': row[19],  # 模块名称
                        'opened_by_name': row[20],  # 开启人真实姓名
                        'assigned_to_name': row[21],  # 指派人真实姓名
                        'resolved_by_name': row[22],  # 解决人真实姓名
                        'closed_by_name': row[23]  # 关闭人真实姓名
                    }
                    bugs.append(bug)
                
                return bugs
                
        except Exception as e:
            print(f"查询bug列表失败: {e}")
            return []
    
    def get_users(self) -> List[Dict[str, Any]]:
        """获取用户列表"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor() as cursor:
                sql = """
                SELECT account, realname, role
                FROM zt_user 
                WHERE deleted = '0'
                ORDER BY account
                """
                cursor.execute(sql)
                results = cursor.fetchall()
                
                users = []
                for row in results:
                    user = {
                        'account': row[0],  # 人员全局唯一标识
                        'realname': row[1],  # 人员真实姓名
                        'role': row[2]  # 人员职位
                    }
                    users.append(user)
                
                return users
                
        except Exception as e:
            print(f"查询用户列表失败: {e}")
            return []
    
    def get_modules(self, product_id: int = None) -> List[Dict[str, Any]]:
        """获取功能模块列表"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            with self.connection.cursor() as cursor:
                sql = """
                SELECT id, name, root
                FROM zt_module 
                WHERE deleted = '0'
                """
                params = []
                
                if product_id:
                    sql += " AND root = %s"
                    params.append(product_id)
                
                sql += " ORDER BY id"
                
                cursor.execute(sql, params)
                results = cursor.fetchall()
                
                modules = []
                for row in results:
                    module = {
                        'id': row[0],  # 全局唯一标识
                        'name': row[1],  # 功能模块名称
                        'root': row[2]  # 所属产品ID
                    }
                    modules.append(module)
                
                return modules
                
        except Exception as e:
            print(f"查询模块列表失败: {e}")
            return []
    
# 全局数据库实例
db = ZentaoDatabase()


async def get_zentao_products() -> list[types.ContentBlock]:
    """获取禅道产品列表"""
    products = db.get_products()
    
    if not products:
        return [types.TextContent(
            type="text", 
            text="无法获取产品列表，请检查数据库连接"
        )]
    
    # 格式化产品信息
    product_text = "禅道产品列表:\n\n"
    for product in products:
        product_text += f"产品ID: {product['id']}\n"
        product_text += f"产品名: {product['name']}\n"
        product_text += f"产品缩写: {product['code']}\n"
        product_text += f"产品经理: {product['PO']}\n"
        product_text += f"测试主管: {product['QD']}\n"
        product_text += f"创建人: {product['createdBy']}\n"
        product_text += f"创建日期: {product['createdDate']}\n"
        product_text += "-" * 40 + "\n"
    
    # 同时返回JSON格式的数据
    json_data = json.dumps(products, ensure_ascii=False, indent=2)
    
    return [
        types.TextContent(type="text", text=product_text),
        types.TextContent(type="text", text=f"JSON格式数据:\n{json_data}")
    ]


async def get_projects_by_product(product_name: str) -> list[types.ContentBlock]:
    """通过产品名获取产品相关的项目"""
    if not product_name:
        return [types.TextContent(
            type="text", 
            text="错误：产品名称不能为空"
        )]
    
    # 获取产品信息
    product = db.get_product_by_name(product_name)
    if not product:
        return [types.TextContent(
            type="text", 
            text=f"错误：未找到名为 '{product_name}' 的产品"
        )]
    
    # 获取相关项目
    projects = db.get_projects_by_product_name(product_name)
    
    if not projects:
        return [types.TextContent(
            type="text", 
            text=f"产品 '{product_name}' 当前没有关联的项目"
        )]
    
    # 格式化项目信息
    project_text = f"产品 '{product_name}' 的相关项目:\n\n"
    project_text += f"产品信息:\n"
    project_text += f"  产品ID: {product['id']}\n"
    project_text += f"  产品名: {product['name']}\n"
    project_text += f"  产品缩写: {product['code']}\n"
    project_text += f"  产品经理: {product['PO']}\n"
    project_text += f"  测试主管: {product['QD']}\n"
    project_text += "\n" + "=" * 50 + "\n"
    project_text += f"关联项目列表 (共 {len(projects)} 个):\n\n"
    
    for i, project in enumerate(projects, 1):
        project_text += f"项目 {i}:\n"
        project_text += f"  项目ID: {project['id']}\n"
        project_text += f"  项目名称: {project['name']}\n"
        project_text += f"  项目缩写: {project['code']}\n"
        project_text += f"  开始时间: {project['begin']}\n"
        project_text += f"  结束时间: {project['end']}\n"
        project_text += f"  运行状态: {project['status']}\n"
        project_text += f"  产品经理: {project['PO']}\n"
        project_text += f"  项目经理: {project['PM']}\n"
        project_text += f"  测试主管: {project['QD']}\n"
        project_text += "-" * 40 + "\n"
    
    # 返回结果数据
    result_data = {
        "product": product,
        "projects": projects,
        "total_projects": len(projects)
    }
    json_data = json.dumps(result_data, ensure_ascii=False, indent=2)
    
    return [
        types.TextContent(type="text", text=project_text),
        types.TextContent(type="text", text=f"JSON格式数据:\n{json_data}")
    ]


async def get_zentao_bugs(arguments: dict) -> list[types.ContentBlock]:
    """获取禅道bug列表"""
    # 解析参数
    limit = arguments.get("limit", 50)
    product_id = arguments.get("product_id")
    project_id = arguments.get("project_id")
    status = arguments.get("status")
    user_realname = arguments.get("user_realname")  # 新增：用户真实姓名参数
    
    # 验证参数
    if limit <= 0 or limit > 200:
        limit = 50
    
    # 获取bug列表
    bugs = db.get_bugs(limit=limit, product_id=product_id, project_id=project_id, 
                       status=status, user_realname=user_realname)
    
    if not bugs:
        return [types.TextContent(
            type="text", 
            text="没有找到符合条件的bug记录"
        )]
    
    # 格式化bug信息
    bug_text = f"禅道Bug列表 (共 {len(bugs)} 个):\n\n"
    
    # 添加筛选条件说明
    filter_info = []
    if product_id:
        filter_info.append(f"产品ID: {product_id}")
    if project_id:
        filter_info.append(f"项目ID: {project_id}")
    if status:
        filter_info.append(f"状态: {status}")
    if user_realname:
        filter_info.append(f"相关人员: {user_realname}")
    if limit:
        filter_info.append(f"限制: {limit}条")
    
    if filter_info:
        bug_text += f"筛选条件: {', '.join(filter_info)}\n"
        bug_text += "=" * 60 + "\n\n"
    
    for i, bug in enumerate(bugs, 1):
        bug_text += f"Bug {i}:\n"
        bug_text += f"  ID: {bug['id']}\n"
        bug_text += f"  标题: {bug['title']}\n"
        bug_text += f"  产品: {bug['product_name']} (ID: {bug['product']})\n"
        bug_text += f"  项目: {bug['project_name']} (ID: {bug['project']})\n"
        bug_text += f"  模块: {bug['module_name']} (ID: {bug['module']})\n"
        bug_text += f"  严重程度: {bug['severity']}\n"
        bug_text += f"  优先级: {bug['pri']}\n"
        bug_text += f"  状态: {bug['status']}\n"
        bug_text += f"  开启人: {bug['opened_by_name']} ({bug['openedBy']}) - {bug['openedDate']}\n"
        if bug['assignedTo']:
            bug_text += f"  指派给: {bug['assigned_to_name']} ({bug['assignedTo']}) - {bug['assignedDate']}\n"
        if bug['resolvedBy']:
            bug_text += f"  解决人: {bug['resolved_by_name']} ({bug['resolvedBy']}) - {bug['resolvedDate']}\n"
        if bug['closedBy']:
            bug_text += f"  关闭人: {bug['closed_by_name']} ({bug['closedBy']}) - {bug['closedDate']}\n"
        if bug['steps']:
            # 限制步骤描述的长度
            steps_preview = bug['steps'][:200] + "..." if len(bug['steps']) > 200 else bug['steps']
            bug_text += f"  重现步骤: {steps_preview}\n"
        bug_text += "-" * 50 + "\n"
      # 返回结果数据
    result_data = {
        "bugs": bugs,
        "total_bugs": len(bugs),
        "filters": {
            "limit": limit,
            "product_id": product_id,
            "project_id": project_id,
            "status": status,
            "user_realname": user_realname
        }
    }
    json_data = json.dumps(result_data, ensure_ascii=False, indent=2)
    
    return [
        types.TextContent(type="text", text=bug_text),
        types.TextContent(type="text", text=f"JSON格式数据:\n{json_data}")
    ]


async def get_zentao_users() -> list[types.ContentBlock]:
    """获取禅道用户列表"""
    users = db.get_users()
    
    if not users:
        return [types.TextContent(
            type="text", 
            text="无法获取用户列表，请检查数据库连接"
        )]
    
    # 格式化用户信息
    user_text = f"禅道用户列表 (共 {len(users)} 个):\n\n"
    for i, user in enumerate(users, 1):
        user_text += f"用户 {i}:\n"
        user_text += f"  账号: {user['account']}\n"
        user_text += f"  姓名: {user['realname']}\n"
        user_text += f"  角色: {user['role']}\n"
        user_text += "-" * 30 + "\n"
    
    # 返回结果数据
    json_data = json.dumps(users, ensure_ascii=False, indent=2)
    
    return [
        types.TextContent(type="text", text=user_text),
        types.TextContent(type="text", text=f"JSON格式数据:\n{json_data}")
    ]


async def get_zentao_modules(arguments: dict) -> list[types.ContentBlock]:
    """获取禅道功能模块列表"""
    product_id = arguments.get("product_id")
    
    modules = db.get_modules(product_id=product_id)
    
    if not modules:
        filter_text = f"产品ID {product_id} " if product_id else ""
        return [types.TextContent(
            type="text", 
            text=f"没有找到{filter_text}的功能模块"
        )]
    
    # 格式化模块信息
    filter_text = f" (产品ID: {product_id})" if product_id else ""
    module_text = f"功能模块列表{filter_text} (共 {len(modules)} 个):\n\n"
    
    for i, module in enumerate(modules, 1):
        module_text += f"模块 {i}:\n"
        module_text += f"  ID: {module['id']}\n"
        module_text += f"  名称: {module['name']}\n"
        module_text += f"  所属产品: {module['root']}\n"
        module_text += "-" * 30 + "\n"
    
    # 返回结果数据
    result_data = {
        "modules": modules,
        "total_modules": len(modules),
        "product_id": product_id
    }
    json_data = json.dumps(result_data, ensure_ascii=False, indent=2)
    
    return [
        types.TextContent(type="text", text=module_text),
        types.TextContent(type="text", text=f"JSON格式数据:\n{json_data}")
    ]
@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="sse",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    """主函数，启动MCP服务器"""
    app = Server("zentao-mcp-server")

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
        """处理工具调用"""
        if name == "list_products":
            return await get_zentao_products()
        elif name == "get_projects_by_product":
            product_name = arguments.get("product_name", "")
            return await get_projects_by_product(product_name)
        elif name == "get_bugs":
            return await get_zentao_bugs(arguments)
        elif name == "list_users":
            return await get_zentao_users()
        elif name == "list_modules":
            return await get_zentao_modules(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """列出可用的工具"""
        return [
            types.Tool(
                name="list_products",
                title="禅道产品列表",
                description="获取禅道系统中所有产品的列表，包括产品ID、名称、负责人等信息",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
            ),
            types.Tool(
                name="get_projects_by_product",
                title="通过产品名获取项目",
                description="根据产品名称获取相关的项目列表，包括项目ID、名称、负责人等信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "产品名称"
                        }
                    },
                    "required": ["product_name"]
                },
            ),            types.Tool(
                name="get_bugs",
                title="获取Bug列表",
                description="获取禅道系统中Bug的列表，包括Bug ID、标题、状态、指派人等信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "返回记录的数量，最大值200",
                            "default": 50
                        },
                        "product_id": {
                            "type": "integer",
                            "description": "按产品ID过滤"
                        },
                        "project_id": {
                            "type": "integer",
                            "description": "按项目ID过滤"
                        },
                        "status": {
                            "type": "string",
                            "description": "按状态过滤"
                        },
                        "user_realname": {
                            "type": "string",
                            "description": "按用户真实姓名过滤，查找该用户相关的所有bug（开启、指派、解决、关闭）"
                        }
                    },
                    "required": []
                },
            ),
            types.Tool(
                name="list_users",
                title="获取用户列表",
                description="获取禅道系统中用户的列表，包括用户账号、姓名、角色等信息",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                },
            ),
            types.Tool(
                name="list_modules",
                title="获取模块列表",
                description="获取禅道系统中功能模块的列表，包括模块ID、名称、所属产品等信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "integer",
                            "description": "按产品ID过滤"
                        }
                    },
                    "required": []
                },
            )
        ]    # 启动时连接数据库
    if not db.connect():
        print("警告: 数据库连接失败，服务器仍会启动，但功能可能受限")

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.responses import Response, PlainTextResponse
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
            return Response()

        async def handle_root(request):
            """处理根路径请求"""
            return PlainTextResponse("Zentao MCP Server is running. Use SSE endpoint for connections.")

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/", endpoint=handle_sse, methods=["GET"]),  # 根路径作为主要SSE端点
                Route("/sse", endpoint=handle_sse, methods=["GET"]),  # 备用SSE端点
                Route("/status", endpoint=handle_root, methods=["GET"]),  # 状态检查端点
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        print(f"启动禅道MCP服务器 (SSE模式) 在端口 {port}")
        print(f"主要SSE端点: http://127.0.0.1:{port}/")
        print(f"备用SSE端点: http://127.0.0.1:{port}/sse")
        print(f"状态检查端点: http://127.0.0.1:{port}/status")
        uvicorn.run(starlette_app, host="127.0.0.1", port=port)
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        print("启动禅道MCP服务器 (STDIO模式)")
        anyio.run(arun)

    # 服务器关闭时断开数据库连接
    db.disconnect()
    return 0


if __name__ == "__main__":
    import sys
    sys.argv = ['zentao_mcp_server.py', '--port', '8000', '--transport', 'sse']    
    main()
