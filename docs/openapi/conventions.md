---
title: ZenTao OpenAPI 约定与命名规则
description: 路径、参数与字段的命名约定
ms.date: 2026-02-02
ms.topic: reference
keywords:
  - zentao
  - openapi
  - conventions
estimated_reading_time: 5
---

## 命名约定

* 端点名称使用 `模块.动作` 格式
* 路径使用小写与短横线组合
* 参数占位符使用花括号标记

## 字段约定

* data 字段可能是 JSON 字符串，需二次解析
* 缺省字段使用 Optional 表示

## 状态约定

* status 为 success 表示请求成功
* message 字段用于错误提示

## 变更流程

* 新端点先入未验证清单
* 补齐 request/response 样本后提升为已验证
* 端点变更必须同步更新注册表与 mock