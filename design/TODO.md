# MCP-ZenTao 任务清单

## 🎯 当前阶段：API 探索与数据建模

### 📋 任务安排

#### 🔥 优先级 1
- [x] **会话管理分析** - 分析现有 `test_zentao_api.py` 中的会话管理逻辑
- [x] **SessionID 数据模型** - 定义 SessionID 获取的请求/响应模型
- [x] **登录数据模型** - 定义用户登录的请求/响应模型
- [x] **运行现有测试** - 执行测试收集实际 API 响应数据

#### ⚡ 优先级 2
- [x] **项目结构优化** - 创建 `src/mcp_zentao/models/` 目录结构
- [x] **安装依赖** - 使用 uv 安装 pydantic 等必要依赖

#### 📚 优先级 3
- [x] **用户信息模型** - 开始设计用户信息的数据模型
- [x] **错误处理模型** - 设计统一的错误响应模型

### 📅 剩余任务

#### API详情收集与数据建模 ✅ **已完成**
- [x] 收集用户登出API响应数据和结构
- [x] 收集缺陷详情API完整响应数据和结构
- [x] 收集任务详情API完整响应数据和结构
- [x] 收集项目任务API完整响应数据和结构
- [x] 完善session.py中的LogoutResponse数据模型
- [x] 完善bug.py中的BugDetailResponse和BugDetailData数据模型
- [x] 完善task.py中的TaskDetailResponse和TaskDetailData数据模型
- [x] 完善project.py中的ProjectTaskResponse和ProjectTaskData数据模型
- [x] 完善project.py中的ProjectBugResponse和ProjectBugData数据模型
- [x] 创建API详情收集测试用例
- [x] 创建数据模型验证测试用例
- [x] 确保所有新模型能正确解析真实API数据

#### 会话与用户管理完善
- [x] 完善会话管理的所有数据模型
- [x] 实现用户登录/登出的完整测试用例
- [x] 收集用户信息相关的 API 响应数据
- [x] 定义用户权限和状态的枚举类型

#### 测试框架与基础设施
- [x] 建立统一的测试基础设施
- [x] 实现测试数据的 Mock 机制
- [x] 添加测试配置管理
- [x] 完善异常处理和日志记录

### 🔍 技术债务与改进点

#### 代码质量改进
- [ ] **硬编码消除** - 将测试中的硬编码账号密码移到配置文件
- [ ] **重复代码提取** - 提取公共的 HTTP 请求逻辑
- [ ] **类型安全** - 为所有函数添加类型提示
- [ ] **文档完善** - 为所有模型添加详细的 docstring (基于数据事实，避免猜测)

#### 测试改进
- [ ] **参数化测试** - 使用 pytest 的参数化功能测试多种场景
- [ ] **测试隔离** - 确保测试之间的独立性
- [ ] **性能测试** - 添加 API 响应时间的基准测试
- [ ] **错误场景** - 补充异常情况的测试用例

### 📊 数据收集清单

#### 已收集的 API 信息
- [x] **GET** `/api-getSessionID.json` - 获取会话ID
- [x] **GET** `/user-login-{sessionid}.json` - 用户登录
- [x] **GET** `/user-logout.json` - 用户登出
- [x] **GET** `/my-project.json` - 获取我的项目
- [x] **GET** `/my-task.json` - 获取我的任务
- [x] **GET** `/my-bug.json` - 获取我的缺陷

#### 待收集的 API 信息
- [x] **GET** `company-browse-{dept_id}.json` - 获取用户列表
- [x] **GET** `/bug-view-{id}.json` - 获取缺陷详情
- [x] **GET** `/task-view-{id}.json` - 获取任务详情
- [x] **GET** `/project-task-{id}.json` - 获取项目所有任务清单
- [x] **GET** `/project-bug-{id}.json` - 获取项目所有缺陷清单
<!-- 暂不支持
- [ ] **?** `/bug-create-{productID}-{branch}-moduleID={moduleID}.json` - 创建缺陷
- [ ] **?** `/task-create-{projectID}--{moduleID}.json` - 创建任务
- [ ] **?** `/project-create.json` - 创建项目
- [ ] **?** `/task-finish-{id}.json` - 完成任务
- [ ] **?** `/task-close-{id}.json` - 关闭任务
- [ ] **?** `/task-start-{id}.json` - 开始任务
- [ ] **?** `/bug-resolve-{id}.json` - 解决缺陷
- [ ] **?** `/bug-close-{id}.json` - 关闭缺陷
- [ ] **?** `/bug-confirmBug-{id}.json` - 确认缺陷
-->

### 🏗️ 架构决策记录

#### ADR-001: 数据模型技术选型
**决策**: 使用 Pydantic 作为数据建模工具
**理由**: 
- 类型安全
- 自动验证
- 序列化/反序列化支持
- 与 FastAPI 等框架兼容性好

#### ADR-002: HTTP 客户端选择
**决策**: 使用 httpx 作为 HTTP 客户端
**理由**:
- 异步支持
- 现代化的 API 设计
- 更好的性能表现
- 与 requests 兼容的接口

#### ADR-003: 测试策略
**决策**: 采用测试驱动的开发方式
**理由**:
- 先收集真实 API 数据
- 基于数据设计模型
- 确保模型的正确性
- 为后续开发提供可靠基础

### 🐛 已知问题与解决方案

#### 问题 1: 会话管理复杂性
**描述**: 禅道的会话管理需要先获取 SessionID，然后在后续请求中使用
**影响**: 所有 API 调用都需要先建立会话
**解决方案**: 
- [ ] **自动处理会话获取和维护** - 使用共享的 `httpx.Client` 实例管理Cookie
- [ ] **Cookie 自动同步机制** - 子客户端共享同一HTTP会话
- [ ] **实现统一会话管理器** - `ZenTaoClient` 类统一管理所有API访问
- [ ] **上下文管理器支持** - 支持 `with ZenTaoClient() as client:` 语法自动资源管理
- [ ] **登录状态检查** - 提供 `is_logged_in` 属性和 `ensure_logged_in()` 方法

#### 问题 2: API 响应格式不一致
**描述**: 部分 API 返回的 data 字段是 JSON 字符串而非直接的对象
**影响**: 需要额外的解析步骤
**解决方案**:
- 在数据模型中添加自定义的解析器
- 使用 Pydantic 的 validator 功能
- 统一处理这种不一致性

### 📝 学习与研究任务

#### MCP 协议研究
- [ ] **深入了解 MCP 的工具定义方式** - 使用 Semantic Kernel 的 `@kernel_function` 装饰器定义MCP工具
- [ ] **研究 MCP 的错误处理机制** - 在 `ZenTaoMCPServer` 中实现统一的错误处理和响应格式
- [ ] **分析 MCP 的异步操作支持** - 使用 `asyncio` 和 `anyio` 支持异步操作
- [ ] **设计适合禅道的 MCP 工具集** - 实现核心工具函数集合

**启动方式**:
```bash
# STDIO模式（默认）
uv run python -m mcp_zentao.sk_mcp_server --base-url "http://zentao.example.com"

# SSE服务器模式  
uv run python -m mcp_zentao.sk_mcp_server --transport sse --port 8080 --base-url "http://zentao.example.com"
```

### ✅ 完成标准

#### 数据模型完成标准
- [ ] 所有模型都有完整的类型提示
- [ ] 所有模型都有 docstring 文档
- [ ] 所有模型都通过了验证测试
- [ ] 所有枚举值都有明确的定义

#### 测试完成标准
- [ ] 每个 API 都有对应的测试用例
- [ ] 测试覆盖率达到 90% 以上
- [ ] 包含正常和异常场景的测试
- [ ] 测试可以独立运行且可重复

#### 文档完成标准
- [ ] 每个模块都有详细的说明文档
- [ ] API 使用示例完整
- [ ] 错误处理指南清晰
- [ ] 部署和配置说明完善

### 📞 协作与沟通

#### 需要用户参与的任务
- [ ] **配置信息提供** - 提供测试环境的禅道访问信息
- [ ] **业务需求确认** - 确认各模块的具体功能需求
- [ ] **测试数据准备** - 准备测试用的项目、任务、缺陷数据
- [ ] **验收标准确认** - 确认各阶段的验收标准

#### 定期同步计划
- **阶段性**: 更新任务完成状态，回顾进展，调整计划
- **里程碑**: 完成阶段性验收和规划调整

---

**最后更新**: 2025-08-07
**下次更新**: 阶段性或有重大进展时更新
