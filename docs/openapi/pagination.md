---
title: ZenTao 分页规则
description: 分页 URL 规则与参数语义说明
ms.date: 2026-02-02
ms.topic: reference
keywords:
  - zentao
  - pagination
  - openapi
estimated_reading_time: 6
---

## 基础形态

* 列表端点基础形式为 `{base_endpoint}.json`
* 非第一页使用复合 URL 形式

## 复合 URL 模板

`{base_endpoint}-{operation}-{sort_key}-{rec_total}-{rec_per_page}-{page_id}.json`

## 参数说明

* base_endpoint: 列表端点标识，如 my-task、my-bug
* operation: 业务维度，如 assignedTo、openedBy、finishedBy
* sort_key: 排序键，如 id_desc、deadline_desc
* rec_total: 总记录数
* rec_per_page: 每页数量
* page_id: 页码，从 1 开始

## 示例

* my-task-assignedTo-id_desc-301-20-2.json
* my-bug-assignedTo-id_desc-305-20-2.json

## 约束

* 在获取第二页之前必须先获取第一页以确定 rec_total
* rec_total 应与服务端返回一致
