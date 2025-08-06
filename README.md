# Zentao MCP Server

这是一个为Zentao项目管理系统实现的MCP (Model Context Protocol) 服务器。

## 功能

- 连接Zentao MySQL数据库
- 提供产品信息查询工具
- 符合MCP协议规范

## 安装

```bash
pip install -r requirements.txt
```

## 使用

运行MCP服务器:
```bash
python src/server.py
```

## 可用工具

1. `get_products` - 获取产品列表
2. `get_product_by_id` - 根据ID获取特定产品信息

## 数据库配置

服务器连接到以下数据库:
- 主机: 192.168.2.84
- 端口: 3306
- 用户: dev
- 数据库: zentao

## 数据字段映射

从zt_product表获取的字段映射为:
- id → 产品唯一编号
- name → 产品名
- code → 产品缩写名
- PO → 负责的产品经理
- QD → 负责的测试主管
- createdBy → 此记录的创建人
- createdDate → 此记录的创建日期