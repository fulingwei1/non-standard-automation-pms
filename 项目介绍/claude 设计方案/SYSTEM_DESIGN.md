# 非标自动化项目管理系统 - 完整设计方案

**编制单位**：深圳金凯博自动化科技有限公司
**编制日期**：2025年1月
**版本**：V1.0

---

## 一、系统概述

### 1.1 核心目标

解决非标自动化设备企业面临的7大核心痛点：

| 痛点 | 系统解决方案 |
|------|-------------|
| **缺料** | BOM管理 + 采购跟踪 + 齐套率监控 + 缺料预警 |
| **交期逾期** | 三维状态管理 + 里程碑监控 + 关键路径分析 |
| **工程师互相等** | 任务依赖管理 + 负荷可视化 + 协同预警 |
| **设计变更混乱** | ECN流程 + BOM联动 + 版本管理 |
| **外协跟踪难** | 外协订单管理 + 进度跟踪 + 供应商评价 |
| **售后响应慢** | 工单系统 + 设备档案 + 知识库 |
| **不复盘** | 复盘模板 + 成本分析 + 经验沉淀 |

### 1.2 技术架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              非标自动化项目管理系统                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                          前端层 (Vue 3 + TypeScript)                   │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │ │
│  │  │Element+ │ │ ECharts │ │ DHTMLX  │ │  Pinia  │ │  Axios  │         │ │
│  │  │   UI    │ │  图表   │ │  甘特图 │ │  状态   │ │  HTTP   │         │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│                              REST API                                       │
│                                    │                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                          后端层 (FastAPI + Python)                     │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │ │
│  │  │ SQLAlch │ │ Celery  │ │ Pydantic│ │  JWT    │ │  Redis  │         │ │
│  │  │  ORM    │ │  异步   │ │  校验   │ │  认证   │ │  缓存   │         │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                    │                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                            数据层                                      │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐        │ │
│  │  │    MySQL 8.0    │  │     Redis       │  │   MinIO/OSS     │        │ │
│  │  │    主数据库     │  │    缓存/队列    │  │    文件存储     │        │ │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘        │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                           集成层                                       │ │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                      │ │
│  │  │企业微信 │ │  钉钉   │ │  邮件   │ │  短信   │                      │ │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 技术选型

| 层级 | 技术栈 | 版本 | 说明 |
|------|--------|------|------|
| **前端** | Vue 3 | 3.4+ | 组合式API |
| | TypeScript | 5.0+ | 类型安全 |
| | Element Plus | 2.5+ | UI组件库 |
| | Pinia | 2.1+ | 状态管理 |
| | Vite | 5.0+ | 构建工具 |
| | ECharts | 5.4+ | 图表库 |
| | DHTMLX Gantt | 8.0+ | 甘特图 |
| **后端** | Python | 3.11+ | 运行环境 |
| | FastAPI | 0.109+ | Web框架 |
| | SQLAlchemy | 2.0+ | ORM |
| | Pydantic | 2.0+ | 数据校验 |
| | Celery | 5.3+ | 异步任务 |
| | Redis | 7.0+ | 缓存/消息队列 |
| **数据库** | MySQL | 8.0+ | 主数据库 |
| | Redis | 7.0+ | 缓存 |
| | MinIO | - | 对象存储 |
| **部署** | Docker | 24+ | 容器化 |
| | Nginx | 1.24+ | 反向代理 |

---

## 二、功能模块架构

### 2.1 模块全景图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           系统模块架构                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─ 第一期：基础平台 ─────────────────────────────────────────────────────┐│
│  │                                                                         ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│  │  │ 01.系统  │  │ 02.主数据│  │ 03.项目  │  │ 04.任务  │  │ 05.采购  │ ││
│  │  │    管理  │  │    管理  │  │    管理  │  │    管理  │  │    物料  │ ││
│  │  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤ ││
│  │  │• 用户管理│  │• 客户档案│  │• 项目立项│  │• WBS分解 │  │• BOM管理 │ ││
│  │  │• 角色权限│  │• 供应商  │  │• 三维状态│  │• 甘特图  │  │• 采购订单│ ││
│  │  │• 组织架构│  │• 物料库  │  │• 里程碑  │  │• 任务依赖│  │• 到货跟踪│ ││
│  │  │• 系统配置│  │• 人员档案│  │• 项目看板│  │• 进度更新│  │• 缺料预警│ ││
│  │  │• 操作日志│  │• 编码规则│  │• 健康度  │  │• 工时填报│  │• 齐套分析│ ││
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ ││
│  │                                                                         ││
│  │  ┌──────────┐                                                           ││
│  │  │ 06.预警  │                                                           ││
│  │  │    中心  │                                                           ││
│  │  ├──────────┤                                                           ││
│  │  │• 逾期预警│                                                           ││
│  │  │• 缺料预警│                                                           ││
│  │  │• 负荷预警│                                                           ││
│  │  │• 预警处理│                                                           ││
│  │  └──────────┘                                                           ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─ 第二期：协同与变更 ───────────────────────────────────────────────────┐│
│  │                                                                         ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│  │  │ 07.设计  │  │ 08.外协  │  │ 09.资源  │  │ 10.收款  │  │ 11.消息  │ ││
│  │  │    变更  │  │    管理  │  │    排程  │  │    管理  │  │    通知  │ ││
│  │  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤ ││
│  │  │• ECN流程 │  │• 外协需求│  │• 人员负荷│  │• 付款节点│  │• 企微推送│ ││
│  │  │• 影响评估│  │• 外协订单│  │• 产能规划│  │• 收款跟踪│  │• 站内消息│ ││
│  │  │• BOM联动 │  │• 进度跟踪│  │• 资源调度│  │• 收款提醒│  │• 待办提醒│ ││
│  │  │• 变更追溯│  │• 供应商评│  │• 负荷热力│  │• 应收报表│  │• 审批通知│ ││
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
│  ┌─ 第三期：售后与沉淀 ───────────────────────────────────────────────────┐│
│  │                                                                         ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ ││
│  │  │ 12.售后  │  │ 13.项目  │  │ 14.知识  │  │ 15.成本  │  │ 16.BI    │ ││
│  │  │    服务  │  │    复盘  │  │    库    │  │    核算  │  │    报表  │ ││
│  │  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤ ││
│  │  │• 工单管理│  │• 复盘模板│  │• 问题库  │  │• 成本归集│  │• 交付率  │ ││
│  │  │• 设备档案│  │• 经验总结│  │• 方案库  │  │• 利润分析│  │• 健康度板│ ││
│  │  │• 服务记录│  │• 改进措施│  │• 文档库  │  │• 成本预警│  │• 人效分析│ ││
│  │  │• SLA管理 │  │• 模板沉淀│  │• 搜索查询│  │• 对比分析│  │• 趋势分析│ ││
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块功能清单

#### 2.2.1 第一期：基础平台

**01. 系统管理**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 用户管理 | 用户CRUD、密码管理、状态管理 | P0 |
| 角色管理 | 角色CRUD、权限分配 | P0 |
| 权限管理 | 菜单权限、数据权限、按钮权限 | P0 |
| 组织架构 | 部门管理、层级关系 | P0 |
| 系统配置 | 参数配置、字典管理 | P1 |
| 操作日志 | 登录日志、操作审计 | P1 |

**02. 主数据管理**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 客户档案 | 客户信息、联系人、历史项目 | P0 |
| 供应商档案 | 供应商信息、品类、评价 | P0 |
| 物料主数据 | 物料信息、分类、标准交期 | P0 |
| 人员档案 | 工程师信息、技能标签 | P0 |
| 编码规则 | 项目号、物料号等编码规则配置 | P1 |

**03. 项目管理**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 项目创建 | 项目立项、基本信息录入 | P0 |
| 项目列表 | 列表/卡片视图、筛选搜索 | P0 |
| 项目看板 | 按阶段看板、健康度展示 | P0 |
| 项目详情 | 360度视图、进度、团队、成本 | P0 |
| 三维状态 | 阶段(S1-S9)、状态、健康度 | P0 |
| 里程碑管理 | 关键节点定义与跟踪 | P0 |
| 项目团队 | 团队成员分配、角色定义 | P1 |

**04. 任务管理**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| WBS分解 | 三级任务分解、拖拽调整 | P0 |
| 甘特图 | 可视化进度、拖拽编辑 | P0 |
| 任务依赖 | FS/SS/FF/SF四种依赖 | P0 |
| 关键路径 | CPM自动计算、浮动时间 | P0 |
| 进度更新 | 任务进度、完成情况 | P0 |
| 任务分配 | 任务指派、多人协作 | P0 |
| 工时填报 | 每日工时、审批流程 | P1 |
| 我的任务 | 个人任务清单 | P0 |

**05. 采购物料**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| BOM管理 | BOM创建、导入、版本管理 | P0 |
| 采购需求 | 根据BOM生成采购需求 | P0 |
| 采购订单 | 订单创建、跟踪 | P0 |
| 到货管理 | 到货登记、检验 | P0 |
| 缺料预警 | 自动识别影响生产的缺料 | P0 |
| 齐套分析 | 项目物料齐套率分析 | P0 |

**06. 预警中心**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 预警列表 | 分级显示（红/橙/黄） | P0 |
| 预警处理 | 认领、处理、关闭 | P0 |
| 预警规则 | 阈值配置 | P1 |
| 预警统计 | 趋势分析 | P2 |

#### 2.2.2 第二期：协同与变更

**07. 设计变更（ECN）**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 变更申请 | 发起设计变更 | P0 |
| 影响评估 | 成本/交期/BOM影响分析 | P0 |
| 变更审批 | 多级审批流程 | P0 |
| 变更执行 | BOM更新、采购调整联动 | P0 |
| 变更追溯 | 变更历史查询 | P1 |

**08. 外协管理**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 外协需求 | 生成外协加工需求 | P0 |
| 外协订单 | 外协单创建、打印 | P0 |
| 进度跟踪 | 进度更新、延期预警 | P0 |
| 外协报表 | 发给供应商的报表 | P1 |
| 供应商评价 | 交期、质量评分 | P1 |

**09. 资源排程**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 人员负荷 | 工程师工作量统计 | P0 |
| 负荷热力图 | 可视化负荷分布 | P0 |
| 产能规划 | 装配/调试工位排期 | P1 |
| 资源调度 | 任务再分配 | P1 |

**10. 收款管理**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 付款节点 | 合同付款节点定义 | P0 |
| 收款跟踪 | 各节点收款状态 | P0 |
| 收款提醒 | 到期自动提醒 | P0 |
| 应收报表 | 应收账款分析 | P1 |

**11. 消息通知**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 企微推送 | 企业微信消息推送 | P0 |
| 站内消息 | 系统内消息通知 | P0 |
| 待办提醒 | 任务到期提醒 | P0 |
| 审批通知 | 审批流程通知 | P1 |

#### 2.2.3 第三期：售后与沉淀

**12. 售后服务**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 工单创建 | 客户问题录入 | P0 |
| 工单分派 | 分配责任人 | P0 |
| 处理跟踪 | 处理过程记录 | P0 |
| 工单关闭 | 客户确认、归档 | P0 |
| 设备档案 | 每台设备的服务记录 | P1 |
| SLA管理 | 响应时间管理 | P2 |

**13. 项目复盘**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 复盘模板 | 标准化复盘框架 | P0 |
| 成本对比 | 预算vs实际 | P0 |
| 问题总结 | 问题与解决方案归档 | P0 |
| 经验沉淀 | 最佳实践提取 | P1 |

**14. 知识库**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 问题库 | 历史问题与解决方案 | P0 |
| 方案库 | 典型方案模板 | P1 |
| 文档库 | 图纸、程序版本管理 | P1 |
| 全文搜索 | 知识检索 | P1 |

**15. 成本核算**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 成本归集 | 物料+人工+外协 | P0 |
| 利润分析 | 项目毛利计算 | P0 |
| 成本预警 | 超预算预警 | P1 |
| 成本对比 | 多项目对比分析 | P2 |

**16. BI报表**

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 交付准时率 | 按月/客户/类型 | P0 |
| 健康度看板 | 红黄绿灯分布 | P0 |
| 人员利用率 | 工程师工作量 | P1 |
| 供应商绩效 | 交期/质量评分 | P1 |
| 成本趋势 | 成本结构分析 | P2 |

---

## 三、数据库设计

### 3.1 核心实体关系图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ER关系图（核心部分）                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                           ┌──────────────┐                                  │
│                           │   customer   │                                  │
│                           │   客户表     │                                  │
│                           └───────┬──────┘                                  │
│                                   │ 1:N                                     │
│  ┌──────────────┐                 │                  ┌──────────────┐       │
│  │   contract   │─────────────────┼──────────────────│    project   │       │
│  │   合同表     │     1:N         │         1:N      │    项目表    │       │
│  └──────────────┘                 │                  └───────┬──────┘       │
│                                   │                          │              │
│                    ┌──────────────┼──────────────┐           │              │
│                    │              │              │           │              │
│              ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐     │              │
│              │  wbs_task │  │    bom    │  │  payment  │     │              │
│              │   任务表  │  │  BOM表    │  │  收款计划 │     │              │
│              └─────┬─────┘  └─────┬─────┘  └───────────┘     │              │
│                    │              │                          │              │
│        ┌───────────┼───────┐      │                          │              │
│        │           │       │      │                          │              │
│  ┌─────┴─────┐ ┌───┴───┐ ┌─┴───────────┐              ┌──────┴─────┐        │
│  │task_assign│ │timesht│ │    ecn      │              │project_team│        │
│  │  任务分配 │ │ 工时  │ │  设计变更   │              │  项目团队  │        │
│  └───────────┘ └───────┘ └─────────────┘              └────────────┘        │
│                                                                             │
│        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│        │  supplier    │  │  material    │  │    user      │                 │
│        │  供应商表    │  │   物料表     │  │   用户表     │                 │
│        └───────┬──────┘  └───────┬──────┘  └──────────────┘                 │
│                │                 │                                          │
│          ┌─────┴──────┐    ┌─────┴──────┐                                   │
│          │purchase_ord│    │outsource   │                                   │
│          │  采购订单  │    │  外协订单  │                                   │
│          └────────────┘    └────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据表清单

#### 3.2.1 系统管理模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| sys_user | 用户表 | 系统用户信息 |
| sys_role | 角色表 | 角色定义 |
| sys_user_role | 用户角色关联表 | 多对多关联 |
| sys_menu | 菜单表 | 系统菜单 |
| sys_role_menu | 角色菜单关联表 | 权限分配 |
| sys_dept | 部门表 | 组织架构 |
| sys_config | 系统配置表 | 参数配置 |
| sys_dict | 字典表 | 数据字典 |
| sys_log | 操作日志表 | 审计日志 |

#### 3.2.2 主数据模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| customer | 客户表 | 客户主数据 |
| supplier | 供应商表 | 供应商主数据 |
| material | 物料表 | 物料主数据 |
| material_category | 物料分类表 | 物料类别 |

#### 3.2.3 项目管理模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| project | 项目表 | 项目主表 |
| project_team | 项目团队表 | 项目成员 |
| project_milestone | 里程碑表 | 关键节点 |
| contract | 合同表 | 销售合同 |

#### 3.2.4 任务管理模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| wbs_task | WBS任务表 | 任务分解 |
| task_assignment | 任务分配表 | 任务指派 |
| task_dependency | 任务依赖表 | 前后置关系 |
| task_log | 任务日志表 | 变更记录 |
| timesheet | 工时记录表 | 工时填报 |

#### 3.2.5 采购物料模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| project_bom | 项目BOM表 | BOM清单 |
| bom_version | BOM版本表 | 版本管理 |
| purchase_order | 采购订单表 | 采购单 |
| purchase_order_item | 采购订单明细表 | 采购明细 |
| delivery_record | 到货记录表 | 入库记录 |

#### 3.2.6 变更管理模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| ecn | 设计变更表 | ECN主表 |
| ecn_bom_change | ECN BOM变更明细 | 变更内容 |
| ecn_approval | ECN审批记录 | 审批流程 |

#### 3.2.7 外协管理模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| outsource_order | 外协订单表 | 外协单 |
| outsource_order_item | 外协订单明细表 | 外协明细 |
| outsource_progress | 外协进度表 | 进度跟踪 |

#### 3.2.8 预警模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| progress_alert | 进度预警表 | 预警记录 |
| alert_rule | 预警规则表 | 规则配置 |
| workload_snapshot | 负荷快照表 | 负荷统计 |

#### 3.2.9 收款模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| payment_plan | 收款计划表 | 付款节点 |
| payment_record | 收款记录表 | 实际收款 |

#### 3.2.10 售后模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| service_order | 售后工单表 | 工单管理 |
| equipment | 设备档案表 | 设备信息 |
| service_record | 服务记录表 | 服务历史 |

#### 3.2.11 知识库模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| knowledge_article | 知识文章表 | 文章内容 |
| knowledge_category | 知识分类表 | 分类管理 |

#### 3.2.12 成本模块

| 表名 | 中文名 | 说明 |
|------|--------|------|
| project_cost | 项目成本表 | 成本归集 |
| project_review | 项目复盘表 | 复盘记录 |

### 3.3 核心表DDL

```sql
-- =============================================
-- 非标自动化项目管理系统 DDL脚本
-- 数据库：MySQL 8.0+
-- =============================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- 1. 客户主数据表
-- ----------------------------
DROP TABLE IF EXISTS `customer`;
CREATE TABLE `customer` (
    `customer_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '客户ID',
    `customer_code` VARCHAR(20) NOT NULL COMMENT '客户编码 C00001',
    `customer_name` VARCHAR(100) NOT NULL COMMENT '客户名称',
    `short_name` VARCHAR(50) NULL COMMENT '简称',
    `industry` VARCHAR(50) NULL COMMENT '行业：汽车电子/白色家电/BMS等',
    `level` VARCHAR(10) DEFAULT 'B' COMMENT '等级：A/B/C/D',
    `contact_name` VARCHAR(50) NULL COMMENT '联系人',
    `contact_phone` VARCHAR(20) NULL COMMENT '联系电话',
    `contact_email` VARCHAR(100) NULL COMMENT '邮箱',
    `address` VARCHAR(300) NULL COMMENT '地址',
    `credit_limit` DECIMAL(12,2) DEFAULT 0 COMMENT '信用额度',
    `payment_terms` VARCHAR(50) NULL COMMENT '账期',
    `status` VARCHAR(20) DEFAULT '正常' COMMENT '状态',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_by` BIGINT NULL COMMENT '更新人ID',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`customer_id`),
    UNIQUE KEY `uk_customer_code` (`customer_code`),
    KEY `idx_customer_name` (`customer_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='客户主数据表';

-- ----------------------------
-- 2. 供应商主数据表
-- ----------------------------
DROP TABLE IF EXISTS `supplier`;
CREATE TABLE `supplier` (
    `supplier_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '供应商ID',
    `supplier_code` VARCHAR(20) NOT NULL COMMENT '供应商编码 V00001',
    `supplier_name` VARCHAR(100) NOT NULL COMMENT '供应商名称',
    `supplier_type` VARCHAR(30) NOT NULL COMMENT '类型：机加/钣金/电气/标准件/贸易',
    `contact_name` VARCHAR(50) NULL COMMENT '联系人',
    `contact_phone` VARCHAR(20) NULL COMMENT '联系电话',
    `contact_email` VARCHAR(100) NULL COMMENT '邮箱',
    `address` VARCHAR(300) NULL COMMENT '地址',
    `lead_time` INT DEFAULT 7 COMMENT '标准交期(天)',
    `quality_score` DECIMAL(3,1) DEFAULT 80 COMMENT '质量评分',
    `delivery_score` DECIMAL(3,1) DEFAULT 80 COMMENT '交期评分',
    `status` VARCHAR(20) DEFAULT '合格' COMMENT '状态：合格/观察/淘汰',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`supplier_id`),
    UNIQUE KEY `uk_supplier_code` (`supplier_code`),
    KEY `idx_supplier_type` (`supplier_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='供应商主数据表';

-- ----------------------------
-- 3. 物料主数据表
-- ----------------------------
DROP TABLE IF EXISTS `material`;
CREATE TABLE `material` (
    `material_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '物料ID',
    `material_code` VARCHAR(30) NOT NULL COMMENT '物料编码',
    `material_name` VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification` VARCHAR(200) NULL COMMENT '规格型号',
    `category_l1` VARCHAR(20) NOT NULL COMMENT '大类：ME/EL/PN/ST/OT/TR',
    `category_l2` VARCHAR(20) NULL COMMENT '中类',
    `category_l3` VARCHAR(20) NULL COMMENT '小类',
    `unit` VARCHAR(20) DEFAULT 'pcs' COMMENT '单位',
    `is_standard` TINYINT DEFAULT 0 COMMENT '是否标准件',
    `default_supplier_id` BIGINT NULL COMMENT '默认供应商',
    `lead_time` INT DEFAULT 7 COMMENT '标准采购周期(天)',
    `reference_price` DECIMAL(12,2) NULL COMMENT '参考单价',
    `min_order_qty` DECIMAL(10,2) DEFAULT 1 COMMENT '最小起订量',
    `status` VARCHAR(20) DEFAULT '启用' COMMENT '状态',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`material_id`),
    UNIQUE KEY `uk_material_code` (`material_code`),
    KEY `idx_material_category` (`category_l1`, `category_l2`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='物料主数据表';

-- ----------------------------
-- 4. 合同表
-- ----------------------------
DROP TABLE IF EXISTS `contract`;
CREATE TABLE `contract` (
    `contract_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '合同ID',
    `contract_code` VARCHAR(30) NOT NULL COMMENT '合同号 HT2507-001',
    `contract_name` VARCHAR(200) NOT NULL COMMENT '合同名称',
    `customer_id` BIGINT NOT NULL COMMENT '客户ID',
    `customer_name` VARCHAR(100) NOT NULL COMMENT '客户名称',
    `contract_amount` DECIMAL(14,2) NOT NULL COMMENT '合同金额',
    `tax_rate` DECIMAL(5,2) DEFAULT 13.00 COMMENT '税率%',
    `sign_date` DATE NOT NULL COMMENT '签订日期',
    `delivery_date` DATE NOT NULL COMMENT '合同交期',
    `machine_count` INT DEFAULT 1 COMMENT '机台数量',
    `warranty_months` INT DEFAULT 12 COMMENT '质保期(月)',
    `sales_id` BIGINT NOT NULL COMMENT '销售负责人ID',
    `sales_name` VARCHAR(50) NOT NULL COMMENT '销售负责人',
    `status` VARCHAR(20) DEFAULT '执行中' COMMENT '状态：待生效/执行中/已完成/已终止',
    `payment_terms` TEXT NULL COMMENT '付款条款JSON',
    `tech_requirements` TEXT NULL COMMENT '技术要求',
    `special_terms` TEXT NULL COMMENT '特殊条款',
    `attachment_ids` VARCHAR(500) NULL COMMENT '附件ID列表',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`contract_id`),
    UNIQUE KEY `uk_contract_code` (`contract_code`),
    KEY `idx_contract_customer` (`customer_id`),
    KEY `idx_contract_sales` (`sales_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='合同表';

-- ----------------------------
-- 5. 项目主表
-- ----------------------------
DROP TABLE IF EXISTS `project`;
CREATE TABLE `project` (
    `project_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '项目ID',
    `project_code` VARCHAR(30) NOT NULL COMMENT '项目编号 PJ250708001',
    `project_name` VARCHAR(200) NOT NULL COMMENT '项目名称',
    `project_type` VARCHAR(20) NOT NULL DEFAULT '订单' COMMENT '项目类型：订单/研发/改造/维保',
    `project_level` VARCHAR(10) NOT NULL DEFAULT 'B' COMMENT '项目等级：A/B/C/D',
    `contract_id` BIGINT NULL COMMENT '关联合同ID',
    `contract_code` VARCHAR(30) NULL COMMENT '合同号',
    `customer_id` BIGINT NOT NULL COMMENT '客户ID',
    `customer_name` VARCHAR(100) NOT NULL COMMENT '客户名称',
    `machine_count` INT DEFAULT 1 COMMENT '机台数量',
    `pm_id` BIGINT NOT NULL COMMENT '项目经理ID',
    `pm_name` VARCHAR(50) NOT NULL COMMENT '项目经理姓名',
    `te_id` BIGINT NULL COMMENT '技术经理ID',
    `te_name` VARCHAR(50) NULL COMMENT '技术经理姓名',
    `plan_start_date` DATE NOT NULL COMMENT '计划开始日期',
    `plan_end_date` DATE NOT NULL COMMENT '计划结束日期（合同交期）',
    `baseline_start_date` DATE NULL COMMENT '基线开始日期',
    `baseline_end_date` DATE NULL COMMENT '基线结束日期',
    `actual_start_date` DATE NULL COMMENT '实际开始日期',
    `actual_end_date` DATE NULL COMMENT '实际结束日期',
    `plan_duration` INT NOT NULL DEFAULT 0 COMMENT '计划工期（工作日）',
    `progress_rate` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '进度完成率%',
    `plan_progress_rate` DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT '计划进度率%',
    `spi` DECIMAL(5,2) NOT NULL DEFAULT 1.00 COMMENT 'SPI进度绩效指数',
    `plan_manhours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '计划总工时',
    `actual_manhours` DECIMAL(10,2) NOT NULL DEFAULT 0 COMMENT '已消耗工时',
    `budget_amount` DECIMAL(14,2) NULL COMMENT '预算金额',
    `actual_cost` DECIMAL(14,2) DEFAULT 0 COMMENT '实际成本',
    `current_stage` VARCHAR(30) NOT NULL DEFAULT 'S1' COMMENT '当前阶段 S1-S9',
    `current_phase` VARCHAR(30) NOT NULL DEFAULT '立项启动' COMMENT '当前阶段名称',
    `status` VARCHAR(20) NOT NULL DEFAULT '未启动' COMMENT '项目状态',
    `health_status` VARCHAR(10) NOT NULL DEFAULT '绿' COMMENT '健康状态：绿/黄/红',
    `risk_level` VARCHAR(10) DEFAULT '低' COMMENT '风险等级：低/中/高',
    `description` TEXT NULL COMMENT '项目描述',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_by` BIGINT NULL COMMENT '更新人ID',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT NOT NULL DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`project_id`),
    UNIQUE KEY `uk_project_code` (`project_code`),
    KEY `idx_project_customer` (`customer_id`),
    KEY `idx_project_pm` (`pm_id`),
    KEY `idx_project_status` (`status`),
    KEY `idx_project_health` (`health_status`),
    KEY `idx_project_date` (`plan_start_date`, `plan_end_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目主表';

-- ----------------------------
-- 6. 项目团队表
-- ----------------------------
DROP TABLE IF EXISTS `project_team`;
CREATE TABLE `project_team` (
    `team_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '团队ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `user_name` VARCHAR(50) NOT NULL COMMENT '用户姓名',
    `dept_id` BIGINT NOT NULL COMMENT '部门ID',
    `dept_name` VARCHAR(50) NOT NULL COMMENT '部门名称',
    `role` VARCHAR(30) NOT NULL COMMENT '项目角色：PM/TE/机械/电气/软件/采购/装配/调试',
    `join_date` DATE NOT NULL COMMENT '加入日期',
    `leave_date` DATE NULL COMMENT '退出日期',
    `allocation_rate` DECIMAL(5,2) DEFAULT 100 COMMENT '投入比例%',
    `status` VARCHAR(20) DEFAULT '在岗' COMMENT '状态',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`team_id`),
    UNIQUE KEY `uk_project_user` (`project_id`, `user_id`),
    KEY `idx_team_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目团队表';

-- ----------------------------
-- 7. 项目BOM表
-- ----------------------------
DROP TABLE IF EXISTS `project_bom`;
CREATE TABLE `project_bom` (
    `bom_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'BOM ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `machine_no` VARCHAR(30) NOT NULL COMMENT '机台号 PJ250708001-PN001',
    `material_id` BIGINT NOT NULL COMMENT '物料ID',
    `material_code` VARCHAR(30) NOT NULL COMMENT '物料编码',
    `material_name` VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification` VARCHAR(200) NULL COMMENT '规格型号',
    `quantity` DECIMAL(10,2) NOT NULL COMMENT '需求数量',
    `unit` VARCHAR(20) DEFAULT 'pcs' COMMENT '单位',
    `category` VARCHAR(30) NOT NULL COMMENT '物料类别',
    `reference_price` DECIMAL(12,2) NULL COMMENT '参考单价',
    `estimated_cost` DECIMAL(12,2) NULL COMMENT '预估成本',
    `bom_version` VARCHAR(10) DEFAULT 'V1.0' COMMENT 'BOM版本',
    `is_long_lead` TINYINT DEFAULT 0 COMMENT '是否长周期',
    `required_date` DATE NULL COMMENT '需求日期',
    `ordered_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '已下单数量',
    `received_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '已到货数量',
    `status` VARCHAR(20) DEFAULT '待采购' COMMENT '状态：待采购/采购中/已到货',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`bom_id`),
    KEY `idx_bom_project` (`project_id`),
    KEY `idx_bom_material` (`material_id`),
    KEY `idx_bom_machine` (`machine_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目BOM表';

-- ----------------------------
-- 8. 采购订单表
-- ----------------------------
DROP TABLE IF EXISTS `purchase_order`;
CREATE TABLE `purchase_order` (
    `po_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '采购订单ID',
    `po_code` VARCHAR(30) NOT NULL COMMENT '采购订单号 PO250710-001',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `project_code` VARCHAR(30) NOT NULL COMMENT '项目编号',
    `supplier_id` BIGINT NOT NULL COMMENT '供应商ID',
    `supplier_name` VARCHAR(100) NOT NULL COMMENT '供应商名称',
    `po_amount` DECIMAL(12,2) NOT NULL COMMENT '订单金额',
    `tax_amount` DECIMAL(12,2) DEFAULT 0 COMMENT '税额',
    `order_date` DATE NOT NULL COMMENT '下单日期',
    `expect_date` DATE NOT NULL COMMENT '预计到货日期',
    `actual_date` DATE NULL COMMENT '实际到货日期',
    `status` VARCHAR(20) DEFAULT '待确认' COMMENT '状态：待确认/已确认/部分到货/已到货/已关闭',
    `buyer_id` BIGINT NOT NULL COMMENT '采购员ID',
    `buyer_name` VARCHAR(50) NOT NULL COMMENT '采购员',
    `payment_terms` VARCHAR(100) NULL COMMENT '付款条件',
    `delivery_address` VARCHAR(300) NULL COMMENT '收货地址',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`po_id`),
    UNIQUE KEY `uk_po_code` (`po_code`),
    KEY `idx_po_project` (`project_id`),
    KEY `idx_po_supplier` (`supplier_id`),
    KEY `idx_po_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购订单表';

-- ----------------------------
-- 9. 采购订单明细表
-- ----------------------------
DROP TABLE IF EXISTS `purchase_order_item`;
CREATE TABLE `purchase_order_item` (
    `item_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '明细ID',
    `po_id` BIGINT NOT NULL COMMENT '采购订单ID',
    `bom_id` BIGINT NULL COMMENT '关联BOM ID',
    `material_id` BIGINT NOT NULL COMMENT '物料ID',
    `material_code` VARCHAR(30) NOT NULL COMMENT '物料编码',
    `material_name` VARCHAR(200) NOT NULL COMMENT '物料名称',
    `specification` VARCHAR(200) NULL COMMENT '规格型号',
    `quantity` DECIMAL(10,2) NOT NULL COMMENT '采购数量',
    `unit` VARCHAR(20) DEFAULT 'pcs' COMMENT '单位',
    `unit_price` DECIMAL(12,2) NOT NULL COMMENT '单价',
    `amount` DECIMAL(12,2) NOT NULL COMMENT '金额',
    `received_qty` DECIMAL(10,2) DEFAULT 0 COMMENT '已到货数量',
    `status` VARCHAR(20) DEFAULT '待到货' COMMENT '状态：待到货/部分到货/已到货',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    PRIMARY KEY (`item_id`),
    KEY `idx_poi_po` (`po_id`),
    KEY `idx_poi_bom` (`bom_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='采购订单明细表';

-- ----------------------------
-- 10. 到货记录表
-- ----------------------------
DROP TABLE IF EXISTS `delivery_record`;
CREATE TABLE `delivery_record` (
    `delivery_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '到货ID',
    `po_id` BIGINT NOT NULL COMMENT '采购订单ID',
    `item_id` BIGINT NOT NULL COMMENT '订单明细ID',
    `delivery_qty` DECIMAL(10,2) NOT NULL COMMENT '到货数量',
    `delivery_date` DATE NOT NULL COMMENT '到货日期',
    `quality_status` VARCHAR(20) DEFAULT '待检' COMMENT '质量状态：待检/合格/不合格',
    `inspector_id` BIGINT NULL COMMENT '检验员ID',
    `inspector_name` VARCHAR(50) NULL COMMENT '检验员',
    `inspect_date` DATE NULL COMMENT '检验日期',
    `reject_reason` VARCHAR(500) NULL COMMENT '不合格原因',
    `warehouse_id` BIGINT NULL COMMENT '入库仓库',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`delivery_id`),
    KEY `idx_dr_po` (`po_id`),
    KEY `idx_dr_item` (`item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='到货记录表';

-- ----------------------------
-- 11. 设计变更ECN表
-- ----------------------------
DROP TABLE IF EXISTS `ecn`;
CREATE TABLE `ecn` (
    `ecn_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'ECN ID',
    `ecn_code` VARCHAR(30) NOT NULL COMMENT '变更单号 ECN-PJ250708001-01',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `project_code` VARCHAR(30) NOT NULL COMMENT '项目编号',
    `ecn_type` VARCHAR(30) NOT NULL COMMENT '变更类型：客户需求/内部优化/供应问题/质量问题',
    `urgency` VARCHAR(10) DEFAULT '普通' COMMENT '紧急程度：紧急/普通',
    `change_reason` TEXT NOT NULL COMMENT '变更原因',
    `change_content` TEXT NOT NULL COMMENT '变更内容',
    `cost_impact` DECIMAL(12,2) DEFAULT 0 COMMENT '成本影响',
    `schedule_impact` INT DEFAULT 0 COMMENT '交期影响(天)',
    `affected_tasks` VARCHAR(500) NULL COMMENT '影响的任务ID列表',
    `initiated_by` BIGINT NOT NULL COMMENT '发起人ID',
    `initiated_name` VARCHAR(50) NOT NULL COMMENT '发起人',
    `initiated_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '发起时间',
    `status` VARCHAR(20) DEFAULT '待评审' COMMENT '状态：待评审/评审中/已批准/已执行/已关闭/已拒绝',
    `current_approver_id` BIGINT NULL COMMENT '当前审批人ID',
    `approved_by` BIGINT NULL COMMENT '最终审批人ID',
    `approved_time` DATETIME NULL COMMENT '审批时间',
    `executed_by` BIGINT NULL COMMENT '执行人ID',
    `executed_time` DATETIME NULL COMMENT '执行时间',
    `closed_time` DATETIME NULL COMMENT '关闭时间',
    `reject_reason` VARCHAR(500) NULL COMMENT '拒绝原因',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`ecn_id`),
    UNIQUE KEY `uk_ecn_code` (`ecn_code`),
    KEY `idx_ecn_project` (`project_id`),
    KEY `idx_ecn_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设计变更ECN表';

-- ----------------------------
-- 12. ECN BOM变更明细表
-- ----------------------------
DROP TABLE IF EXISTS `ecn_bom_change`;
CREATE TABLE `ecn_bom_change` (
    `change_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '变更明细ID',
    `ecn_id` BIGINT NOT NULL COMMENT 'ECN ID',
    `change_type` VARCHAR(10) NOT NULL COMMENT '变更类型：新增/修改/删除',
    `bom_id` BIGINT NULL COMMENT '原BOM ID',
    `material_id` BIGINT NOT NULL COMMENT '物料ID',
    `material_code` VARCHAR(30) NOT NULL COMMENT '物料编码',
    `material_name` VARCHAR(200) NOT NULL COMMENT '物料名称',
    `old_quantity` DECIMAL(10,2) NULL COMMENT '原数量',
    `new_quantity` DECIMAL(10,2) NULL COMMENT '新数量',
    `old_specification` VARCHAR(200) NULL COMMENT '原规格',
    `new_specification` VARCHAR(200) NULL COMMENT '新规格',
    `cost_change` DECIMAL(12,2) DEFAULT 0 COMMENT '成本变化',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    PRIMARY KEY (`change_id`),
    KEY `idx_ecnbom_ecn` (`ecn_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ECN BOM变更明细表';

-- ----------------------------
-- 13. 外协订单表
-- ----------------------------
DROP TABLE IF EXISTS `outsource_order`;
CREATE TABLE `outsource_order` (
    `order_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '外协订单ID',
    `order_code` VARCHAR(30) NOT NULL COMMENT '外协单号 OT-250710-001',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `project_code` VARCHAR(30) NOT NULL COMMENT '项目编号',
    `supplier_id` BIGINT NOT NULL COMMENT '供应商ID',
    `supplier_name` VARCHAR(100) NOT NULL COMMENT '供应商名称',
    `order_date` DATE NOT NULL COMMENT '下单日期',
    `expect_date` DATE NOT NULL COMMENT '预计交货日期',
    `actual_date` DATE NULL COMMENT '实际交货日期',
    `total_amount` DECIMAL(12,2) NOT NULL COMMENT '订单总金额',
    `status` VARCHAR(20) DEFAULT '待确认' COMMENT '状态：待确认/加工中/部分交货/已交货/已关闭',
    `buyer_id` BIGINT NOT NULL COMMENT '下单人ID',
    `buyer_name` VARCHAR(50) NOT NULL COMMENT '下单人',
    `contact_info` VARCHAR(200) NULL COMMENT '联系方式',
    `delivery_address` VARCHAR(300) NULL COMMENT '送货地址',
    `quality_requirement` TEXT NULL COMMENT '质量要求',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`order_id`),
    UNIQUE KEY `uk_order_code` (`order_code`),
    KEY `idx_ot_project` (`project_id`),
    KEY `idx_ot_supplier` (`supplier_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外协加工订单表';

-- ----------------------------
-- 14. 外协订单明细表
-- ----------------------------
DROP TABLE IF EXISTS `outsource_order_item`;
CREATE TABLE `outsource_order_item` (
    `item_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '明细ID',
    `order_id` BIGINT NOT NULL COMMENT '外协订单ID',
    `part_name` VARCHAR(200) NOT NULL COMMENT '零件名称',
    `drawing_no` VARCHAR(50) NULL COMMENT '图纸号',
    `quantity` INT NOT NULL COMMENT '数量',
    `unit` VARCHAR(20) DEFAULT 'pcs' COMMENT '单位',
    `unit_price` DECIMAL(12,2) NOT NULL COMMENT '单价',
    `amount` DECIMAL(12,2) NOT NULL COMMENT '金额',
    `material` VARCHAR(100) NULL COMMENT '材料',
    `surface_treatment` VARCHAR(100) NULL COMMENT '表面处理',
    `process_requirement` TEXT NULL COMMENT '工艺要求',
    `completed_qty` INT DEFAULT 0 COMMENT '已完成数量',
    `status` VARCHAR(20) DEFAULT '加工中' COMMENT '状态：加工中/已完成/已检验',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    PRIMARY KEY (`item_id`),
    KEY `idx_oti_order` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='外协订单明细表';

-- ----------------------------
-- 15. 收款计划表
-- ----------------------------
DROP TABLE IF EXISTS `payment_plan`;
CREATE TABLE `payment_plan` (
    `plan_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '计划ID',
    `contract_id` BIGINT NOT NULL COMMENT '合同ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `phase` VARCHAR(50) NOT NULL COMMENT '阶段：预付款/发货款/验收款/质保款',
    `phase_order` INT NOT NULL COMMENT '阶段顺序',
    `plan_ratio` DECIMAL(5,2) NOT NULL COMMENT '比例%',
    `plan_amount` DECIMAL(12,2) NOT NULL COMMENT '计划金额',
    `plan_date` DATE NOT NULL COMMENT '计划收款日期',
    `trigger_condition` VARCHAR(200) NULL COMMENT '触发条件',
    `actual_amount` DECIMAL(12,2) DEFAULT 0 COMMENT '实际收款金额',
    `actual_date` DATE NULL COMMENT '实际收款日期',
    `status` VARCHAR(20) DEFAULT '待收款' COMMENT '状态：待收款/部分收款/已收款',
    `invoice_no` VARCHAR(50) NULL COMMENT '发票号',
    `invoice_date` DATE NULL COMMENT '开票日期',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`plan_id`),
    KEY `idx_pp_contract` (`contract_id`),
    KEY `idx_pp_project` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收款计划表';

-- ----------------------------
-- 16. 售后工单表
-- ----------------------------
DROP TABLE IF EXISTS `service_order`;
CREATE TABLE `service_order` (
    `order_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '工单ID',
    `order_code` VARCHAR(30) NOT NULL COMMENT '工单号 SR-250715-001',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `project_code` VARCHAR(30) NOT NULL COMMENT '项目编号',
    `machine_no` VARCHAR(30) NOT NULL COMMENT '机台号',
    `customer_id` BIGINT NOT NULL COMMENT '客户ID',
    `customer_name` VARCHAR(100) NOT NULL COMMENT '客户名称',
    `problem_type` VARCHAR(50) NOT NULL COMMENT '问题类型：软件问题/机械问题/电气问题/操作问题/其他',
    `problem_desc` TEXT NOT NULL COMMENT '问题描述',
    `urgency` VARCHAR(10) DEFAULT '普通' COMMENT '紧急程度：紧急/普通',
    `reported_by` VARCHAR(50) NOT NULL COMMENT '报告人',
    `reported_phone` VARCHAR(20) NULL COMMENT '报告人电话',
    `reported_time` DATETIME NOT NULL COMMENT '报告时间',
    `assigned_to` BIGINT NULL COMMENT '负责人ID',
    `assigned_name` VARCHAR(50) NULL COMMENT '负责人',
    `assigned_time` DATETIME NULL COMMENT '分配时间',
    `status` VARCHAR(20) DEFAULT '待分配' COMMENT '状态：待分配/处理中/待验证/已关闭',
    `response_time` DATETIME NULL COMMENT '响应时间',
    `resolved_time` DATETIME NULL COMMENT '解决时间',
    `solution` TEXT NULL COMMENT '解决方案',
    `root_cause` TEXT NULL COMMENT '根本原因',
    `preventive_action` TEXT NULL COMMENT '预防措施',
    `satisfaction` INT NULL COMMENT '满意度1-5',
    `feedback` VARCHAR(500) NULL COMMENT '客户反馈',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`order_id`),
    UNIQUE KEY `uk_so_code` (`order_code`),
    KEY `idx_so_project` (`project_id`),
    KEY `idx_so_customer` (`customer_id`),
    KEY `idx_so_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='售后工单表';

-- ----------------------------
-- 17. 项目复盘表
-- ----------------------------
DROP TABLE IF EXISTS `project_review`;
CREATE TABLE `project_review` (
    `review_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '复盘ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `project_code` VARCHAR(30) NOT NULL COMMENT '项目编号',
    `review_date` DATE NOT NULL COMMENT '复盘日期',
    `plan_duration` INT NULL COMMENT '计划工期(天)',
    `actual_duration` INT NULL COMMENT '实际工期(天)',
    `schedule_variance` INT NULL COMMENT '进度偏差(天)',
    `budget_amount` DECIMAL(12,2) NULL COMMENT '预算金额',
    `actual_cost` DECIMAL(12,2) NULL COMMENT '实际成本',
    `cost_variance` DECIMAL(12,2) NULL COMMENT '成本偏差',
    `quality_issues` INT DEFAULT 0 COMMENT '质量问题数',
    `change_count` INT DEFAULT 0 COMMENT '变更次数',
    `customer_satisfaction` INT NULL COMMENT '客户满意度1-5',
    `success_factors` TEXT NULL COMMENT '成功因素',
    `problems` TEXT NULL COMMENT '问题与教训',
    `improvements` TEXT NULL COMMENT '改进建议',
    `best_practices` TEXT NULL COMMENT '最佳实践',
    `reviewer_id` BIGINT NOT NULL COMMENT '复盘负责人ID',
    `reviewer_name` VARCHAR(50) NOT NULL COMMENT '复盘负责人',
    `participants` VARCHAR(500) NULL COMMENT '参与人ID列表',
    `participant_names` VARCHAR(500) NULL COMMENT '参与人姓名',
    `attachment_ids` VARCHAR(500) NULL COMMENT '附件ID列表',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`review_id`),
    KEY `idx_pr_project` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目复盘表';

-- ----------------------------
-- 18. 知识库文章表
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_article`;
CREATE TABLE `knowledge_article` (
    `article_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '文章ID',
    `title` VARCHAR(200) NOT NULL COMMENT '标题',
    `category` VARCHAR(50) NOT NULL COMMENT '分类：问题库/方案库/经验分享',
    `sub_category` VARCHAR(50) NULL COMMENT '子分类',
    `tags` VARCHAR(200) NULL COMMENT '标签，逗号分隔',
    `summary` VARCHAR(500) NULL COMMENT '摘要',
    `content` LONGTEXT NOT NULL COMMENT '内容',
    `project_id` BIGINT NULL COMMENT '关联项目ID',
    `view_count` INT DEFAULT 0 COMMENT '浏览次数',
    `like_count` INT DEFAULT 0 COMMENT '点赞数',
    `author_id` BIGINT NOT NULL COMMENT '作者ID',
    `author_name` VARCHAR(50) NOT NULL COMMENT '作者',
    `status` VARCHAR(20) DEFAULT '已发布' COMMENT '状态：草稿/已发布/已归档',
    `attachment_ids` VARCHAR(500) NULL COMMENT '附件ID列表',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除',
    PRIMARY KEY (`article_id`),
    KEY `idx_ka_category` (`category`),
    KEY `idx_ka_author` (`author_id`),
    FULLTEXT KEY `ft_article` (`title`, `content`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识库文章表';

-- ----------------------------
-- 19. 项目成本表
-- ----------------------------
DROP TABLE IF EXISTS `project_cost`;
CREATE TABLE `project_cost` (
    `cost_id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '成本ID',
    `project_id` BIGINT NOT NULL COMMENT '项目ID',
    `cost_type` VARCHAR(30) NOT NULL COMMENT '成本类型：物料/人工/外协/差旅/其他',
    `cost_item` VARCHAR(100) NOT NULL COMMENT '成本项目',
    `budget_amount` DECIMAL(12,2) DEFAULT 0 COMMENT '预算金额',
    `actual_amount` DECIMAL(12,2) DEFAULT 0 COMMENT '实际金额',
    `variance` DECIMAL(12,2) DEFAULT 0 COMMENT '偏差',
    `variance_rate` DECIMAL(5,2) DEFAULT 0 COMMENT '偏差率%',
    `source_type` VARCHAR(30) NULL COMMENT '来源类型：采购单/工时/外协单',
    `source_id` BIGINT NULL COMMENT '来源ID',
    `cost_date` DATE NULL COMMENT '发生日期',
    `remark` VARCHAR(500) NULL COMMENT '备注',
    `created_by` BIGINT NOT NULL COMMENT '创建人ID',
    `created_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_time` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`cost_id`),
    KEY `idx_pc_project` (`project_id`),
    KEY `idx_pc_type` (`cost_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='项目成本表';

SET FOREIGN_KEY_CHECKS = 1;
```

---

## 四、核心API设计

### 4.1 API规范

- 基础路径：`/api/v1`
- 认证方式：JWT Token
- 请求格式：JSON
- 响应格式：统一响应结构

```json
{
    "code": 200,
    "message": "success",
    "data": {},
    "timestamp": 1704268800000
}
```

### 4.2 API模块清单

| 模块 | 前缀 | 核心接口 |
|------|------|---------|
| 认证 | /auth | login, logout, refresh, userinfo |
| 用户 | /users | CRUD, password, status |
| 角色 | /roles | CRUD, permissions |
| 客户 | /customers | CRUD, search |
| 供应商 | /suppliers | CRUD, search, evaluate |
| 物料 | /materials | CRUD, import, search |
| 合同 | /contracts | CRUD, payment-terms |
| 项目 | /projects | CRUD, dashboard, progress, health, team |
| 任务 | /tasks | WBS, gantt, CPM, progress-update, my-tasks |
| BOM | /bom | create, import, export, version |
| 采购 | /purchase | orders, items, delivery, shortage-alert |
| 外协 | /outsource | orders, tracking, print-report |
| ECN | /ecn | create, review, execute, impact |
| 工时 | /timesheets | fill, approve, statistics |
| 负荷 | /workload | team, heatmap, available |
| 预警 | /alerts | list, handle, rules, statistics |
| 收款 | /payments | plans, receivables, remind |
| 售后 | /service | orders, assign, resolve |
| 知识库 | /knowledge | articles, search, recommend |
| 成本 | /costs | summary, detail, compare |
| 复盘 | /reviews | create, list |
| 报表 | /reports | delivery-rate, cost, efficiency |

### 4.3 核心API详细设计

#### 4.3.1 项目管理API

```yaml
# 项目列表
GET /api/v1/projects
Query:
  - status: 项目状态
  - health: 健康状态
  - pm_id: 项目经理
  - customer_id: 客户
  - page: 页码
  - size: 每页数量
Response:
  - total: 总数
  - items: 项目列表

# 创建项目
POST /api/v1/projects
Body:
  - project_name: 项目名称
  - project_type: 项目类型
  - customer_id: 客户ID
  - contract_id: 合同ID
  - pm_id: 项目经理
  - plan_start_date: 计划开始
  - plan_end_date: 计划结束

# 项目详情
GET /api/v1/projects/{id}
Response:
  - basic_info: 基本信息
  - team: 团队信息
  - milestones: 里程碑
  - progress: 进度信息
  - cost: 成本信息

# 项目仪表盘
GET /api/v1/projects/{id}/dashboard
Response:
  - progress: 进度数据
  - milestone_status: 里程碑状态
  - risk_alerts: 风险预警
  - team_workload: 团队负荷
  - material_status: 物料状态
  - payment_status: 收款状态

# 项目健康度
GET /api/v1/projects/{id}/health
Response:
  - overall: 综合健康度
  - spi: 进度绩效指数
  - cpi: 成本绩效指数
  - overdue_tasks: 逾期任务数
  - milestone_risk: 里程碑风险
```

#### 4.3.2 任务管理API

```yaml
# WBS任务树
GET /api/v1/tasks/{project_id}/wbs
Response:
  - tasks: WBS树形结构

# 甘特图数据
GET /api/v1/tasks/{project_id}/gantt
Response:
  - tasks: 任务列表(含依赖)
  - links: 依赖关系

# 计算关键路径
POST /api/v1/tasks/{project_id}/calculate-cpm
Response:
  - critical_tasks: 关键任务
  - project_duration: 项目工期
  - float_info: 浮动时间

# 更新任务进度
PUT /api/v1/tasks/{id}/progress
Body:
  - progress_rate: 进度百分比
  - actual_start_date: 实际开始
  - actual_end_date: 实际结束
  - status: 状态
  - remark: 备注

# 我的任务
GET /api/v1/tasks/my-tasks
Query:
  - status: 状态
  - start_date: 开始日期
  - end_date: 结束日期
```

#### 4.3.3 采购管理API

```yaml
# 采购订单列表
GET /api/v1/purchase/orders
Query:
  - project_id: 项目ID
  - supplier_id: 供应商ID
  - status: 状态

# 创建采购订单
POST /api/v1/purchase/orders
Body:
  - project_id: 项目ID
  - supplier_id: 供应商ID
  - expect_date: 预计到货
  - items: 物料明细列表

# 登记到货
POST /api/v1/purchase/orders/{id}/delivery
Body:
  - items: 到货明细
    - item_id: 明细ID
    - delivery_qty: 到货数量
    - delivery_date: 到货日期

# 缺料预警列表
GET /api/v1/purchase/shortage-alerts
Query:
  - project_id: 项目ID
Response:
  - shortage_items: 缺料物料列表
  - kit_rate: 齐套率
```

#### 4.3.4 设计变更API

```yaml
# 创建ECN
POST /api/v1/ecn
Body:
  - project_id: 项目ID
  - ecn_type: 变更类型
  - urgency: 紧急程度
  - change_reason: 变更原因
  - change_content: 变更内容
  - bom_changes: BOM变更明细

# ECN影响评估
GET /api/v1/ecn/{id}/impact
Response:
  - cost_impact: 成本影响
  - schedule_impact_days: 交期影响
  - affected_tasks: 影响的任务
  - affected_purchases: 影响的采购
  - risk_level: 风险等级

# ECN审批
POST /api/v1/ecn/{id}/approve
Body:
  - action: approve/reject
  - comment: 审批意见

# ECN执行
POST /api/v1/ecn/{id}/execute
Body:
  - execute_remark: 执行备注
```

---

## 五、前端页面设计

### 5.1 页面结构

```
src/
├── views/
│   ├── dashboard/              # 工作台
│   │   └── index.vue
│   ├── project/                # 项目管理
│   │   ├── list.vue           # 项目列表
│   │   ├── kanban.vue         # 项目看板
│   │   ├── detail.vue         # 项目详情
│   │   └── create.vue         # 创建项目
│   ├── task/                   # 任务管理
│   │   ├── wbs.vue            # WBS分解
│   │   ├── gantt.vue          # 甘特图
│   │   ├── my-tasks.vue       # 我的任务
│   │   └── board.vue          # 任务看板
│   ├── bom/                    # BOM管理
│   │   ├── list.vue           # BOM列表
│   │   └── editor.vue         # BOM编辑
│   ├── purchase/               # 采购管理
│   │   ├── orders.vue         # 采购订单
│   │   ├── delivery.vue       # 到货管理
│   │   └── shortage.vue       # 缺料预警
│   ├── outsource/              # 外协管理
│   │   ├── orders.vue         # 外协订单
│   │   └── print.vue          # 打印外协单
│   ├── ecn/                    # 设计变更
│   │   ├── list.vue           # 变更列表
│   │   ├── create.vue         # 发起变更
│   │   └── detail.vue         # 变更详情
│   ├── timesheet/              # 工时管理
│   │   ├── fill.vue           # 工时填报
│   │   └── approve.vue        # 工时审批
│   ├── workload/               # 负荷管理
│   │   ├── team.vue           # 团队负荷
│   │   └── heatmap.vue        # 负荷热力图
│   ├── alert/                  # 预警中心
│   │   └── center.vue
│   ├── payment/                # 收款管理
│   │   └── plan.vue
│   ├── service/                # 售后管理
│   │   ├── orders.vue         # 工单列表
│   │   └── detail.vue         # 工单详情
│   ├── knowledge/              # 知识库
│   │   ├── list.vue
│   │   └── article.vue
│   ├── report/                 # 报表中心
│   │   └── center.vue
│   └── system/                 # 系统管理
│       ├── user.vue
│       ├── role.vue
│       ├── dept.vue
│       └── config.vue
```

### 5.2 工作台设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              工作台                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ 进行中项目   │  │  待处理预警  │  │  今日任务    │  │  本周工时    │        │
│  │     12      │  │      5      │  │      8      │  │   32/40h   │        │
│  │  ▲ 2       │  │   🔴3 🟡2   │  │  完成3/待做5 │  │    80%     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                             │
│  ┌──────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │          项目健康度分布           │  │         预警趋势              │  │
│  │                                  │  │                                │  │
│  │   🟢 正常: 8个 (67%)             │  │    ▲                           │  │
│  │   🟡 关注: 3个 (25%)             │  │   /  \    ───  本周            │  │
│  │   🔴 预警: 1个 (8%)              │  │  /    \  ╲                     │  │
│  │                                  │  │ ╱      ╲__╲__  上周           │  │
│  │      [饼图]                      │  │                                │  │
│  └──────────────────────────────────┘  └────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────┐  ┌────────────────────────────────┐  │
│  │            今日待办               │  │       预警提醒                 │  │
│  │                                  │  │                                │  │
│  │  □ 完成XX项目机械设计评审        │  │  🔴 PJ250708001 缺料预警       │  │
│  │  □ 更新YY项目进度                │  │     传感器预计延期3天          │  │
│  │  □ 审批ZZ的工时单                │  │                                │  │
│  │  ☑ 回复客户技术问题              │  │  🟡 PJ250709002 进度滞后       │  │
│  │                                  │  │     SPI=0.88 需关注            │  │
│  └──────────────────────────────────┘  └────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 项目看板设计

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             项目看板                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  [筛选] 客户▼ 项目经理▼ 健康度▼    [视图] 看板 | 列表 | 卡片               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  立项   │ │  设计   │ │  采购   │ │  装配   │ │  调试   │ │  交付   │  │
│  │  (2)    │ │  (4)    │ │  (3)    │ │  (2)    │ │  (1)    │ │  (0)    │  │
│  ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤  │
│  │         │ │         │ │         │ │         │ │         │ │         │  │
│  │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │ │         │  │
│  │ │PJ001│ │ │ │PJ003│ │ │ │PJ005│ │ │ │PJ008│ │ │ │PJ010│ │ │         │  │
│  │ │🟢80%│ │ │ │🟡65%│ │ │ │🔴45%│ │ │ │🟢70%│ │ │ │🟢95%│ │ │         │  │
│  │ │客户A │ │ │ │客户B │ │ │ │客户C │ │ │ │客户D │ │ │ │客户E │ │ │         │  │
│  │ └─────┘ │ │ └─────┘ │ │ └─────┘ │ │ └─────┘ │ │ └─────┘ │ │         │  │
│  │         │ │         │ │         │ │         │ │         │ │         │  │
│  │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │ │ ┌─────┐ │ │         │ │         │  │
│  │ │PJ002│ │ │ │PJ004│ │ │ │PJ006│ │ │ │PJ009│ │ │         │ │         │  │
│  │ │🟢50%│ │ │ │🟢75%│ │ │ │🟡55%│ │ │ │🟡60%│ │ │         │ │         │  │
│  │ └─────┘ │ │ └─────┘ │ │ └─────┘ │ │ └─────┘ │ │         │ │         │  │
│  │         │ │         │ │         │ │         │ │         │ │         │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 六、核心业务流程

### 6.1 项目全生命周期流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        项目全生命周期管理流程                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  销售签单 ──→ 立项评审 ──→ 项目启动 ──→ 设计阶段 ──→ 采购阶段                │
│     │           │           │           │           │                      │
│     ▼           ▼           ▼           ▼           ▼                      │
│  [合同录入]  [PM分配]    [WBS分解]   [出BOM]     [下采购单]                  │
│  [收款计划]  [团队组建]  [里程碑]    [设计评审]  [外协下单]                  │
│             [风险识别]  [进度计划]  [ECN管理]   [到货跟踪]                  │
│                                                                             │
│  ──→ 装配阶段 ──→ 调试阶段 ──→ 交付阶段 ──→ 结项阶段                        │
│        │           │           │           │                               │
│        ▼           ▼           ▼           ▼                               │
│    [机械装配]   [软件调试]   [客户验收]   [项目复盘]                         │
│    [电气接线]   [联调测试]   [培训交接]   [成本核算]                         │
│    [齐套检查]   [内部验收]   [尾款收取]   [知识沉淀]                         │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│                                                                             │
│  贯穿全程：进度监控 │ 预警处理 │ 工时填报 │ 变更管理 │ 问题跟踪              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 设计变更(ECN)流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           设计变更流程 (ECN)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                        变更来源                                              │
│            ┌──────────────┼──────────────┐                                  │
│            ▼              ▼              ▼                                  │
│       客户需求变更    内部设计优化    供应问题变更                            │
│            │              │              │                                  │
│            └──────────────┼──────────────┘                                  │
│                           ▼                                                 │
│                  ┌─────────────────┐                                        │
│                  │  变更申请提交   │                                        │
│                  │  填写变更申请单 │                                        │
│                  └────────┬────────┘                                        │
│                           │                                                 │
│                           ▼                                                 │
│  ┌────────────────────────────────────────────────────────────────┐        │
│  │                      变更影响评估                               │        │
│  │  • 技术影响评估（图纸、程序）                                   │        │
│  │  • 成本影响评估（物料成本变化）                                 │        │
│  │  • 交期影响评估（工期变化）                                     │        │
│  │  • 采购影响评估（已下单物料处理）                               │        │
│  └────────────────────────┬───────────────────────────────────────┘        │
│                           │                                                 │
│                           ▼                                                 │
│                  ┌─────────────────┐                                        │
│                  │    变更审批     │                                        │
│                  └────────┬────────┘                                        │
│                    ┌──────┴──────┐                                          │
│                    ▼             ▼                                          │
│              ┌──────────┐  ┌──────────┐                                     │
│              │   批准   │  │   拒绝   │                                     │
│              └────┬─────┘  └────┬─────┘                                     │
│                   │             │                                           │
│                   ▼             ▼                                           │
│  ┌────────────────────────┐  ┌────────────────┐                            │
│  │      变更执行          │  │  记录拒绝原因  │                            │
│  │  • 更新设计图纸        │  │  关闭变更单    │                            │
│  │  • 更新BOM清单         │  └────────────────┘                            │
│  │  • 调整采购订单        │                                                 │
│  │  • 更新项目计划        │                                                 │
│  │  • 通知相关人员        │                                                 │
│  └────────────┬───────────┘                                                 │
│               │                                                             │
│               ▼                                                             │
│  ┌────────────────────────┐                                                 │
│  │      变更验证关闭      │                                                 │
│  │  • 验证变更效果        │                                                 │
│  │  • 关闭变更单          │                                                 │
│  │  • 归档变更记录        │                                                 │
│  └────────────────────────┘                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 缺料预警处理流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           缺料预警处理流程                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │                    系统每日自动检查                                  │    │
│  │                                                                     │    │
│  │  1. 获取所有进行中项目的BOM                                          │    │
│  │  2. 对比采购订单到货状态                                             │    │
│  │  3. 计算：预计到货日 vs 计划装配日 - 缓冲天数(3天)                    │    │
│  │  4. 识别可能影响生产的物料                                           │    │
│  └──────────────────────────────┬─────────────────────────────────────┘    │
│                                 │                                          │
│                                 ▼                                          │
│                    ┌────────────────────────┐                              │
│                    │    发现缺料风险？       │                              │
│                    └───────────┬────────────┘                              │
│                        是 │        │ 否                                    │
│                           ▼        └──→ [结束]                             │
│                    ┌────────────────────────┐                              │
│                    │   创建缺料预警          │                              │
│                    │   评估影响等级          │                              │
│                    └───────────┬────────────┘                              │
│                                │                                           │
│              ┌─────────────────┼─────────────────┐                         │
│              │                 │                 │                         │
│              ▼                 ▼                 ▼                         │
│        ┌──────────┐     ┌──────────┐     ┌──────────┐                     │
│        │ 🔴 红灯   │     │ 🟡 黄灯   │     │ 🟢 绿灯   │                     │
│        │ 已影响    │     │ 3天内    │     │ 3天后    │                     │
│        │ 生产      │     │ 将影响   │     │ 可能     │                     │
│        └────┬─────┘     └────┬─────┘     └────┬─────┘                     │
│             │                │                │                            │
│             ▼                ▼                ▼                            │
│        [通知PM]          [通知采购]      [记录跟踪]                         │
│        [通知部门经理]    [通知PM]                                           │
│        [企微推送]        [企微推送]                                         │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         预警处理流程                                 │   │
│  │                                                                      │   │
│  │  1. 采购认领预警                                                     │   │
│  │  2. 联系供应商确认交期                                               │   │
│  │  3. 制定应对措施：                                                   │   │
│  │     - 催货                                                           │   │
│  │     - 寻找替代供应商                                                 │   │
│  │     - 寻找替代物料                                                   │   │
│  │     - 调整项目计划                                                   │   │
│  │  4. 更新预警状态                                                     │   │
│  │  5. 关闭预警                                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 七、实施计划

### 7.1 总体规划

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           实施路线图                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  第0期(1个月)          第一期(3个月)         第二期(3个月)                    │
│  基础建设              基础平台              协同与变更                        │
│     │                    │                    │                             │
│     ▼                    ▼                    ▼                             │
│  ┌────────┐          ┌────────────┐      ┌────────────┐                    │
│  │• 编码规范│          │• 用户权限  │      │• ECN变更   │                    │
│  │• 流程梳理│          │• 主数据    │      │• 外协管理  │                    │
│  │• 数据迁移│          │• 项目管理  │      │• 资源排程  │                    │
│  │• 环境搭建│          │• 任务管理  │      │• 收款管理  │                    │
│  └────────┘          │• BOM采购   │      │• 消息通知  │                    │
│                       │• 预警系统  │      └────────────┘                    │
│                       └────────────┘                                        │
│                                                                             │
│  第三期(3个月)         持续优化                                              │
│  售后与沉淀                                                                  │
│     │                                                                       │
│     ▼                                                                       │
│  ┌────────────┐                                                             │
│  │• 售后工单  │                                                             │
│  │• 项目复盘  │                                                             │
│  │• 知识库    │                                                             │
│  │• 成本核算  │                                                             │
│  │• BI报表    │                                                             │
│  └────────────┘                                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 第一期详细计划

| Sprint | 周期 | 主要功能 | 交付物 |
|--------|------|---------|--------|
| Sprint 1 | 2周 | 系统基础架构 | 登录认证、用户管理、角色权限 |
| Sprint 2 | 2周 | 主数据管理 | 客户、供应商、物料档案管理 |
| Sprint 3 | 2周 | 项目管理基础 | 项目CRUD、列表、看板 |
| Sprint 4 | 2周 | 任务管理 | WBS分解、甘特图、任务依赖 |
| Sprint 5 | 2周 | BOM与采购 | BOM管理、采购订单、到货管理 |
| Sprint 6 | 2周 | 预警系统 | 缺料预警、进度预警、消息推送 |

### 7.3 里程碑

| 阶段 | 里程碑 | 验收标准 |
|------|--------|---------|
| 第0期 | 基础建设完成 | 编码规范定稿、历史数据迁移完成、环境搭建完成 |
| 第一期 | 基础平台上线 | 所有在制项目录入、缺料预警上线、项目看板上线 |
| 第二期 | 协同能力上线 | ECN100%走系统、外协跟踪上线、企微通知上线 |
| 第三期 | 全面上线 | 售后工单上线、复盘机制建立、BI报表可用 |

---

## 八、预期收益

### 8.1 量化收益

| 指标 | 当前状态 | 目标 | 提升幅度 |
|------|---------|------|---------|
| 项目交付准时率 | ~70% | 90% | +20% |
| 缺料导致停工比例 | 30% | <5% | -25% |
| 设计变更遗漏率 | 20% | <3% | -17% |
| 外协到货准时率 | 60% | 85% | +25% |
| 项目复盘执行率 | <10% | 80% | +70% |
| 售后响应时间 | 48h+ | <24h | -50% |

### 8.2 管理提升

- **全局可视**：所有项目进度、风险一目了然
- **责任清晰**：每个任务有负责人、有时限
- **数据驱动**：用数据说话，而非凭感觉
- **知识沉淀**：经验不再只在老员工脑袋里
- **协同高效**：跨部门信息透明，减少等待

---

## 附录

### 附录A：编码规则

| 数据对象 | 编码规则 | 示例 |
|----------|----------|------|
| 项目号 | PJyymmddxxx | PJ250708001 |
| 合同号 | HTyymm-xxx | HT2507-001 |
| 机台号 | PJxxx-PNxxx | PJ250708001-PN001 |
| 客户编码 | Cxxxxx | C00001 |
| 供应商编码 | Vxxxxx | V00001 |
| 物料编码 | 类别-中类-小类-规格-流水 | ME-01-01-0001-0001 |
| 采购订单号 | POyymmdd-xxx | PO250710-001 |
| 外协单号 | OTyymmdd-xxx | OT250710-001 |
| ECN变更号 | ECN-PJxxx-xx | ECN-PJ250708001-01 |
| 售后工单号 | SRyymmdd-xxx | SR250715-001 |

### 附录B：项目阶段定义

| 阶段代码 | 阶段名称 | 主要工作 | 典型工期 |
|---------|---------|---------|---------|
| S1 | 需求阶段 | 需求收集、初步方案 | 3-5天 |
| S2 | 技术澄清 | 技术评审、方案确认 | 3-5天 |
| S3 | 立项启动 | 项目立项、团队组建 | 3-5天 |
| S4 | 设计阶段 | 机械/电气/软件设计 | 10-30天 |
| S5 | 采购制造 | 物料采购、外协加工 | 15-30天 |
| S6 | 装配调试 | 组装、调试、测试 | 10-20天 |
| S7 | 厂内验收(FAT) | 内部验收、整改 | 3-7天 |
| S8 | 交付安装(SAT) | 现场安装、调试、培训 | 3-10天 |
| S9 | 结项售后 | 验收、结项、质保 | - |

### 附录C：角色权限矩阵

| 功能 | 管理员 | 总经理 | 部门经理 | PM | 工程师 | 采购 | PMC |
|------|:------:|:------:|:--------:|:--:|:------:|:----:|:---:|
| 创建项目 | ✓ | ✓ | ✓ | - | - | - | - |
| 编辑项目 | ✓ | ✓ | ✓ | ✓ | - | - | - |
| 查看所有项目 | ✓ | ✓ | ✓ | - | - | - | ✓ |
| 创建任务 | ✓ | - | ✓ | ✓ | ✓ | - | - |
| 更新进度 | ✓ | - | ✓ | ✓ | ✓ | - | - |
| 创建采购单 | ✓ | - | - | - | - | ✓ | - |
| 发起ECN | ✓ | - | ✓ | ✓ | ✓ | - | - |
| 审批ECN | ✓ | ✓ | ✓ | ✓ | - | - | - |
| 查看报表 | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ |

---

*文档版本：V1.0*
*编制日期：2025年1月*
*适用企业：非标自动化测试设备制造企业*
