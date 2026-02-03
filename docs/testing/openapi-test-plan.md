---
title: OpenAPI 测试与校验方案
description: 基于 httpx mock 的 request/response 与模型对齐检查
ms.date: 2026-02-02
ms.topic: reference
keywords:
  - zentao
  - openapi
  - testing
estimated_reading_time: 6
---

## 目标

* 为每个端点提供最小 request 与 response 样本
* 通过 mock 校验模型解析与字段一致性

## 测试结构

* `test/fixtures` 存放 response 样本
* `test/samples` 存放 request 样本
* `test/httpx` 存放 mock transport
* `test/test_openapi_model_validation.py` 负责模型校验

## 规则

* 每个已验证端点至少有 1 份 response 样本
* request 样本必须反映当前客户端默认请求参数
* 如果解析失败，先修订模型，再更新样本
