# Zentao MCP Server

禅道（Zentao）项目管理系统的 MCP (Model Context Protocol) 服务器实现。

## 项目概述

本项目实现了一个MCP服务器，用于连接禅道项目管理系统的MySQL数据库，提供产品信息查询、项目关联查询等功能。

## 功能特性

### 阶段一 ✅
- [x] 实现基础的MCP服务器框架
- [x] 支持SSE和STDIO两种传输协议
- [x] 连接MySQL数据库（禅道数据库）
- [x] 基础的错误处理和连接管理

### 阶段二 ✅
- [x] 从`zt_product`表获取产品信息
- [x] 提供MCP接口枚举产品列表
- [x] 字段映射：
  - `id`: 产品唯一编号
  - `name`: 产品名
  - `code`: 产品缩写名
  - `PO`: 负责的产品经理
  - `QD`: 负责的测试主管
  - `createdBy`: 此记录的创建人
  - `createdDate`: 此记录的创建日期
- [x] 返回符合MCP标准的数据格式

### 阶段三 ✅ 新增
- [x] 通过产品名获取产品相关的项目
- [x] 从`zt_project`和`zt_projectproduct`表获取项目信息
- [x] 项目字段映射：
  - `id`: 项目唯一编号
  - `name`: 项目名称
  - `code`: 项目缩写名
  - `begin`: 项目开始时间
  - `end`: 项目结束时间
  - `status`: 项目运行状态
  - `PO`: 产品经理
  - `PM`: 项目经理
  - `QD`: 测试主管
- [x] 多表JOIN查询优化
- [x] 完善的参数验证和错误处理

### 阶段四 ✅ 新增
- [x] 获取Bug列表功能
- [x] 从`zt_bug`、`zt_user`、`zt_module`表获取完整Bug信息
- [x] Bug字段映射：
  - `id`: bug唯一编号
  - `product`: bug对应的产品
  - `project`: bug对应的项目
  - `module`: bug对应的功能模块
  - `title`: bug标题描述
  - `severity`: bug严重程度
  - `pri`: bug需要处理的优先级
  - `steps`: bug产生的过程描述
  - `status`: bug的状态
  - `openedBy/assignedTo/resolvedBy/closedBy`: 相关责任人
  - `openedDate/assignedDate/resolvedDate/closedDate`: 相关时间
- [x] 用户信息管理 (account、realname、role)
- [x] 功能模块管理 (id、name)
- [x] 复杂多表JOIN查询优化
- [x] 支持多条件筛选 (产品、项目、状态、数量限制)
- [x] 完整的人员信息关联

## 项目结构

```
zentao-mcp/
├── src/
│   └── zentao_mcp_server.py      # 主要的MCP服务器代码
├── test/
│   ├── test_zentao_database.py   # 数据库连接测试
│   └── test_zentao_mcp.py        # MCP功能测试
├── requirements.txt               # Python依赖包
├── start_zentao_mcp.bat          # 启动脚本
├── test_zentao.bat               # 测试脚本
└── README_ZENTAO.md              # 项目文档
```

## 安装和运行

### 环境要求

- Python 3.8+
- MySQL数据库（禅道系统）
- 网络连接到禅道数据库

### 安装依赖

```bash
pip install -r requirements.txt
```

### 数据库配置

默认配置：
- 主机: 192.168.2.84
- 端口: 3306
- 用户名: dev
- 密码: 123456
- 数据库: zentao
- 字符集: utf8

### 启动服务器

#### 方式一：使用脚本启动
```bash
# Windows
start_zentao_mcp.bat
```

#### 方式二：直接运行
```bash
# SSE模式（推荐）
python src/zentao_mcp_server.py --port 8000 --transport sse

# STDIO模式
python src/zentao_mcp_server.py --transport stdio
```

### 运行测试

```bash
# Windows
test_zentao.bat

# 或直接运行
python test/test_zentao_database.py
python test/test_zentao_mcp.py
pytest test/test_zentao_database.py -v
```

## 使用方法

### 可用工具

#### 1. list_products
获取禅道系统中所有产品的列表。

**输入参数**: 无

**返回格式**: 
- 文本格式的产品列表
- JSON格式的产品数据

**示例返回**:
```
禅道产品列表:

产品ID: 1
产品名: 示例产品
产品缩写: DEMO
产品经理: admin
测试主管: tester
创建人: admin
创建日期: 2024-01-01 10:00:00
----------------------------------------
```

#### 2. get_projects_by_product 🆕
通过产品名获取产品相关的项目列表。

**输入参数**: 
- `product_name` (string, 必需): 产品名称

**返回格式**:
- 产品信息和相关项目列表
- JSON格式的完整数据

**示例调用**:
```json
{
  "name": "get_projects_by_product",
  "arguments": {
    "product_name": "示例产品"
  }
}
```

**示例返回**:
```
产品 '示例产品' 的相关项目:

产品信息:
  产品ID: 1
  产品名: 示例产品
  产品缩写: DEMO
  产品经理: admin
  测试主管: tester

==================================================
关联项目列表 (共 2 个):

项目 1:
  项目ID: 1
  项目名称: 示例项目A
  项目缩写: PROJ_A
  开始时间: 2024-01-01
  结束时间: 2024-12-31
  运行状态: doing
  产品经理: admin
  项目经理: pm001
  测试主管: tester
----------------------------------------
```

#### 3. get_bugs 🆕
获取禅道系统中的Bug列表。

**输入参数**: 
- `limit` (integer, 可选): 返回记录数量，默认50，最大200
- `product_id` (integer, 可选): 按产品ID过滤
- `project_id` (integer, 可选): 按项目ID过滤
- `status` (string, 可选): 按状态过滤
- `user_realname` (string, 可选): 🆕 按用户真实姓名过滤，查找该用户相关的所有bug（开启、指派、解决、关闭）

**返回格式**:
- Bug详细信息列表，包含关联的产品、项目、模块、人员信息
- JSON格式的完整数据

**示例调用**:
```json
{
  "name": "get_bugs",
  "arguments": {
    "limit": 20,
    "status": "active",
    "product_id": 1
  }
}
```

**🆕 按用户姓名查询示例**:
```json
{
  "name": "get_bugs",
  "arguments": {
    "limit": 20,
    "user_realname": "韦家鹏"
  }
}
```

**示例返回**:
```
禅道Bug列表 (共 5 个):

筛选条件: 产品ID: 1, 状态: active, 限制: 20条
============================================================

Bug 1:
  ID: 123
  标题: 登录页面验证失败
  产品: 示例产品 (ID: 1)
  项目: 示例项目 (ID: 1) 
  模块: 登录模块 (ID: 5)
  严重程度: 2
  优先级: 3
  状态: active
  开启人: 测试人员 (tester01) - 2024-01-15 09:30:00
  指派给: 开发人员 (dev01) - 2024-01-15 10:00:00
  重现步骤: 1. 打开登录页面 2. 输入错误密码...
--------------------------------------------------
```

#### 4. list_users 🆕
获取禅道系统中的用户列表。

**输入参数**: 无

**返回格式**: 用户账号、真实姓名、角色信息

#### 5. list_modules 🆕
获取禅道系统中的功能模块列表。

**输入参数**: 
- `product_id` (integer, 可选): 按产品ID过滤

**返回格式**: 模块ID、名称、所属产品信息

### API端点

当使用SSE模式时，服务器提供以下端点：

- **SSE连接**: `http://127.0.0.1:8000/sse`
- **消息处理**: `http://127.0.0.1:8000/messages/`

## 开发说明

### 数据库连接

`ZentaoDatabase` 类负责管理与禅道数据库的连接：

```python
db = ZentaoDatabase(
    host='192.168.2.84',
    port=3306,
    user='dev',
    password='123456',
    database='zentao',
    charset='utf8'
)
```

### 添加新功能

要添加新的MCP工具，需要：

1. 在 `call_tool` 函数中添加新的工具处理逻辑
2. 在 `list_tools` 函数中注册新工具
3. 实现相应的数据库查询函数

### 错误处理

项目包含完善的错误处理机制：
- 数据库连接失败时的重试逻辑
- SQL查询异常的捕获和处理
- MCP协议错误的标准化返回

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查网络连接
   - 验证数据库凭据
   - 确认MySQL服务运行状态

2. **MCP服务器启动失败**
   - 检查端口是否被占用
   - 验证Python依赖包安装
   - 查看详细错误日志

3. **数据查询返回空**
   - 确认数据库中有数据
   - 检查SQL查询条件
   - 验证表结构是否匹配

### 调试模式

启动时添加调试信息：
```python
# 在服务器代码中启用调试模式
app = Server("zentao-mcp-server", debug=True)
```

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 许可证

本项目采用MIT许可证。
