# Semantic Kernel MCP Server 使用示例

## 功能概览

基于 Semantic Kernel 的禅道 MCP 服务器提供以下核心功能：

### 🔥 缺陷管理
- `query_bug_list` - 查询缺陷清单（支持状态筛选、数量限制、排序）
- `query_bug_detail` - 查询指定缺陷详细信息
- `query_bugs_by_status` - 按状态快速查询缺陷

### ⚡ 任务管理
- `query_task_list` - 查询任务清单（支持状态筛选、数量限制、排序）
- `query_task_detail` - 查询指定任务详细信息  
- `query_tasks_by_status` - 按状态快速查询任务

### 📊 项目管理
- `query_project_list` - 查询项目清单
- `query_project_detail` - 查询指定项目详细信息

### 🔐 会话管理
- `login` - 登录禅道系统
- `logout` - 登出禅道系统
- `get_current_user` - 获取当前用户信息

## 启动服务器

### 1. STDIO 模式（默认）
```bash
# 使用默认配置启动
python -m mcp_zentao.sk_mcp_server

# 指定禅道服务器地址
python -m mcp_zentao.sk_mcp_server --base-url http://localhost/zentao/

# 使用项目脚本
mcp-zentao --base-url http://localhost/zentao/
```

### 2. SSE 模式（HTTP 服务器）
```bash
# 启动 HTTP MCP 服务器
python -m mcp_zentao.sk_mcp_server --transport sse --port 8080 --base-url http://localhost/zentao/
```

## 功能使用示例

### 缺陷管理示例

#### 1. 查询所有缺陷
```python
# 通过 MCP 调用
result = server.query_bug_list()
print(result)
```

输出示例：
```
缺陷清单（共 15 个）
============================================================
  1. **[1001]** 登录页面无法正常显示
     状态: 🔴激活     | 严重程度: 🚨致命  
     指派给: 张三
     创建时间: 2024-01-15
     ──────────────────────────────────────────────────
  2. **[1002]** 数据导出功能异常
     状态: 🟡已解决   | 严重程度: ⚠️严重  
     指派给: 李四
     创建时间: 2024-01-14
     ──────────────────────────────────────────────────
```

#### 2. 按状态查询缺陷
```python
# 查询激活状态的缺陷，限制10条
result = server.query_bugs_by_status("active", limit=10)
print(result)
```

#### 3. 查询缺陷详情
```python
# 查询ID为1001的缺陷详情
result = server.query_bug_detail(1001)
print(result)
```

输出示例：
```
缺陷详细信息 - #1001
============================================================
📋 标题: 登录页面无法正常显示
📊 状态: 🔴激活
🎯 严重程度: 🚨致命
📦 所属产品: 用户管理系统
👤 指派给: 张三
👨‍💻 创建者: 系统管理员
📅 创建时间: 2024-01-15
⏰ 截止时间: 2024-01-20

📝 详细描述:
    ...
```

### 任务管理示例

#### 1. 查询所有任务
```python
# 查询所有任务，按最新排序
result = server.query_task_list(sort_order="latest")
print(result)
```

#### 2. 查询进行中的任务
```python
# 查询进行中的任务，限制5条
result = server.query_tasks_by_status("doing", limit=5)
print(result)
```

#### 3. 查询任务详情
```python
result = server.query_task_detail(2001)
print(result)
```

输出示例：
```
任务详细信息 - #2001
============================================================
📋 任务名称: 用户登录模块重构
📊 状态: 🔄进行中
🎯 优先级: 🔥高优先级
🏗️ 所属项目: 用户管理系统v2.0
👤 指派给: 张三
👨‍💻 创建者: 项目经理
📅 创建时间: 2024-01-10
⏰ 截止时间: 2024-01-25

⏱️ 工时信息:
   预估工时: 16 小时
   已用工时: 8 小时
   剩余工时: 8 小时
   完成进度: 50.0%

📝 详细描述:
    ...
```

### 会话管理示例

```python
# 登录
result = server.login("username", "password")
print(result)  # 输出：登录成功！欢迎，张三（zhangsan）

# 获取当前用户
result = server.get_current_user()
print(result)  # 输出：当前用户：张三（zhangsan），邮箱：zhang@example.com，角色：developer

# 登出
result = server.logout()
print(result)  # 输出：用户 zhangsan 已成功登出
```

## 参数说明

### 缺陷管理参数

#### query_bug_list
- `status`: 状态筛选（"all"默认, "active", "resolved", "closed"）
- `limit`: 数量限制（0表示全部，默认）
- `sort_order`: 排序方式（"latest"默认, "oldest", "priority"）

#### query_bugs_by_status
- `status`: 缺陷状态（"active", "resolved", "closed"）
- `limit`: 数量限制（默认10）

### 任务管理参数

#### query_task_list
- `status`: 状态筛选（"all"默认, "wait", "doing", "done", "closed"）
- `limit`: 数量限制（0表示全部，默认）
- `sort_order`: 排序方式（"latest"默认, "oldest", "deadline"）

#### query_tasks_by_status
- `status`: 任务状态（"wait", "doing", "done", "closed"）
- `limit`: 数量限制（默认10）

## 分页机制

- **默认行为**: 当 `limit=0` 时，自动获取所有页面数据
- **分页设置**: 每页50条记录，最多获取20页（防止数据过多）
- **限制模式**: 当指定 `limit>0` 时，只获取指定数量的记录
- **性能优化**: 对于大量数据，建议使用限制模式避免超时

## 错误处理

服务器包含完善的错误处理机制：

1. **认证错误**: 未登录时会提示先登录
2. **数据错误**: 找不到数据时会给出友好提示
3. **网络错误**: 请求失败时会显示具体错误信息
4. **参数错误**: 无效参数会被自动处理或提示

## 扩展和自定义

如需扩展功能，可以：

1. 继承 `ZenTaoMCPServer` 类
2. 添加新的 `@kernel_function` 装饰的方法
3. 在 `_register_functions` 中注册新功能
4. 重新编译和部署

## 技术细节

- **框架**: Semantic Kernel + MCP Protocol
- **传输**: 支持 STDIO 和 SSE (HTTP) 两种模式
- **数据模型**: 基于 Pydantic 的类型安全数据模型
- **客户端**: 统一的禅道 API 客户端封装
- **日志**: 结构化日志记录，便于调试和监控
