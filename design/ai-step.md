# zentao-mcp 项目开发与规划
## 整体规划
### 实现AI的一个MCP server，参考.\examples\servers\simple-tool\mcp_simple_tool\server.py。完成sse协议的mcp server.
### 用python编码，代码生成在./src, 测试代码生成在./test

### 阶段一
**目标**： 连接mysql数据库，代码如下：
pymysql.connect(host='192.168.2.84', port=3306,user='dev', passwd='123456', db='zentao', charset='utf8')

### 阶段二
**目标**： 从表zt_product获取字段,提供mcp枚举产品的接口。
#### 数据表：zt_product
#### 字段及自然名映射：
#### id: 产品唯一编号
#### name: 产品名
#### code: 产品缩写名
#### PO: 负责的产品经理
#### QD: 负责的测试主管
#### createdBy: 此记录的创建人
#### createdDate: 此记录的创建日期
#### 返回数据符合MCP要求

### 阶段三
**目标**： 通过产品名获取产品相关的项目。
#### 项目信息数据表：zt_project
##### 字段及自然名映射：
##### id: 项目唯一编号
##### name: 项目名称
##### code: 项目缩写名
##### begin: 项目开始时间
##### end: 项目结束时间
##### status: 项目运行状态
##### PO: 产品经理
##### PM: 项目经理
##### QD: 测试主管
#### 项目与产品关联数据表：zt_projectproduct
##### 字段及自然名映射：
##### project: 项目编号
##### product: 项目编号

### 阶段四
**目标**: 获取bug列表
#### 人员数据表: zt_user
##### 字段及自然名映射：
##### account: 人员全局唯一标识，其它表的PO,PM,QD, RD等和人相关的字段都用这个值关联。
##### realname: 人员真实姓名，如：人名韦家鹏对应account字段的account中的weijiapeng。
##### role: 人员职位
#### bug数据表: zt_bug
##### 字段及自然名映射：
##### id: bug唯一编号
##### product: bug对应的产品
##### project: bug对应的项目
##### module: bug对应的功能模块，对应zt_module表
##### title: bug标题描述
##### severity: bug严重程度
##### pri: bug需要处理的优先级
##### steps: bug产生的过程描述
##### status: bug的状态
##### openedBy: 修改status为Open的人员
##### openedDate: 修改status为Open的时间
##### assignedTo: 当前负责人
##### assignedDate: 最近的指派时间
##### resolvedBy: 解决bug的人员
##### resolvedDate: 解决的时间
##### closedBy: 关闭bug的人员
##### closedDate: 关闭bug的时间
#### 功能模块数据表: zt_module
##### 字段及自然名映射：
##### id: 全局唯一标识
##### name: 功能模块名称







