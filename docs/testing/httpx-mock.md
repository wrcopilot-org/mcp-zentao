---
title: httpx Mock 规范
description: 用于 ZenTao OpenAPI 的 request 和 response 样本约定
ms.date: 2026-02-02
ms.topic: how-to
keywords:
  - httpx
  - mock
  - testing
estimated_reading_time: 6
---

## 目标

* 为每个端点保存最小可复现的 request 与 response
* 作为 AI 协作时的接口理解依据

## 样本结构

* request
  * method
  * url
  * params
  * json
  * headers
* response
  * status_code
  * json

## 示例

```json
{
  "request": {
    "method": "GET",
    "url": "http://zentao.example.com/api-getSessionID.json",
    "params": {},
    "json": null,
    "headers": {
      "Accept": "application/json"
    }
  },
  "response": {
    "status_code": 200,
    "json": {
      "status": "success",
      "data": "{\"sessionID\":\"abc\"}"
    }
  }
}
```

## 最小要求

* 已验证端点必须至少 1 组样本
* 未验证端点可以先保留空样本占位
* URL 需要保留占位符可替换
