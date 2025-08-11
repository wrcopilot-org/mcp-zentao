# MCP-ZenTao 项目设计

## 🎯 项目概述

MCP-ZenTao 是一个将禅道（ZenTao）项目管理系统与 Model Context Protocol（MCP）结合的创新项目。通过 MCP，AI 助手可以直接与禅道系统交互，实现智能化的项目管理协作。

### 核心目标
- **信息收集阶段**：通过大量测试收集禅道 API 的请求/响应数据
- **数据建模阶段**：基于收集的数据定义结构化的数据模型
- **API 封装阶段**：创建类型安全的禅道 API 客户端
- **MCP 集成阶段**：实现 MCP 协议，让 AI 助手能够操作禅道系统

## 🏗️ 技术架构设计

### 分层架构
```
┌─────────────────────────────────┐
│        MCP Protocol Layer       │  ← AI 助手交互层
├─────────────────────────────────┤
│       Business Logic Layer      │  ← 业务逻辑封装
├─────────────────────────────────┤
│       Data Model Layer          │  ← 数据模型
├─────────────────────────────────┤
│       HTTP Client Layer         │  ← 禅道 API 客户端
├─────────────────────────────────┤
│         ZenTao REST API         │  ← 禅道系统接口
└─────────────────────────────────┘
```

### 核心模块设计

#### 1. 会话管理模块 (`session`)
- **职责**：管理禅道的会话状态和认证
- **核心功能**：
  - SessionID 获取与维护
  - 用户登录/登出
  - 会话自动续期
  - 认证状态管理

#### 2. 用户管理模块 (`user`)
- **职责**：用户相关操作
- **核心功能**：
  - 用户信息获取
  - 用户权限管理
  - 用户状态查询

#### 3. 缺陷管理模块 (`bug`) - 优先级3
- **职责**：缺陷（Bug）相关操作
- **核心功能**：
  - 缺陷查询
  - 缺陷创建/编辑
  - 缺陷解决/关闭
  - 缺陷状态跟踪

#### 4. 任务管理模块 (`task`) - 优先级4
- **职责**：任务相关操作
- **核心功能**：
  - 任务查询（我的任务、项目任务）
  - 任务创建/编辑
  - 任务状态变更（完成/关闭/取消）
  - 任务分配与转移

#### 5. 项目管理模块 (`project`) - 优先级5
- **职责**：项目相关操作
- **核心功能**：
  - 项目列表查询
  - 项目详情获取
  - 项目创建/编辑
  - 项目状态管理

## 📊 数据模型设计原则

### 结构化数据优先
遵循编程规范，使用 Pydantic 定义所有数据模型：

```python
from pydantic import BaseModel
from enum import Enum
from typing import Optional, List
from datetime import datetime

class TaskStatus(Enum):
    WAIT = "wait"
    DOING = "doing" 
    DONE = "done"
    CLOSED = "closed"
    CANCEL = "cancel"

class TaskModel(BaseModel):
    id: int
    name: str
    status: TaskStatus
    assignedTo: str
    deadline: Optional[datetime]
    project: int
    # ... 其他字段
```

### 单一数据源原则
- 枚举和常量定义在模型中，避免重复硬编码
- 验证逻辑直接引用数据定义
- 确保数据的一致性和可维护性

## 🔧 开发工具链

### 包管理
使用 `uv` 作为 Python 包管理器：
```bash
uv add pydantic      # 数据模型
uv add httpx         # HTTP 客户端
uv add pytest --optional dev  # 测试框架
```

### 项目结构
```
mcp-zentao/
├── src/
│   └── mcp_zentao/
│       ├── __init__.py
│       ├── models/          # 数据模型
│       │   ├── __init__.py
│       │   ├── session.py
│       │   ├── user.py
│       │   ├── project.py
│       │   ├── task.py
│       │   └── bug.py
│       ├── client/          # API 客户端
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── session.py
│       │   ├── user.py
│       │   ├── project.py
│       │   ├── task.py
│       │   └── bug.py
│       ├── mcp/             # MCP 协议实现
│       │   ├── __init__.py
│       │   └── server.py
│       └── main.py
├── test/                    # 测试文件
├── design/                  # 设计文档
└── examples/               # 使用示例
```

## 🚀 开发流程

### 阶段一：信息收集与建模（当前阶段）
1. **API 探索**：编写测试收集各模块的 API 数据
2. **数据建模**：基于 API 响应定义 Pydantic 模型
3. **客户端封装**：创建类型安全的 API 客户端

### 阶段二：功能实现
1. **核心功能**：实现各模块的核心业务逻辑
2. **错误处理**：完善异常处理和错误恢复机制
3. **测试覆盖**：确保代码质量和功能正确性

### 阶段三：MCP 集成
1. **协议实现**：实现 MCP 服务器
2. **工具定义**：定义 AI 助手可用的工具集
3. **集成测试**：验证 AI 助手与禅道的交互

## 📝 质量保证

### 代码质量标准
- 类型提示覆盖率 100%
- 文档字符串完整
- 遵循 SOLID 原则
- 单元测试覆盖率 > 90%

### 数据一致性检查
- [ ] 是否使用了结构化数据模型？
- [ ] 是否避免了硬编码重复？
- [ ] 数据验证是否完整？
- [ ] 是否遵循了单一数据源原则？

## 🎯 成功指标

### 技术指标
- 所有核心 API 的数据模型定义完成
- API 客户端类型安全且易用
- MCP 协议集成成功
- AI 助手能够流畅操作禅道系统

### 用户体验指标
- AI 助手能够理解和执行项目管理任务
- 响应时间 < 2秒
- 错误处理优雅，提供有用的错误信息
