# API集成测试框架

## 概述

本测试框架采用AI辅助生成方式，为非标自动化项目管理系统提供全面的API集成测试。

## 特性

- **统一测试工具类**：`APITestHelper` 提供HTTP请求封装、响应断言、认证管理
- **测试数据生成器**：`TestDataGenerator` 自动生成测试数据
- **模块化测试**：按功能模块组织测试（认证、项目、物料等）
- **完整断言**：状态码、数据内容、字段验证
- **资源跟踪**：自动记录创建的资源用于清理
- **彩色输出**：清晰的测试结果展示

## 目录结构

```
tests/
├── integration/                    # 集成测试目录
│   ├── api_test_helper.py         # 测试工具类
│   ├── test_auth_api.py          # 认证模块测试（原有）
│   ├── test_projects_api_ai.py   # 项目管理测试（AI生成）
│   ├── test_materials_api_ai.py  # 物料管理测试（AI生成）
│   ├── test_purchase_api_ai.py    # 采购管理测试（AI生成）
│   ├── test_acceptance_api_ai.py  # 验收管理测试（AI生成）
│   ├── test_ecn_api_ai.py        # ECN变更管理测试（AI生成）
│   ├── test_alerts_api_ai.py     # 预警管理测试（AI生成）
│   ├── test_sales_api_ai.py       # 销售管理测试（AI生成）
│   ├── test_production_api_ai.py  # 生产管理测试（AI生成）
│   ├── test_outsourcing_api_ai.py # 外协管理测试（AI生成）
│   ├── test_costs_api_ai.py       # 成本管理测试（AI生成）
│   ├── test_progress_api_ai.py    # 进度管理测试（AI生成）
│   ├── test_task_center_api_ai.py # 任务中心测试（AI生成）
│   ├── test_timesheet_api_ai.py   # 工时管理测试（AI生成）
│   ├── test_pmo_api_ai.py         # PMO管理测试（AI生成）
│   ├── test_documents_api_ai.py   # 文档管理测试（AI生成）
│   ├── test_customers_api_ai.py   # 客户管理测试（AI生成）
│   ├── test_suppliers_api_ai.py   # 供应商管理测试（AI生成）
│   ├── test_machines_api_ai.py    # 机台管理测试（AI生成）
│   ├── test_users_api_ai.py       # 用户管理测试（AI生成）
│   ├── test_critical_apis.py     # 关键API测试
│   └── test_project_workflow.py   # 项目工作流测试
├── unit/                          # 单元测试
├── conftest.py                    # pytest配置和fixtures
├── factories.py                    # 测试数据工厂
└── run_api_integration_tests.sh # 测试运行脚本
```

## 核心组件

### 1. APITestHelper

统一的API测试辅助类，提供：

```python
from tests.integration.api_test_helper import APITestHelper

helper = APITestHelper(client)

# 认证管理
token = helper.get_token("admin", "admin123")
headers = helper.get_headers("admin", "admin123")

# HTTP请求
response = helper.get("/projects/", username="admin", password="admin123")
response = helper.post("/projects/", data=project_data, username="admin", password="admin123")
response = helper.put("/projects/1", data=update_data, username="admin", password="admin123")
response = helper.delete("/projects/1", username="admin", password="admin123")

# 响应断言
APITestHelper.assert_success(response, "操作成功")
APITestHelper.assert_status(response, 200, "期望200状态码")
APITestHelper.assert_data_not_empty(response, "数据不为空")
APITestHelper.assert_field_equals(response, "data.id", 123, "ID匹配")

# 资源跟踪
helper.track_resource("project", project_id)
ids = helper.get_created_resource_ids("project")

# 输出辅助
APITestHelper.print_success("操作成功")
APITestHelper.print_error("操作失败")
APITestHelper.print_info("信息")
APITestHelper.print_warning("警告")
```

### 2. TestDataGenerator

测试数据生成器，提供：

```python
from tests.integration.api_test_helper import TestDataGenerator

# 生成项目编码
project_code = TestDataGenerator.generate_project_code()  # PJyymmddHHMMSS

# 生成物料编码
material_code = TestDataGenerator.generate_material_code()  # MAT-YYYYmmddHHMMSS

# 生成订单号
order_no = TestDataGenerator.generate_order_no()  # PO-YYYYmmddHHMMSS

# 生成未来日期
future_date = TestDataGenerator.future_date(days=7)  # YYYY-MM-DD

# 生成过去日期
past_date = TestDataGenerator.past_date(days=7)  # YYYY-MM-DD

# 生成测试邮箱
email = TestDataGenerator.generate_email()  # test-YYYYmmddHHMMSS@example.com
```

## 测试模块

### 认证模块测试

**文件**: `tests/integration/test_auth_api.py`

**覆盖内容**:
- ✅ 用户登录（成功/失败）
- ✅ 令牌生成和验证
- ✅ 密码加密和验证
- ✅ 获取当前用户信息
- ✅ 权限检查
- ✅ 用户管理（CRUD）
- ✅ 角色和权限管理

**运行命令**:
```bash
pytest tests/integration/test_auth_api.py -v
```

### 项目管理测试

**文件**: `tests/integration/test_projects_api_ai.py`

**覆盖内容**:
- ✅ 项目CRUD操作
- ✅ 项目查询和过滤
- ✅ 项目阶段管理
- ✅ 项目成员管理
- ✅ 项目健康度检查
- ✅ 项目统计指标

**运行命令**:
```bash
pytest tests/integration/test_projects_api_ai.py -v
```

### 物料管理测试

**文件**: `tests/integration/test_materials_api_ai.py`

**覆盖内容**:
- ✅ 物料CRUD操作
- ✅ 物料搜索和过滤
- ✅ 供应商管理
- ✅ BOM管理

**运行命令**:
```bash
pytest tests/integration/test_materials_api_ai.py -v
```

### 采购管理测试

**文件**: `tests/integration/test_purchase_api_ai.py`

**覆盖内容**:
- ✅ 采购订单CRUD操作
- ✅ 采购订单项管理
- ✅ 入库操作
- ✅ 供应商订单管理
- ✅ 订单状态管理

**运行命令**:
```bash
pytest tests/integration/test_purchase_api_ai.py -v
```

### 验收管理测试

**文件**: `tests/integration/test_acceptance_api_ai.py`

**覆盖内容**:
- ✅ 验收模板管理（FAT/SAT）
- ✅ 验收模板分类
- ✅ 检查项管理
- ✅ 验收订单管理
- ✅ 验收记录填写
- ✅ 验收报告生成

**运行命令**:
```bash
pytest tests/integration/test_acceptance_api_ai.py -v
```

### ECN变更管理测试

**文件**: `tests/integration/test_ecn_api_ai.py`

**覆盖内容**:
- ✅ ECN基础管理
- ✅ ECN评估管理
- ✅ ECN审批管理
- ✅ ECN执行任务
- ✅ 受影响物料管理
- ✅ 受影响订单管理
- ✅ ECN日志和统计

**运行命令**:
```bash
pytest tests/integration/test_ecn_api_ai.py -v
```

### 预警管理测试

**文件**: `tests/integration/test_alerts_api_ai.py`

**覆盖内容**:
- ✅ 预警规则管理
- ✅ 预警记录管理
- ✅ 预警统计
- ✅ 预警升级
- ✅ 项目健康度快照
- ✅ 预警确认和解决

**运行命令**:
```bash
pytest tests/integration/test_alerts_api_ai.py -v
```

### 成本管理测试

**文件**: `tests/integration/test_costs_api_ai.py`

**覆盖内容**:
- ✅ 成本基础操作 (Basic)
  - 创建/查询/更新项目成本
- ✅ 成本分析和统计 (Analysis)
  - 成本汇总
  - 成本趋势分析
  - 成本对比
- ✅ 人工成本 (Labor)
  - 计算人工成本
  - 人工成本列表
- ✅ 成本分摊 (Allocation)
  - 创建成本分摊
  - 查询分摊记录
- ✅ 预算执行分析 (Budget)
  - 预算偏差
  - 预算执行率
  - 预算预测
- ✅ 成本复盘 (Review)
  - 创建成本复盘
  - 查询复盘记录
- ✅ 成本预警 (Alert)
  - 成本预警列表
  - 成本风险评估
  - 预警规则管理

**运行命令**:
```bash
pytest tests/integration/test_costs_api_ai.py -v
```

### 进度管理测试

**文件**: `tests/integration/test_progress_api_ai.py`

**覆盖内容**:
- ✅ 进度任务管理 (Tasks)
  - 创建/更新任务
  - 完成任务
  - 任务列表查询
- ✅ 计划基线管理 (Baselines)
  - 创建计划基线
  - 查询基线列表
  - 基线对比
- ✅ 进度汇总 (Summary)
  - 进度汇总
  - 任务分布
  - 里程碑进度
- ✅ 进度统计 (Statistics)
  - 进度统计
  - 完成趋势
- ✅ 进度预测 (Forecast)
  - 完成预测
  - 延期风险评估
- ✅ 进度报告 (Reports)
  - 生成进度报告
  - 查询报告列表

**运行命令**:
```bash
pytest tests/integration/test_progress_api_ai.py -v
```

### 任务中心测试

**文件**: `tests/integration/test_task_center_api_ai.py`

**覆盖内容**:
- ✅ 任务概览 (Overview)
  - 任务概览
  - 任务统计
- ✅ 我的任务 (My Tasks)
  - 我的任务列表
  - 按类型查询任务
- ✅ 任务详情 (Detail)
  - 任务详情
  - 任务历史
- ✅ 创建任务 (Create)
  - 创建任务
  - 批量创建任务
- ✅ 更新任务 (Update)
  - 更新任务
  - 批量更新任务
- ✅ 完成任务 (Complete)
  - 完成任务
  - 批量完成任务
- ✅ 转派任务 (Transfer)
  - 转派任务
- ✅ 拒绝任务 (Reject)
  - 拒绝任务
- ✅ 任务评论 (Comments)
  - 添加评论
  - 查询评论列表

**运行命令**:
```bash
pytest tests/integration/test_task_center_api_ai.py -v
```

### 工时管理测试

**文件**: `tests/integration/test_timesheet_api_ai.py`

**覆盖内容**:
- ✅ 工时记录 (Time Entries)
  - 创建工时记录
  - 查询工时列表
  - 更新工时记录
  - 提交工时表
- ✅ 工时审批 (Approval)
  - 待审批工时列表
  - 审批工时
  - 拒绝工时
- ✅ 工时统计 (Statistics)
  - 工时汇总
  - 员工工时统计
  - 项目工时统计
- ✅ 工时报表 (Reports)
  - 生成工时报表
  - 查询报表列表

**运行命令**:
```bash
pytest tests/integration/test_timesheet_api_ai.py -v
```

### PMO管理测试

**文件**: `tests/integration/test_pmo_api_ai.py`

**覆盖内容**:
- ✅ PMO仪表板 (Dashboard)
  - PMO仪表板数据
  - 关键指标
  - 预警汇总
- ✅ 项目组合管理 (Portfolio)
  - 项目组合概览
  - 项目分布
  - 资源利用率
- ✅ 项目健康度监控 (Health Monitor)
  - 健康度矩阵
  - 健康度趋势
  - 风险项目列表
- ✅ PMO报表 (Reports)
  - 生成高管报告
  - 查询报表列表
- ✅ PMO KPI (KPIs)
  - 项目KPI
  - 团队绩效

**运行命令**:
```bash
pytest tests/integration/test_pmo_api_ai.py -v
```

### 销售管理测试

**文件**: `tests/integration/test_sales_api_ai.py`

**覆盖内容**:
- ✅ 线索管理 (Leads)
  - 创建、查询、更新线索
  - 线索跟进记录
  - 线索转商机
- ✅ 商机管理 (Opportunities)
  - 创建、查询商机
  - 更新商机阶段
  - 商机概率管理
- ✅ 报价管理 (Quotes)
  - 创建报价（含版本管理）
  - 报价审批流程
  - 报价列表和详情
- ✅ 销售统计
  - 销售统计数据
  - 销售漏斗分析
  - 销售目标管理

**运行命令**:
```bash
pytest tests/integration/test_sales_api_ai.py -v
```

### 生产管理测试

**文件**: `tests/integration/test_production_api_ai.py`

**覆盖内容**:
- ✅ 车间管理 (Workshops)
  - 创建、查询、更新车间
  - 车间管理信息
- ✅ 工位管理 (Workstations)
  - 创建、查询工位
  - 工位状态管理
- ✅ 生产计划 (Production Plans)
  - 创建生产计划
  - 查询计划详情
  - 更新计划状态
- ✅ 工单管理 (Work Orders)
  - 创建工单
  - 工单派工
  - 更新工单进度
  - 完成工单
- ✅ 工作报表 (Work Reports)
  - 创建工作报表
  - 查询报表列表
- ✅ 生产仪表板
  - 生产统计数据
  - 仪表板数据展示

**运行命令**:
```bash
pytest tests/integration/test_production_api_ai.py -v
```

### 外协管理测试

**文件**: `tests/integration/test_outsourcing_api_ai.py`

**覆盖内容**:
- ✅ 外协供应商 (Vendors)
  - 创建、查询、更新供应商
  - 供应商评级管理
- ✅ 外协订单 (Orders)
  - 创建外协订单
  - 查询订单详情
  - 更新订单状态
  - 取消订单
- ✅ 外协交付 (Deliveries)
  - 创建交付单
  - 查询交付记录
- ✅ 外协质检 (Inspections)
  - 创建质检单
  - 查询质检记录
  - 质检结果管理
- ✅ 外协进度 (Progress)
  - 创建进度更新
  - 查询进度记录
- ✅ 外协付款 (Payments)
  - 创建付款记录
  - 查询付款列表
  - 付款统计

**运行命令**:
```bash
pytest tests/integration/test_outsourcing_api_ai.py -v
```

### 成本管理测试

**文件**: `tests/integration/test_costs_api_ai.py`

**覆盖内容**:
- ✅ 成本基础操作
  - 成本CRUD操作
  - 成本查询和过滤
- ✅ 成本分析
  - 成本汇总分析
  - 成本趋势分析
  - 成本对比分析
- ✅ 人工成本
  - 计算人工成本
  - 查询人工成本记录
- ✅ 成本分摊
  - 创建成本分摊记录
  - 查询分摊明细
- ✅ 预算执行
  - 预算差异分析
  - 执行率计算
  - 预算预测
- ✅ 成本审核
  - 创建成本审核
  - 查询审核记录
- ✅ 成本预警
  - 查询成本预警
  - 成本风险评估
  - 预警规则管理

**运行命令**:
```bash
pytest tests/integration/test_costs_api_ai.py -v
```

### 进度管理测试

**文件**: `tests/integration/test_progress_api_ai.py`

**覆盖内容**:
- ✅ 进度任务管理
  - 任务CRUD操作
  - 更新任务进度
  - 完成任务
- ✅ 基线管理
  - 创建基线
  - 查询基线列表
  - 基线对比
- ✅ 进度汇总
  - 获取进度汇总
  - 任务分布统计
  - 里程碑进度
- ✅ 进度统计
  - 获取统计数据
  - 完成率趋势
- ✅ 进度预测
  - 完成时间预测
  - 延期风险分析
- ✅ 进度报告
  - 生成进度报告
  - 查询报告列表

**运行命令**:
```bash
pytest tests/integration/test_progress_api_ai.py -v
```

### 任务中心测试

**文件**: `tests/integration/test_task_center_api_ai.py`

**覆盖内容**:
- ✅ 任务概览
  - 获取任务概览
  - 任务统计信息
- ✅ 我的任务
  - 查询我的任务列表
  - 按类型筛选
- ✅ 任务详情
  - 获取任务详情
  - 查询任务历史
- ✅ 创建任务
  - 单个创建任务
  - 批量创建任务
- ✅ 更新任务
  - 单个更新任务
  - 批量更新任务
- ✅ 完成任务
  - 单个完成任务
  - 批量完成任务
- ✅ 转移任务
  - 转移给他人
- ✅ 拒绝任务
  - 拒绝接收任务
- ✅ 任务评论
  - 添加评论
  - 查询评论列表

**运行命令**:
```bash
pytest tests/integration/test_task_center_api_ai.py -v
```

### 工时管理测试

**文件**: `tests/integration/test_timesheet_api_ai.py`

**覆盖内容**:
- ✅ 工时记录
  - 创建工时记录
  - 查询工时记录
  - 更新工时记录
  - 提交工时单
- ✅ 工时审批
  - 查询待审批工时
  - 审批通过
  - 审批拒绝
- ✅ 工时统计
  - 工时汇总统计
  - 员工工时统计
  - 项目工时统计
- ✅ 工时报表
  - 生成工时报表
  - 查询报表列表

**运行命令**:
```bash
pytest tests/integration/test_timesheet_api_ai.py -v
```

### PMO管理测试

**文件**: `tests/integration/test_pmo_api_ai.py`

**覆盖内容**:
- ✅ PMO仪表盘
  - 获取仪表盘数据
  - 获取指标数据
  - 获取预警汇总
- ✅ 项目组合管理
  - 项目组合概览
  - 项目分布统计
  - 资源利用率分析
- ✅ 健康度监控
  - 健康度矩阵
  - 健康度趋势
  - 风险项目识别
- ✅ PMO报告
  - 生成高管报告
  - 查询报告列表
- ✅ PMO KPI
  - 项目KPI统计
  - 团队绩效分析

**运行命令**:
```bash
pytest tests/integration/test_pmo_api_ai.py -v
```

### 文档管理测试

**文件**: `tests/integration/test_documents_api_ai.py`

**覆盖内容**:
- ✅ 文档管理
  - 上传文档
  - 查询文档列表
  - 获取文档详情
  - 更新文档
  - 删除文档
  - 下载文档
- ✅ 文件夹管理
  - 创建文件夹
  - 查询文件夹列表
- ✅ 文档权限
  - 授予权限
  - 查询权限列表
- ✅ 文档版本
  - 创建新版本
  - 查询版本历史

**运行命令**:
```bash
pytest tests/integration/test_documents_api_ai.py -v
```

### 客户管理测试

**文件**: `tests/integration/test_customers_api_ai.py`

**覆盖内容**:
- ✅ 客户CRUD操作
  - 创建客户
  - 查询客户列表
  - 获取客户详情
  - 更新客户信息
  - 删除客户
- ✅ 客户关联数据
  - 查询客户项目列表
  - 查询客户订单列表
  - 获取客户统计数据
- ✅ 客户360视图
  - 获取客户全景视图
  - 查询项目概览
  - 查询财务概览

**运行命令**:
```bash
pytest tests/integration/test_customers_api_ai.py -v
```

### 供应商管理测试

**文件**: `tests/integration/test_suppliers_api_ai.py`

**覆盖内容**:
- ✅ 供应商CRUD操作
  - 创建供应商
  - 查询供应商列表
  - 获取供应商详情
  - 更新供应商信息
  - 停用供应商
- ✅ 供应商评级
  - 为供应商评级
  - 查询评级列表
  - 评级汇总统计
- ✅ 供应商物料
  - 添加物料到供应商
  - 查询供应商物料列表
- ✅ 供应商分类
  - 查询供应商分类列表
- ✅ 供应商产品
  - 查询供应商产品列表
- ✅ 供应商质检
  - 创建质检记录
  - 查询质检记录
  - 质检汇总统计

**运行命令**:
```bash
pytest tests/integration/test_suppliers_api_ai.py -v
```

### 机台管理测试

**文件**: `tests/integration/test_machines_api_ai.py`

**覆盖内容**:
- ✅ 机台基本CRUD操作
  - 创建机台
  - 查询机台列表
  - 获取机台详情
  - 更新机台信息
  - 删除机台
  - 更新机台进度
  - 查询机台BOM
  - 查询项目机台汇总
  - 重新计算项目机台数据
- ✅ 服务历史
  - 查询机台服务历史
- ✅ 文档管理
  - 上传机台文档
  - 查询机台文档列表
  - 下载机台文档
  - 查询文档版本列表

**运行命令**:
```bash
pytest tests/integration/test_machines_api_ai.py -v
```

### 用户管理测试

**文件**: `tests/integration/test_users_api_ai.py`

**覆盖内容**:
- ✅ 用户基本CRUD操作
  - 创建用户
  - 查询用户列表
  - 获取用户详情
  - 更新用户信息
  - 删除用户
  - 更新用户角色
- ✅ 用户同步
  - 从员工同步用户
  - 从员工创建用户
  - 切换用户激活状态
  - 重置用户密码
  - 批量切换激活状态
- ✅ 工时分配
  - 获取用户工时分配

**运行命令**:
```bash
pytest tests/integration/test_users_api_ai.py -v
```

## 快速开始

### 1. 安装依赖

```bash
pip install pytest pytest-cov pytest-asyncio httpx
```

### 2. 运行所有测试

```bash
# 使用测试脚本
./tests/run_api_integration_tests.sh

# 或使用pytest直接运行
pytest tests/integration/ -v
```

### 3. 运行特定模块

```bash
# 只运行认证测试
./tests/run_api_integration_tests.sh auth

# 只运行项目管理测试
./tests/run_api_integration_tests.sh projects

# 只运行物料管理测试
./tests/run_api_integration_tests.sh materials

# 只运行采购管理测试
./tests/run_api_integration_tests.sh purchase

# 只运行验收管理测试
./tests/run_api_integration_tests.sh acceptance

# 只运行ECN变更管理测试
./tests/run_api_integration_tests.sh ecn

# 只运行预警管理测试
./tests/run_api_integration_tests.sh alerts

# 只运行销售管理测试
./tests/run_api_integration_tests.sh sales

# 只运行生产管理测试
./tests/run_api_integration_tests.sh production

# 只运行外协管理测试
./tests/run_api_integration_tests.sh outsourcing

# 只运行成本管理测试
./tests/run_api_integration_tests.sh costs

# 只运行进度管理测试
./tests/run_api_integration_tests.sh progress

# 只运行任务中心测试
./tests/run_api_integration_tests.sh tasks

# 只运行工时管理测试
./tests/run_api_integration_tests.sh timesheet

# 只运行PMO管理测试
./tests/run_api_integration_tests.sh pmo

# 只运行文档管理测试
./tests/run_api_integration_tests.sh documents

# 只运行客户管理测试
./tests/run_api_integration_tests.sh customers

# 只运行供应商管理测试
./tests/run_api_integration_tests.sh suppliers

# 只运行机台管理测试
./tests/run_api_integration_tests.sh machines

# 只运行用户管理测试
./tests/run_api_integration_tests.sh users

# 只运行关键API测试
./tests/run_api_integration_tests.sh critical

# 只运行项目工作流测试
./tests/run_api_integration_tests.sh workflow
```

### 4. 生成测试覆盖率报告

```bash
# 使用测试脚本
./tests/run_api_integration_tests.sh coverage

# 或直接运行pytest
pytest tests/integration/ --cov=app --cov-report=html
```

覆盖率报告将生成在 `htmlcov/index.html`

### 5. 清理测试缓存

```bash
./tests/run_api_integration_tests.sh clean
```

## 编写新测试

### 基本模板

```python
# -*- coding: utf-8 -*-
"""
模块API集成测试（AI辅助生成）
"""

import pytest
from datetime import datetime

from tests.integration.api_test_helper import APITestHelper, TestDataGenerator


@pytest.mark.integration
class TestModuleName:
    """模块名称测试"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """测试设置"""
        self.client = client
        self.helper = APITestHelper(client)

    def test_create_resource(self, admin_token):
        """测试创建资源"""
        self.helper.print_info("测试: 创建资源")

        # 准备测试数据
        test_data = {
            "field1": "value1",
            "field2": TestDataGenerator.generate_material_code(),
        }

        # 发送请求
        response = self.helper.post(
            "/endpoint/",
            test_data,
            username="admin",
            password="admin123"
        )

        # 打印信息
        self.helper.print_request("POST", "/endpoint/", test_data)
        self.helper.print_response(response)

        # 断言
        APITestHelper.assert_success(response, "创建资源成功")
        APITestHelper.assert_data_not_empty(response, "响应数据不为空")
        APITestHelper.assert_field_equals(response, "data.field1", "value1")

        # 跟踪资源
        resource_id = response["data"].get("id")
        if resource_id:
            self.helper.track_resource("resource_type", resource_id)

        self.helper.print_success("✓ 资源创建成功")
```

### 使用fixtures

项目提供了丰富的fixtures：

```python
# 用户fixtures
def test_with_admin_user(admin_token):
    """使用管理员用户"""
    pass

def test_with_normal_user(normal_user_token):
    """使用普通用户"""
    pass

# 数据fixtures
def test_with_project(test_project):
    """使用测试项目"""
    pass

def test_with_customer(test_customer):
    """使用测试客户"""
    pass

def test_with_material(test_material):
    """使用测试物料"""
    pass
```

## 测试配置

### pytest.ini

```ini
[pytest]
minversion = 6.0
addopts =
    -ra
    -v
    -l
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
    -W ignore::DeprecationWarning
filterwarnings =
    ignore::pydantic.warnings.PydanticDeprecatedSince20
testpaths =
    tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试
    api: API测试
```

## 最佳实践

### 1. 测试命名

- 使用描述性的测试名称
- 采用 `test_功能_场景` 的格式
- 示例：`test_create_project_success`, `test_login_wrong_password`

### 2. 测试结构

每个测试函数应该包含：
1. 测试设置（使用fixtures或setup方法）
2. 准备测试数据
3. 执行API请求
4. 断言验证
5. 清理（自动或手动）

### 3. 数据隔离

- 每个测试使用独立的测试数据
- 使用fixtures确保数据可用
- 测试后清理创建的资源

### 4. 断言使用

优先使用 `APITestHelper` 的断言方法：
- `assert_success()`: 验证2xx状态码
- `assert_status()`: 验证特定状态码
- `assert_data_not_empty()`: 验证响应数据
- `assert_field_equals()`: 验证字段值

### 5. 错误处理

- 使用 `pytest.skip()` 跳过缺少前置条件的测试
- 使用 `try-except` 捕获预期的异常
- 提供清晰的错误消息

## CI/CD集成

### GitHub Actions示例

```yaml
name: API Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run integration tests
      run: ./tests/run_api_integration_tests.sh

    - name: Upload coverage reports
      uses: codecov/codecov-action@v2
      with:
        files: ./coverage/integration.xml
```

## 故障排查

### 问题1: 数据库连接失败

**原因**: 测试数据库未初始化

**解决**:
```bash
python3 init_db.py
```

### 问题2: 认证失败

**原因**: 默认用户不存在或密码错误

**解决**:
- 检查 `conftest.py` 中的用户创建逻辑
- 确认数据库中存在admin用户（密码：admin123）

### 问题3: 端点404

**原因**: API路径错误或路由未注册

**解决**:
- 检查 `app/api/v1/api.py` 中的路由配置
- 验证端点前缀和路径

### 问题4: 依赖错误

**原因**: 缺少必要的Python包

**解决**:
```bash
pip install -r requirements.txt
```

## 扩展测试框架

### 添加新模块测试

1. 在 `tests/integration/` 创建新测试文件
2. 继承测试模板结构
3. 使用 `APITestHelper` 和 `TestDataGenerator`
4. 添加到运行脚本

### 添加自定义断言

在 `api_test_helper.py` 中添加新方法：

```python
@staticmethod
def assert_custom_condition(response: Dict[str, Any], condition: callable):
    """自定义断言"""
    data = response.get("data")
    assert condition(data), "自定义条件失败"
```

## 维护建议

1. **定期更新测试**: 随着API变化更新测试用例
2. **保持覆盖率**: 目标覆盖率 > 70%
3. **添加新测试**: 新功能必须包含测试
4. **修复失败测试**: 优先修复CI中的失败测试
5. **文档更新**: 保持README文档同步

## 贡献指南

欢迎提交测试改进和新增测试：

1. Fork 项目
2. 创建特性分支
3. 添加测试或修复问题
4. 运行测试确保通过
5. 提交Pull Request

## 许可证

[待添加]

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目Issues: [GitHub Issues URL]
- 邮件: [项目邮箱]
