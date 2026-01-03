# 开发任务列表 - 非标自动化项目管理系统

> 最后更新：2026-01-03
> 状态说明：✅ 已完成 | ⚠️ 部分完成 | ❌ 待开发 | 🚧 开发中

---

## 一、整体开发路线图（18个月）

```
第0期（基础建设）   第一期（基础平台）   第二期（协同变更）   第三期（售后沉淀）
     2个月               4个月               6个月               6个月
   2025.7-8           2025.9-12           2026.1-6           2026.7-12
       │                  │                   │                   │
       ▼                  ▼                   ▼                   ▼
   编码体系           主数据管理          设计变更            售后工单
   流程梳理           项目管理            外协管理            项目复盘
   数据清洗           生产进度            资源排程            知识库
   模板准备           采购物料            收款管理            成本核算
                      异常管理            移动端应用          BI报表
```

---

## 二、当前完成状态总览

| 层级 | 模块 | 完成度 | 说明 |
|------|------|:------:|------|
| 数据库模型 | 全部 ORM 模型 | ✅ 100% | 已完成所有模型定义 |
| 数据库迁移 | SQL 迁移脚本 | ✅ 100% | SQLite + MySQL 双版本 |
| Pydantic Schema | API 数据模式 | ✅ 100% | 请求/响应模式已定义 |
| API 端点 | 项目管理 | ⚠️ 20% | 仅完成基础 CRUD |
| API 端点 | 其他模块 | ❌ 0% | 待开发 |
| 前端界面 | Web UI | ❌ 0% | 未开始 |
| 移动端 | 企微/钉钉 | ❌ 0% | 未开始 |
| 系统集成 | ERP/PDM | ❌ 0% | 未开始 |

---

## 三、第0期：基础建设任务（2个月）

### 3.1 编码体系设计

| 序号 | 任务 | 优先级 | 状态 | 交付物 |
|:----:|------|:------:|:----:|--------|
| 0.1.1 | 项目编码规则定义 (PJyymmddxxx) | 🔴 P0 | ✅ | 编码规范文档 |
| 0.1.2 | 物料编码规则定义 (类别+规格+流水) | 🔴 P0 | ✅ | 编码规范文档 |
| 0.1.3 | 供应商编码规则 (Vxxxxx) | 🔴 P0 | ✅ | 编码规范文档 |
| 0.1.4 | 客户编码规则 (Cxxxxx) | 🔴 P0 | ✅ | 编码规范文档 |
| 0.1.5 | ECN 编码规则 (ECN-PJxxx-xx) | 🔴 P0 | ✅ | 编码规范文档 |
| 0.1.6 | 外协单编码规则 (OT-yymmdd-xxx) | 🔴 P0 | ✅ | 编码规范文档 |

### 3.2 三维状态体系设计

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| 0.2.1 | 阶段(Stage) S1-S9 定义 | 🔴 P0 | ✅ | 9阶段生命周期 |
| 0.2.2 | 状态(Status) ST01-ST30 定义 | 🔴 P0 | ✅ | 32个子状态 |
| 0.2.3 | 健康度(Health) H1-H4 定义 | 🔴 P0 | ✅ | 红黄绿灰 |
| 0.2.4 | 状态流转规则定义 | 🔴 P0 | ✅ | 状态机设计 |
| 0.2.5 | 健康度自动计算规则 | 🟡 P1 | ❌ | 待开发服务 |

### 3.3 业务流程梳理

| 序号 | 任务 | 优先级 | 状态 | 交付物 |
|:----:|------|:------:|:----:|--------|
| 0.3.1 | 项目全生命周期流程 | 🔴 P0 | ✅ | 流程图文档 |
| 0.3.2 | 设计变更(ECN)流程 | 🔴 P0 | ✅ | 流程图文档 |
| 0.3.3 | 采购与到货流程 | 🔴 P0 | ✅ | 流程图文档 |
| 0.3.4 | 外协管理流程 | 🔴 P0 | ✅ | 流程图文档 |
| 0.3.5 | 验收管理流程 (FAT/SAT) | 🔴 P0 | ✅ | 流程图文档 |
| 0.3.6 | 预警与异常处理流程 | 🔴 P0 | ✅ | 流程图文档 |

---

## 四、第一期：基础平台任务（4个月）

### 4.1 用户认证与权限 API（M1-W1~W2）

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.1.1 | 用户登录 API | 🔴 P0 | ❌ | `POST /auth/login` | 返回 JWT Token |
| 1.1.2 | 用户登出 API | 🔴 P0 | ❌ | `POST /auth/logout` | 使 Token 失效 |
| 1.1.3 | Token 刷新 API | 🔴 P0 | ❌ | `POST /auth/refresh` | 刷新访问令牌 |
| 1.1.4 | 获取当前用户信息 | 🔴 P0 | ❌ | `GET /auth/me` | 返回用户+权限 |
| 1.1.5 | 修改密码 API | 🟡 P1 | ❌ | `PUT /auth/password` | 密码修改 |
| 1.1.6 | 用户列表 API | 🔴 P0 | ❌ | `GET /users` | 分页+筛选 |
| 1.1.7 | 创建用户 API | 🔴 P0 | ❌ | `POST /users` | 管理员创建 |
| 1.1.8 | 更新用户 API | 🔴 P0 | ❌ | `PUT /users/{id}` | 修改用户信息 |
| 1.1.9 | 删除/禁用用户 | 🟡 P1 | ❌ | `DELETE /users/{id}` | 软删除 |
| 1.1.10 | 角色列表 API | 🔴 P0 | ❌ | `GET /roles` | 获取角色列表 |
| 1.1.11 | 创建角色 API | 🔴 P0 | ❌ | `POST /roles` | 创建新角色 |
| 1.1.12 | 角色权限分配 | 🔴 P0 | ❌ | `PUT /roles/{id}/permissions` | 分配权限 |
| 1.1.13 | 用户角色分配 | 🔴 P0 | ❌ | `PUT /users/{id}/roles` | 分配角色 |
| 1.1.14 | 权限列表 API | 🟡 P1 | ❌ | `GET /permissions` | 获取权限列表 |

### 4.2 主数据管理 API（M1-W2~W4）

#### 4.2.1 客户管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.2.1 | 客户列表 API | 🔴 P0 | ❌ | `GET /customers` |
| 1.2.2 | 客户详情 API | 🔴 P0 | ❌ | `GET /customers/{id}` |
| 1.2.3 | 创建客户 API | 🔴 P0 | ❌ | `POST /customers` |
| 1.2.4 | 更新客户 API | 🔴 P0 | ❌ | `PUT /customers/{id}` |
| 1.2.5 | 删除客户 API | 🟡 P1 | ❌ | `DELETE /customers/{id}` |
| 1.2.6 | 客户项目列表 | 🟡 P1 | ❌ | `GET /customers/{id}/projects` |

#### 4.2.2 供应商管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.2.7 | 供应商列表 API | 🔴 P0 | ❌ | `GET /suppliers` |
| 1.2.8 | 供应商详情 API | 🔴 P0 | ❌ | `GET /suppliers/{id}` |
| 1.2.9 | 创建供应商 API | 🔴 P0 | ❌ | `POST /suppliers` |
| 1.2.10 | 更新供应商 API | 🔴 P0 | ❌ | `PUT /suppliers/{id}` |
| 1.2.11 | 供应商评级 API | 🟡 P1 | ❌ | `PUT /suppliers/{id}/rating` |
| 1.2.12 | 供应商物料列表 | 🟡 P1 | ❌ | `GET /suppliers/{id}/materials` |

#### 4.2.3 部门与组织

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.2.13 | 部门树 API | 🔴 P0 | ❌ | `GET /departments/tree` |
| 1.2.14 | 创建部门 API | 🔴 P0 | ❌ | `POST /departments` |
| 1.2.15 | 更新部门 API | 🟡 P1 | ❌ | `PUT /departments/{id}` |
| 1.2.16 | 部门人员列表 | 🟡 P1 | ❌ | `GET /departments/{id}/users` |

### 4.3 项目管理 API（M2）

#### 4.3.1 项目基础 CRUD

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.3.1 | 项目列表 API | 🔴 P0 | ⚠️ | `GET /projects` | 需完善筛选 |
| 1.3.2 | 项目详情 API | 🔴 P0 | ⚠️ | `GET /projects/{id}` | 需关联数据 |
| 1.3.3 | 创建项目 API | 🔴 P0 | ⚠️ | `POST /projects` | 需完善字段 |
| 1.3.4 | 更新项目 API | 🔴 P0 | ⚠️ | `PUT /projects/{id}` | 基本完成 |
| 1.3.5 | 删除项目 API | 🟡 P1 | ❌ | `DELETE /projects/{id}` | 软删除 |
| 1.3.6 | 项目看板 API | 🔴 P0 | ❌ | `GET /projects/board` | 红黄绿灯看板 |
| 1.3.7 | 项目统计 API | 🟡 P1 | ❌ | `GET /projects/stats` | 按状态统计 |

#### 4.3.2 三维状态管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.3.8 | 更新项目阶段 | 🔴 P0 | ❌ | `PUT /projects/{id}/stage` | S1-S9 |
| 1.3.9 | 更新项目状态 | 🔴 P0 | ❌ | `PUT /projects/{id}/status` | ST01-ST30 |
| 1.3.10 | 更新健康度 | 🔴 P0 | ❌ | `PUT /projects/{id}/health` | H1-H4 |
| 1.3.11 | 健康度自动计算 | 🟡 P1 | ❌ | 后台服务 | 规则引擎 |
| 1.3.12 | 状态变更历史 | 🟡 P1 | ❌ | `GET /projects/{id}/status-history` | 追溯 |

#### 4.3.3 机台管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.3.13 | 项目机台列表 | 🔴 P0 | ❌ | `GET /projects/{id}/machines` |
| 1.3.14 | 创建机台 | 🔴 P0 | ❌ | `POST /projects/{id}/machines` |
| 1.3.15 | 更新机台 | 🔴 P0 | ❌ | `PUT /machines/{id}` |
| 1.3.16 | 机台详情 | 🔴 P0 | ❌ | `GET /machines/{id}` |
| 1.3.17 | 机台进度更新 | 🟡 P1 | ❌ | `PUT /machines/{id}/progress` |
| 1.3.18 | 机台 BOM 列表 | 🟡 P1 | ❌ | `GET /machines/{id}/bom` |

#### 4.3.4 项目阶段管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.3.19 | 项目阶段列表 | 🔴 P0 | ❌ | `GET /projects/{id}/stages` |
| 1.3.20 | 初始化项目阶段 | 🔴 P0 | ❌ | `POST /projects/{id}/stages/init` |
| 1.3.21 | 更新阶段进度 | 🔴 P0 | ❌ | `PUT /project-stages/{id}` |
| 1.3.22 | 阶段状态列表 | 🟡 P1 | ❌ | `GET /project-stages/{id}/statuses` |
| 1.3.23 | 更新状态完成 | 🟡 P1 | ❌ | `PUT /project-statuses/{id}/complete` |

#### 4.3.5 里程碑管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.3.24 | 里程碑列表 | 🔴 P0 | ❌ | `GET /projects/{id}/milestones` |
| 1.3.25 | 创建里程碑 | 🔴 P0 | ❌ | `POST /projects/{id}/milestones` |
| 1.3.26 | 更新里程碑 | 🔴 P0 | ❌ | `PUT /milestones/{id}` |
| 1.3.27 | 完成里程碑 | 🔴 P0 | ❌ | `PUT /milestones/{id}/complete` |
| 1.3.28 | 里程碑预警 | 🟡 P1 | ❌ | 后台服务 |

#### 4.3.6 项目成员管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.3.29 | 项目成员列表 | 🟡 P1 | ❌ | `GET /projects/{id}/members` |
| 1.3.30 | 添加项目成员 | 🟡 P1 | ❌ | `POST /projects/{id}/members` |
| 1.3.31 | 更新成员角色 | 🟡 P1 | ❌ | `PUT /project-members/{id}` |
| 1.3.32 | 移除项目成员 | 🟡 P1 | ❌ | `DELETE /project-members/{id}` |

#### 4.3.7 项目成本管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.3.33 | 项目成本列表 | 🟡 P1 | ❌ | `GET /projects/{id}/costs` |
| 1.3.34 | 添加成本记录 | 🟡 P1 | ❌ | `POST /projects/{id}/costs` |
| 1.3.35 | 成本汇总统计 | 🟡 P1 | ❌ | `GET /projects/{id}/costs/summary` |
| 1.3.36 | 成本超支预警 | 🟢 P2 | ❌ | 后台服务 |

#### 4.3.8 项目文档管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.3.37 | 项目文档列表 | 🟢 P2 | ❌ | `GET /projects/{id}/documents` |
| 1.3.38 | 上传文档 | 🟢 P2 | ❌ | `POST /projects/{id}/documents` |
| 1.3.39 | 下载文档 | 🟢 P2 | ❌ | `GET /documents/{id}/download` |
| 1.3.40 | 文档版本管理 | 🟢 P2 | ❌ | `GET /documents/{id}/versions` |

### 4.4 采购与物料 API（M3）

#### 4.4.1 物料主数据

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.4.1 | 物料列表 API | 🔴 P0 | ❌ | `GET /materials` |
| 1.4.2 | 物料详情 API | 🔴 P0 | ❌ | `GET /materials/{id}` |
| 1.4.3 | 创建物料 API | 🔴 P0 | ❌ | `POST /materials` |
| 1.4.4 | 更新物料 API | 🔴 P0 | ❌ | `PUT /materials/{id}` |
| 1.4.5 | 物料分类列表 | 🔴 P0 | ❌ | `GET /material-categories` |
| 1.4.6 | 物料供应商关联 | 🟡 P1 | ❌ | `GET /materials/{id}/suppliers` |
| 1.4.7 | 物料替代关系 | 🟢 P2 | ❌ | `GET /materials/{id}/alternatives` |

#### 4.4.2 BOM 管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.4.8 | BOM 列表 API | 🔴 P0 | ❌ | `GET /machines/{id}/bom` |
| 1.4.9 | 创建 BOM | 🔴 P0 | ❌ | `POST /machines/{id}/bom` |
| 1.4.10 | BOM 明细列表 | 🔴 P0 | ❌ | `GET /bom/{id}/items` |
| 1.4.11 | 添加 BOM 明细 | 🔴 P0 | ❌ | `POST /bom/{id}/items` |
| 1.4.12 | 更新 BOM 明细 | 🔴 P0 | ❌ | `PUT /bom-items/{id}` |
| 1.4.13 | BOM 版本管理 | 🟡 P1 | ❌ | `POST /bom/{id}/release` |
| 1.4.14 | BOM 导入 (Excel) | 🟡 P1 | ❌ | `POST /bom/{id}/import` |
| 1.4.15 | BOM 导出 (Excel) | 🟡 P1 | ❌ | `GET /bom/{id}/export` |

#### 4.4.3 采购订单

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.4.16 | 采购订单列表 | 🔴 P0 | ❌ | `GET /purchase-orders` |
| 1.4.17 | 采购订单详情 | 🔴 P0 | ❌ | `GET /purchase-orders/{id}` |
| 1.4.18 | 创建采购订单 | 🔴 P0 | ❌ | `POST /purchase-orders` |
| 1.4.19 | 更新采购订单 | 🔴 P0 | ❌ | `PUT /purchase-orders/{id}` |
| 1.4.20 | 采购订单审批 | 🔴 P0 | ❌ | `PUT /purchase-orders/{id}/approve` |
| 1.4.21 | 采购订单明细 | 🔴 P0 | ❌ | `GET /purchase-orders/{id}/items` |
| 1.4.22 | 从 BOM 生成采购需求 | 🟡 P1 | ❌ | `POST /bom/{id}/generate-pr` |

#### 4.4.4 到货与入库

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.4.23 | 收货记录列表 | 🔴 P0 | ❌ | `GET /goods-receipts` |
| 1.4.24 | 创建收货记录 | 🔴 P0 | ❌ | `POST /goods-receipts` |
| 1.4.25 | 收货明细 | 🔴 P0 | ❌ | `GET /goods-receipts/{id}/items` |
| 1.4.26 | 到货状态更新 | 🔴 P0 | ❌ | `PUT /po-items/{id}/receive` |

#### 4.4.5 齐套率与缺料预警

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.4.27 | 项目齐套率计算 | 🔴 P0 | ❌ | `GET /projects/{id}/kit-rate` |
| 1.4.28 | 机台齐套率计算 | 🔴 P0 | ❌ | `GET /machines/{id}/kit-rate` |
| 1.4.29 | 缺料清单 | 🔴 P0 | ❌ | `GET /projects/{id}/shortage` |
| 1.4.30 | 缺料预警生成 | 🔴 P0 | ❌ | 后台服务 |
| 1.4.31 | 缺料预警列表 | 🔴 P0 | ❌ | `GET /alerts?type=SHORTAGE` |

### 4.5 预警与异常 API（M4）

#### 4.5.1 预警规则

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.5.1 | 预警规则列表 | 🔴 P0 | ❌ | `GET /alert-rules` |
| 1.5.2 | 创建预警规则 | 🔴 P0 | ❌ | `POST /alert-rules` |
| 1.5.3 | 更新预警规则 | 🔴 P0 | ❌ | `PUT /alert-rules/{id}` |
| 1.5.4 | 启用/禁用规则 | 🔴 P0 | ❌ | `PUT /alert-rules/{id}/toggle` |
| 1.5.5 | 预警规则模板 | 🟡 P1 | ❌ | `GET /alert-rule-templates` |

#### 4.5.2 预警记录

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.5.6 | 预警记录列表 | 🔴 P0 | ❌ | `GET /alerts` |
| 1.5.7 | 预警详情 | 🔴 P0 | ❌ | `GET /alerts/{id}` |
| 1.5.8 | 确认预警 | 🔴 P0 | ❌ | `PUT /alerts/{id}/acknowledge` |
| 1.5.9 | 处理预警 | 🔴 P0 | ❌ | `PUT /alerts/{id}/resolve` |
| 1.5.10 | 忽略预警 | 🟡 P1 | ❌ | `PUT /alerts/{id}/ignore` |
| 1.5.11 | 预警通知列表 | 🟡 P1 | ❌ | `GET /alert-notifications` |
| 1.5.12 | 标记通知已读 | 🟡 P1 | ❌ | `PUT /alert-notifications/{id}/read` |

#### 4.5.3 异常事件

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.5.13 | 异常事件列表 | 🟡 P1 | ❌ | `GET /exceptions` |
| 1.5.14 | 创建异常事件 | 🟡 P1 | ❌ | `POST /exceptions` |
| 1.5.15 | 异常事件详情 | 🟡 P1 | ❌ | `GET /exceptions/{id}` |
| 1.5.16 | 更新异常状态 | 🟡 P1 | ❌ | `PUT /exceptions/{id}/status` |
| 1.5.17 | 添加处理记录 | 🟡 P1 | ❌ | `POST /exceptions/{id}/actions` |
| 1.5.18 | 异常升级 | 🟡 P1 | ❌ | `POST /exceptions/{id}/escalate` |

#### 4.5.4 项目健康度快照

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.5.19 | 生成健康度快照 | 🟡 P1 | ❌ | 后台定时任务 |
| 1.5.20 | 健康度趋势查询 | 🟡 P1 | ❌ | `GET /projects/{id}/health-history` |
| 1.5.21 | 预警统计分析 | 🟢 P2 | ❌ | `GET /alerts/statistics` |

---

## 五、第二期：协同与变更任务（6个月）

### 5.1 设计变更管理 (ECN) API（M1-M2）

#### 5.1.1 ECN 基础管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.1.1 | ECN 列表 API | 🔴 P0 | ❌ | `GET /ecns` |
| 2.1.2 | ECN 详情 API | 🔴 P0 | ❌ | `GET /ecns/{id}` |
| 2.1.3 | 创建 ECN 申请 | 🔴 P0 | ❌ | `POST /ecns` |
| 2.1.4 | 更新 ECN | 🔴 P0 | ❌ | `PUT /ecns/{id}` |
| 2.1.5 | 提交 ECN | 🔴 P0 | ❌ | `PUT /ecns/{id}/submit` |
| 2.1.6 | 取消 ECN | 🟡 P1 | ❌ | `PUT /ecns/{id}/cancel` |

#### 5.1.2 ECN 评估

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.1.7 | 评估列表 | 🔴 P0 | ❌ | `GET /ecns/{id}/evaluations` |
| 2.1.8 | 创建评估 | 🔴 P0 | ❌ | `POST /ecns/{id}/evaluations` |
| 2.1.9 | 提交评估结果 | 🔴 P0 | ❌ | `PUT /ecn-evaluations/{id}/submit` |
| 2.1.10 | 评估汇总 | 🟡 P1 | ❌ | `GET /ecns/{id}/evaluation-summary` |

#### 5.1.3 ECN 审批

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.1.11 | 审批记录列表 | 🔴 P0 | ❌ | `GET /ecns/{id}/approvals` |
| 2.1.12 | 审批通过 | 🔴 P0 | ❌ | `PUT /ecn-approvals/{id}/approve` |
| 2.1.13 | 审批驳回 | 🔴 P0 | ❌ | `PUT /ecn-approvals/{id}/reject` |
| 2.1.14 | 审批规则配置 | 🟡 P1 | ❌ | `GET /ecn-approval-matrix` |

#### 5.1.4 ECN 执行

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.1.15 | ECN 任务列表 | 🔴 P0 | ❌ | `GET /ecns/{id}/tasks` |
| 2.1.16 | 分派 ECN 任务 | 🔴 P0 | ❌ | `POST /ecns/{id}/tasks` |
| 2.1.17 | 更新任务进度 | 🔴 P0 | ❌ | `PUT /ecn-tasks/{id}/progress` |
| 2.1.18 | 完成 ECN 任务 | 🔴 P0 | ❌ | `PUT /ecn-tasks/{id}/complete` |
| 2.1.19 | 受影响物料列表 | 🟡 P1 | ❌ | `GET /ecns/{id}/affected-materials` |
| 2.1.20 | 受影响订单列表 | 🟡 P1 | ❌ | `GET /ecns/{id}/affected-orders` |

#### 5.1.5 ECN 追溯

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.1.21 | ECN 日志列表 | 🟡 P1 | ❌ | `GET /ecns/{id}/logs` |
| 2.1.22 | ECN 统计分析 | 🟢 P2 | ❌ | `GET /ecns/statistics` |
| 2.1.23 | 项目 ECN 列表 | 🟡 P1 | ❌ | `GET /projects/{id}/ecns` |

### 5.2 外协管理 API（M3）

#### 5.2.1 外协供应商

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.2.1 | 外协商列表 | 🔴 P0 | ❌ | `GET /outsourcing-vendors` |
| 2.2.2 | 外协商详情 | 🔴 P0 | ❌ | `GET /outsourcing-vendors/{id}` |
| 2.2.3 | 创建外协商 | 🔴 P0 | ❌ | `POST /outsourcing-vendors` |
| 2.2.4 | 更新外协商 | 🔴 P0 | ❌ | `PUT /outsourcing-vendors/{id}` |
| 2.2.5 | 外协商评价 | 🟡 P1 | ❌ | `POST /outsourcing-vendors/{id}/evaluations` |

#### 5.2.2 外协订单

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.2.6 | 外协订单列表 | 🔴 P0 | ❌ | `GET /outsourcing-orders` |
| 2.2.7 | 外协订单详情 | 🔴 P0 | ❌ | `GET /outsourcing-orders/{id}` |
| 2.2.8 | 创建外协订单 | 🔴 P0 | ❌ | `POST /outsourcing-orders` |
| 2.2.9 | 更新外协订单 | 🔴 P0 | ❌ | `PUT /outsourcing-orders/{id}` |
| 2.2.10 | 外协订单审批 | 🔴 P0 | ❌ | `PUT /outsourcing-orders/{id}/approve` |
| 2.2.11 | 外协订单明细 | 🔴 P0 | ❌ | `GET /outsourcing-orders/{id}/items` |
| 2.2.12 | 外协订单打印 | 🟡 P1 | ❌ | `GET /outsourcing-orders/{id}/print` |

#### 5.2.3 外协交付与质检

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.2.13 | 交付记录列表 | 🔴 P0 | ❌ | `GET /outsourcing-deliveries` |
| 2.2.14 | 创建交付记录 | 🔴 P0 | ❌ | `POST /outsourcing-deliveries` |
| 2.2.15 | 质检记录列表 | 🔴 P0 | ❌ | `GET /outsourcing-inspections` |
| 2.2.16 | 创建质检记录 | 🔴 P0 | ❌ | `POST /outsourcing-inspections` |
| 2.2.17 | 质检结果更新 | 🔴 P0 | ❌ | `PUT /outsourcing-inspections/{id}` |

#### 5.2.4 外协进度与付款

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.2.18 | 外协进度更新 | 🟡 P1 | ❌ | `PUT /outsourcing-orders/{id}/progress` |
| 2.2.19 | 外协进度列表 | 🟡 P1 | ❌ | `GET /outsourcing-orders/{id}/progress-logs` |
| 2.2.20 | 外协付款记录 | 🟡 P1 | ❌ | `GET /outsourcing-payments` |
| 2.2.21 | 创建付款记录 | 🟡 P1 | ❌ | `POST /outsourcing-payments` |
| 2.2.22 | 外协对账单 | 🟢 P2 | ❌ | `GET /outsourcing-vendors/{id}/statement` |

### 5.3 验收管理 API（M4）

#### 5.3.1 验收模板

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.3.1 | 验收模板列表 | 🔴 P0 | ❌ | `GET /acceptance-templates` |
| 2.3.2 | 验收模板详情 | 🔴 P0 | ❌ | `GET /acceptance-templates/{id}` |
| 2.3.3 | 创建验收模板 | 🔴 P0 | ❌ | `POST /acceptance-templates` |
| 2.3.4 | 模板检查项列表 | 🔴 P0 | ❌ | `GET /acceptance-templates/{id}/items` |
| 2.3.5 | 添加模板检查项 | 🔴 P0 | ❌ | `POST /acceptance-templates/{id}/items` |

#### 5.3.2 验收单管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.3.6 | 验收单列表 | 🔴 P0 | ❌ | `GET /acceptance-orders` |
| 2.3.7 | 验收单详情 | 🔴 P0 | ❌ | `GET /acceptance-orders/{id}` |
| 2.3.8 | 创建验收单(FAT) | 🔴 P0 | ❌ | `POST /acceptance-orders` |
| 2.3.9 | 开始验收 | 🔴 P0 | ❌ | `PUT /acceptance-orders/{id}/start` |
| 2.3.10 | 验收检查项列表 | 🔴 P0 | ❌ | `GET /acceptance-orders/{id}/items` |
| 2.3.11 | 更新检查项结果 | 🔴 P0 | ❌ | `PUT /acceptance-items/{id}` |
| 2.3.12 | 完成验收 | 🔴 P0 | ❌ | `PUT /acceptance-orders/{id}/complete` |

#### 5.3.3 验收问题管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.3.13 | 验收问题列表 | 🔴 P0 | ❌ | `GET /acceptance-orders/{id}/issues` |
| 2.3.14 | 创建验收问题 | 🔴 P0 | ❌ | `POST /acceptance-orders/{id}/issues` |
| 2.3.15 | 更新问题状态 | 🔴 P0 | ❌ | `PUT /acceptance-issues/{id}` |
| 2.3.16 | 添加跟进记录 | 🟡 P1 | ❌ | `POST /acceptance-issues/{id}/follow-ups` |
| 2.3.17 | 关闭问题 | 🔴 P0 | ❌ | `PUT /acceptance-issues/{id}/close` |

#### 5.3.4 验收签字与报告

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.3.18 | 验收签字列表 | 🟡 P1 | ❌ | `GET /acceptance-orders/{id}/signatures` |
| 2.3.19 | 添加签字 | 🟡 P1 | ❌ | `POST /acceptance-orders/{id}/signatures` |
| 2.3.20 | 生成验收报告 | 🟡 P1 | ❌ | `POST /acceptance-orders/{id}/report` |
| 2.3.21 | 下载验收报告 | 🟡 P1 | ❌ | `GET /acceptance-reports/{id}/download` |

### 5.4 资源排程 API（M5）

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.4.1 | 工程师负荷统计 | 🟡 P1 | ❌ | `GET /users/{id}/workload` |
| 2.4.2 | 部门负荷统计 | 🟡 P1 | ❌ | `GET /departments/{id}/workload` |
| 2.4.3 | 资源负荷看板 | 🟡 P1 | ❌ | `GET /workload/dashboard` |
| 2.4.4 | 甘特图数据 | 🟢 P2 | ❌ | `GET /projects/{id}/gantt` |

### 5.5 收款管理 API（M6）

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 2.5.1 | 合同收款节点 | 🟡 P1 | ❌ | `GET /projects/{id}/payment-milestones` |
| 2.5.2 | 创建收款节点 | 🟡 P1 | ❌ | `POST /projects/{id}/payment-milestones` |
| 2.5.3 | 收款记录 | 🟡 P1 | ❌ | `GET /payments` |
| 2.5.4 | 登记收款 | 🟡 P1 | ❌ | `POST /payments` |
| 2.5.5 | 应收账款统计 | 🟢 P2 | ❌ | `GET /receivables/summary` |
| 2.5.6 | 收款提醒服务 | 🟢 P2 | ❌ | 后台服务 |

---

## 六、第三期：售后与沉淀任务（6个月）

### 6.1 售后工单 API（M1-M2）

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 3.1.1 | 售后工单列表 | 🟡 P1 | ❌ | `GET /service-orders` |
| 3.1.2 | 创建售后工单 | 🟡 P1 | ❌ | `POST /service-orders` |
| 3.1.3 | 工单详情 | 🟡 P1 | ❌ | `GET /service-orders/{id}` |
| 3.1.4 | 分派工单 | 🟡 P1 | ❌ | `PUT /service-orders/{id}/assign` |
| 3.1.5 | 更新工单状态 | 🟡 P1 | ❌ | `PUT /service-orders/{id}/status` |
| 3.1.6 | 关闭工单 | 🟡 P1 | ❌ | `PUT /service-orders/{id}/close` |
| 3.1.7 | 设备档案 | 🟢 P2 | ❌ | `GET /machines/{id}/service-history` |

### 6.2 项目复盘 API（M3）

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 3.2.1 | 复盘报告列表 | 🟢 P2 | ❌ | `GET /project-reviews` |
| 3.2.2 | 创建复盘报告 | 🟢 P2 | ❌ | `POST /project-reviews` |
| 3.2.3 | 成本对比分析 | 🟢 P2 | ❌ | `GET /projects/{id}/cost-analysis` |
| 3.2.4 | 问题总结 | 🟢 P2 | ❌ | `GET /projects/{id}/lessons-learned` |

### 6.3 知识库 API（M4）

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 3.3.1 | 问题库列表 | 🟢 P2 | ❌ | `GET /knowledge/issues` |
| 3.3.2 | 方案库列表 | 🟢 P2 | ❌ | `GET /knowledge/solutions` |
| 3.3.3 | 搜索知识库 | 🟢 P2 | ❌ | `GET /knowledge/search` |
| 3.3.4 | 添加知识条目 | 🟢 P2 | ❌ | `POST /knowledge` |

### 6.4 成本核算 API（M5）

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 3.4.1 | 项目成本汇总 | 🟡 P1 | ❌ | `GET /projects/{id}/cost-summary` |
| 3.4.2 | 成本明细列表 | 🟡 P1 | ❌ | `GET /projects/{id}/cost-details` |
| 3.4.3 | 项目利润分析 | 🟢 P2 | ❌ | `GET /projects/{id}/profit-analysis` |
| 3.4.4 | 成本趋势分析 | 🟢 P2 | ❌ | `GET /cost-trends` |

### 6.5 BI 报表 API（M6）

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 3.5.1 | 交付准时率 | 🟢 P2 | ❌ | `GET /reports/delivery-rate` |
| 3.5.2 | 项目健康度分布 | 🟢 P2 | ❌ | `GET /reports/health-distribution` |
| 3.5.3 | 人员利用率 | 🟢 P2 | ❌ | `GET /reports/utilization` |
| 3.5.4 | 供应商绩效 | 🟢 P2 | ❌ | `GET /reports/supplier-performance` |
| 3.5.5 | 决策驾驶舱数据 | 🟢 P2 | ❌ | `GET /dashboard/executive` |

---

## 七、前端开发任务

### 7.1 基础框架（第一期 M1）

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.1.1 | 项目骨架搭建 | 🔴 P0 | ❌ | React + Ant Design Pro |
| F.1.2 | 路由配置 | 🔴 P0 | ❌ | 路由权限控制 |
| F.1.3 | 状态管理 | 🔴 P0 | ❌ | Redux/Zustand |
| F.1.4 | API 封装 | 🔴 P0 | ❌ | Axios + 拦截器 |
| F.1.5 | 登录页面 | 🔴 P0 | ❌ | JWT 认证 |
| F.1.6 | 布局组件 | 🔴 P0 | ❌ | 侧边栏+头部 |

### 7.2 核心页面（第一期 M2-M4）

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.2.1 | 项目列表页 | 🔴 P0 | ❌ | 表格+筛选 |
| F.2.2 | 项目看板页 | 🔴 P0 | ❌ | 红黄绿灯看板 |
| F.2.3 | 项目详情页 | 🔴 P0 | ❌ | Tab 多页签 |
| F.2.4 | 项目创建/编辑表单 | 🔴 P0 | ❌ | 步骤表单 |
| F.2.5 | 机台管理页 | 🔴 P0 | ❌ | 列表+详情 |
| F.2.6 | 里程碑管理 | 🟡 P1 | ❌ | 时间线组件 |
| F.2.7 | 物料列表页 | 🔴 P0 | ❌ | 表格+筛选 |
| F.2.8 | BOM 管理页 | 🔴 P0 | ❌ | 树形表格 |
| F.2.9 | 采购订单页 | 🔴 P0 | ❌ | 列表+表单 |
| F.2.10 | 到货管理页 | 🔴 P0 | ❌ | 列表+表单 |
| F.2.11 | 预警中心页 | 🔴 P0 | ❌ | 列表+统计 |
| F.2.12 | 异常管理页 | 🟡 P1 | ❌ | 列表+详情 |

### 7.3 协同页面（第二期）

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.3.1 | ECN 列表页 | 🔴 P0 | ❌ | 列表+状态筛选 |
| F.3.2 | ECN 详情页 | 🔴 P0 | ❌ | 流程+评估+任务 |
| F.3.3 | ECN 创建/编辑 | 🔴 P0 | ❌ | 多步骤表单 |
| F.3.4 | 外协订单列表 | 🔴 P0 | ❌ | 列表+筛选 |
| F.3.5 | 外协订单详情 | 🔴 P0 | ❌ | 进度+质检 |
| F.3.6 | 验收单列表 | 🔴 P0 | ❌ | FAT/SAT 分类 |
| F.3.7 | 验收执行页 | 🔴 P0 | ❌ | 检查项+问题 |
| F.3.8 | 资源负荷看板 | 🟡 P1 | ❌ | 甘特图+统计 |

### 7.4 决策与分析页面（第三期）

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.4.1 | 决策驾驶舱 | 🟢 P2 | ❌ | 综合看板 |
| F.4.2 | 成本分析页 | 🟢 P2 | ❌ | 图表+对比 |
| F.4.3 | 项目复盘页 | 🟢 P2 | ❌ | 表单+统计 |
| F.4.4 | 知识库页面 | 🟢 P2 | ❌ | 搜索+分类 |

---

## 八、后台服务任务

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| S.1 | 健康度自动计算服务 | 🔴 P0 | ❌ | 定时任务 |
| S.2 | 缺料预警生成服务 | 🔴 P0 | ❌ | 定时任务 |
| S.3 | 里程碑预警服务 | 🔴 P0 | ❌ | 定时任务 |
| S.4 | 外协交期预警服务 | 🟡 P1 | ❌ | 定时任务 |
| S.5 | 收款提醒服务 | 🟡 P1 | ❌ | 定时任务 |
| S.6 | 预警升级服务 | 🟡 P1 | ❌ | 定时任务 |
| S.7 | 健康度快照服务 | 🟡 P1 | ❌ | 每日快照 |
| S.8 | 消息推送服务 | 🟡 P1 | ❌ | 企微/邮件 |

---

## 九、系统集成任务

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| I.1 | 企业微信登录集成 | 🟡 P1 | ❌ | OAuth2 |
| I.2 | 企业微信消息推送 | 🟡 P1 | ❌ | 卡片消息 |
| I.3 | 企业微信审批集成 | 🟢 P2 | ❌ | 审批应用 |
| I.4 | ERP 采购订单同步 | 🟢 P2 | ❌ | 接口对接 |
| I.5 | ERP 物料数据同步 | 🟢 P2 | ❌ | 接口对接 |
| I.6 | PDM 图纸版本同步 | 🟢 P2 | ❌ | 接口对接 |

---

## 十、部署与运维任务

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| D.1 | Docker 镜像构建 | 🔴 P0 | ❌ | Dockerfile |
| D.2 | docker-compose 配置 | 🔴 P0 | ❌ | 本地开发 |
| D.3 | 数据库备份方案 | 🟡 P1 | ❌ | 定时备份 |
| D.4 | 日志收集配置 | 🟡 P1 | ❌ | ELK/Loki |
| D.5 | 监控告警配置 | 🟡 P1 | ❌ | Prometheus |
| D.6 | CI/CD 流水线 | 🟡 P1 | ❌ | GitHub Actions |
| D.7 | 生产环境部署 | 🟢 P2 | ❌ | K8s/Docker |

---

## 十一、测试任务

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| T.1 | 单元测试框架搭建 | 🟡 P1 | ❌ | pytest |
| T.2 | API 集成测试 | 🟡 P1 | ❌ | httpx |
| T.3 | 前端单元测试 | 🟢 P2 | ❌ | Jest |
| T.4 | E2E 测试 | 🟢 P2 | ❌ | Playwright |

---

## 附录：优先级说明

| 优先级 | 标识 | 说明 |
|:------:|:----:|------|
| P0 | 🔴 | 核心功能，必须优先完成 |
| P1 | 🟡 | 重要功能，第二优先级 |
| P2 | 🟢 | 增强功能，可延后 |

---

*文档版本：v1.0*
*更新日期：2026-01-03*
