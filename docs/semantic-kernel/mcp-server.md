---
title: Semantic Kernel MCP 服务器
description: ZenTao MCP 服务器的结构与函数注册约定
ms.date: 2026-02-02
ms.topic: reference
keywords:
  - semantic-kernel
  - mcp
  - zentao
estimated_reading_time: 7
---

## 设计要点

* 业务逻辑与输出格式分离
* 函数返回结构化数据，交由调用层渲染
* 核心函数以最小参数实现可组合能力

## 函数注册策略

* 每个功能域单独命名空间
* 使用明确的函数名避免歧义
* 注册时只暴露必要字段

## 输出结构建议

```json
{
  "status": "success",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "per_page": 20
  }
}
```

## 参考链接

* <https://github.com/microsoft/semantic-kernel/tree/main/python>
* <https://github.com/microsoft/semantic-kernel/tree/main/python/samples/demos/mcp_server>
