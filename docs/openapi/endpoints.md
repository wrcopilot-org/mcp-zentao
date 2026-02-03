---
title: ZenTao OpenAPI 端点注册表
description: 未验证与未验证端点清单，支持持续增删改
ms.date: 2026-02-02
ms.topic: reference
keywords:
  - zentao
  - openapi
  - endpoints
estimated_reading_time: 8
---

## 端点注册表

| 名称 | 方法 | 路径模板 | 验证状态 | 备注 |
| --- | --- | --- | --- | --- |
| session.get_session_id | GET | /api-getSessionID.json | 未验证 | data 字段为 JSON 字符串 |
| session.login | GET | /user-login-{sessionid}.json | 未验证 | 参数通过 query 传递 |
| session.logout | GET | /user-logout-{sessionid}.json | 未验证 | 以代码为准 |
| user.list | GET | /company-browse-{dept_id}.json | 未验证 |  |
| project.my_list | GET | /my-project.json | 未验证 |  |
| project.task_list | GET | /project-task-{project_id}.json | 未验证 |  |
| project.bug_list | GET | /project-bug-{project_id}.json | 未验证 |  |
| task.my_list | GET | /my-task.json | 未验证 |  |
| task.detail | GET | /task-view-{task_id}.json | 未验证 |  |
| bug.my_list | GET | /my-bug.json | 未验证 |  |
| bug.detail | GET | /bug-view-{bug_id}.json | 未验证 |  |
| task.create | POST | /task-create-{project_id}--{module_id}-{sessionid}.json | 未验证 |  |
| task.start | POST | /task-start-{task_id}-{sessionid}.json | 未验证 |  |
| task.finish | POST | /task-finish-{task_id}-{sessionid}.json | 未验证 |  |
| task.close | POST | /task-close-{task_id}-{sessionid}.json | 未验证 |  |
| bug.create | POST | /bug-create-{product_id}-{branch}-moduleID={module_id}-{sessionid}.json | 未验证 |  |
| bug.resolve | POST | /bug-resolve-{bug_id}-{sessionid}.json | 未验证 |  |
| bug.confirm | POST | /bug-confirmBug-{bug_id}-{sessionid}.json | 未验证 |  |
| bug.close | POST | /bug-close-{bug_id}-{sessionid}.json | 未验证 |  |
| project.create | POST | /project-create-{sessionid}.json | 未验证 |  |
| project.close | POST | /project-close-{project_id}-{sessionid}.json | 未验证 |  |
| project.start | POST | /project-start-{project_id}-{sessionid}.json | 未验证 |  |

## 变更规则

* 新端点先进入未验证清单
* 完成 request 和 response 样本后标记为未验证
* 端点路径变更必须更新分页规则和 mock 示例
