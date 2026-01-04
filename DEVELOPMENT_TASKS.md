# 开发任务列表 - 非标自动化项目管理系统

> 最后更新：2026-01-04
> 版本：v1.7
> 状态说明：✅ 已完成 | ⚠️ 部分完成 | ❌ 待开发 | 🚧 开发中
> 设计文档对齐：已全面对齐 `claude 设计方案/` 目录下所有详细设计文档，补充缺失模块

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
| 数据库模型 | 核心业务模型 | ✅ 95% | 项目/采购/ECN/验收/外协/预警/生产/PMO等 |
| 数据库模型 | 缺料管理模型 | ⚠️ 10% | 🆕 需补充9张专用表 |
| 数据库模型 | 研发项目模型 | ❌ 0% | 🆕 需新建6张专用表 |
| 数据库模型 | 售后/知识库模型 | ❌ 0% | 🆕 需新建6张专用表 |
| 数据库模型 | 项目复盘模型 | ❌ 0% | 🆕 需新建3张专用表 |
| 数据库迁移 | SQL 迁移脚本 | ⚠️ 85% | 部分新表待生成迁移脚本 |
| Pydantic Schema | API 数据模式 | ⚠️ 80% | 部分新模块待补充 |
| API 端点 | 项目管理 | ⚠️ 20% | 仅完成基础 CRUD |
| API 端点 | 缺料管理 | ❌ 0% | 🆕 需补充30+端点 |
| API 端点 | 进度跟踪 | ❌ 0% | 🆕 新增模块 |
| API 端点 | 生产管理 | ❌ 0% | 🆕 新增模块（核心） |
| API 端点 | 销售管理(O2C) | ❌ 0% | 🆕 新增模块 |
| API 端点 | 研发项目管理 | ❌ 0% | 🆕 新增模块（IPO合规） |
| API 端点 | 售后/知识库 | ❌ 0% | 🆕 需补充15+端点 |
| API 端点 | 通知中心 | ❌ 0% | 🆕 需新建5端点 |
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

#### 4.4.5 齐套率与物料保障

> 参考设计文档：`采购与物料管理模块_详细设计文档.md` 第七、八章

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.4.27 | 项目齐套率计算 | 🔴 P0 | ❌ | `GET /projects/{id}/kit-rate` | 按数量/金额加权 |
| 1.4.28 | 机台齐套率计算 | 🔴 P0 | ❌ | `GET /machines/{id}/kit-rate` | |
| 1.4.29 | 机台物料状态 | 🔴 P0 | ❌ | `GET /machines/{id}/material-status` | 详细到货状态 |
| 1.4.30 | 项目物料汇总 | 🔴 P0 | ❌ | `GET /projects/{id}/material-status` | 项目级汇总 |
| 1.4.31 | 缺料清单 | 🔴 P0 | ❌ | `GET /projects/{id}/shortage` | 缺料明细 |
| 1.4.32 | 关键物料缺口 | 🔴 P0 | ❌ | `GET /projects/{id}/critical-shortage` | 关键件缺口 |
| 1.4.33 | 齐套看板数据 | 🔴 P0 | ❌ | `GET /kit-rate/dashboard` | 全局看板 |
| 1.4.34 | 齐套趋势分析 | 🟡 P1 | ❌ | `GET /kit-rate/trend` | 趋势图表 |

#### 4.4.6 缺料预警管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.4.35 | 缺料预警列表 | 🔴 P0 | ❌ | `GET /shortage-alerts` | 分页+筛选 |
| 1.4.36 | 缺料预警详情 | 🔴 P0 | ❌ | `GET /shortage-alerts/{id}` | |
| 1.4.37 | 确认预警 | 🔴 P0 | ❌ | `PUT /shortage-alerts/{id}/acknowledge` | PMC确认 |
| 1.4.38 | 处理预警 | 🔴 P0 | ❌ | `PATCH /shortage-alerts/{id}` | 更新处理措施 |
| 1.4.39 | 解决预警 | 🔴 P0 | ❌ | `POST /shortage-alerts/{id}/resolve` | 结案 |
| 1.4.40 | 添加跟进记录 | 🟡 P1 | ❌ | `POST /shortage-alerts/{id}/follow-ups` | 跟进记录 |
| 1.4.41 | 预警统计 | 🟡 P1 | ❌ | `GET /shortage-alerts/statistics` | 按级别/类型 |
| 1.4.42 | 更新项目健康度 | 🔴 P0 | ❌ | 后台服务 | 缺料→H3阻塞 |

#### 4.4.7 物料需求计划

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.4.43 | 物料需求汇总 | 🟡 P1 | ❌ | `GET /material-demands` | 多项目汇总 |
| 1.4.44 | 需求与库存对比 | 🟡 P1 | ❌ | `GET /material-demands/vs-stock` | 需求-库存 |
| 1.4.45 | 自动生成采购需求 | 🟡 P1 | ❌ | `POST /material-demands/generate-pr` | 从缺口生成PR |
| 1.4.46 | 需求时间表 | 🟡 P1 | ❌ | `GET /material-demands/schedule` | 按日期需求 |
| 1.4.47 | 物料交期预测 | 🟢 P2 | ❌ | `GET /materials/{id}/lead-time-forecast` | 基于历史 |

### 4.5 进度跟踪 API（M4）🆕

> 参考设计文档：`进度跟踪模块_详细设计文档.md`

#### 4.5.1 WBS 模板管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.5.1 | WBS 模板列表 | 🔴 P0 | ❌ | `GET /wbs-templates` | 单机类/线体类 |
| 1.5.2 | 创建 WBS 模板 | 🔴 P0 | ❌ | `POST /wbs-templates` | |
| 1.5.3 | WBS 模板详情 | 🔴 P0 | ❌ | `GET /wbs-templates/{id}` | |
| 1.5.4 | 更新 WBS 模板 | 🟡 P1 | ❌ | `PUT /wbs-templates/{id}` | |
| 1.5.5 | 模板任务列表 | 🔴 P0 | ❌ | `GET /wbs-templates/{id}/tasks` | |
| 1.5.6 | 添加模板任务 | 🔴 P0 | ❌ | `POST /wbs-templates/{id}/tasks` | |
| 1.5.7 | 更新模板任务 | 🟡 P1 | ❌ | `PUT /wbs-template-tasks/{id}` | |

#### 4.5.2 项目任务管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.5.8 | 从模板初始化 WBS | 🔴 P0 | ❌ | `POST /projects/{id}/init-wbs` | 一键生成计划 |
| 1.5.9 | 项目任务列表 | 🔴 P0 | ❌ | `GET /projects/{id}/tasks` | |
| 1.5.10 | 创建项目任务 | 🔴 P0 | ❌ | `POST /projects/{id}/tasks` | |
| 1.5.11 | 更新项目任务 | 🔴 P0 | ❌ | `PUT /tasks/{id}` | |
| 1.5.12 | 任务详情 | 🔴 P0 | ❌ | `GET /tasks/{id}` | |
| 1.5.13 | 更新任务进度 | 🔴 P0 | ❌ | `PUT /tasks/{id}/progress` | 百分比进度 |
| 1.5.14 | 完成任务 | 🔴 P0 | ❌ | `PUT /tasks/{id}/complete` | |
| 1.5.15 | 任务依赖关系 | 🟡 P1 | ❌ | `GET /tasks/{id}/dependencies` | 前置任务 |
| 1.5.16 | 设置任务依赖 | 🟡 P1 | ❌ | `PUT /tasks/{id}/dependencies` | |
| 1.5.17 | 任务负责人分配 | 🔴 P0 | ❌ | `PUT /tasks/{id}/assignee` | |

#### 4.5.3 进度填报

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.5.18 | 提交进度日报 | 🔴 P0 | ❌ | `POST /progress-reports` | 日报/周报 |
| 1.5.19 | 进度报告列表 | 🔴 P0 | ❌ | `GET /progress-reports` | |
| 1.5.20 | 进度报告详情 | 🟡 P1 | ❌ | `GET /progress-reports/{id}` | |
| 1.5.21 | 项目进度汇总 | 🔴 P0 | ❌ | `GET /projects/{id}/progress-summary` | 整体完成率 |
| 1.5.22 | 机台进度汇总 | 🔴 P0 | ❌ | `GET /machines/{id}/progress-summary` | |

#### 4.5.4 进度看板与报表

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.5.23 | 甘特图数据 | 🔴 P0 | ❌ | `GET /projects/{id}/gantt` | 任务甘特图 |
| 1.5.24 | 进度看板 | 🔴 P0 | ❌ | `GET /projects/{id}/progress-board` | |
| 1.5.25 | 里程碑达成率 | 🟡 P1 | ❌ | `GET /reports/milestone-rate` | |
| 1.5.26 | 延期原因统计 | 🟡 P1 | ❌ | `GET /reports/delay-reasons` | Top N |
| 1.5.27 | 延期/阻塞预警 | 🔴 P0 | ❌ | 后台服务 | 自动触发预警 |

### 4.6 预警与异常 API（M4）

#### 4.6.1 预警规则

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.6.1 | 预警规则列表 | 🔴 P0 | ❌ | `GET /alert-rules` |
| 1.6.2 | 创建预警规则 | 🔴 P0 | ❌ | `POST /alert-rules` |
| 1.6.3 | 更新预警规则 | 🔴 P0 | ❌ | `PUT /alert-rules/{id}` |
| 1.6.4 | 启用/禁用规则 | 🔴 P0 | ❌ | `PUT /alert-rules/{id}/toggle` |
| 1.6.5 | 预警规则模板 | 🟡 P1 | ❌ | `GET /alert-rule-templates` |

#### 4.6.2 预警记录

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.6.6 | 预警记录列表 | 🔴 P0 | ❌ | `GET /alerts` |
| 1.6.7 | 预警详情 | 🔴 P0 | ❌ | `GET /alerts/{id}` |
| 1.6.8 | 确认预警 | 🔴 P0 | ❌ | `PUT /alerts/{id}/acknowledge` |
| 1.6.9 | 处理预警 | 🔴 P0 | ❌ | `PUT /alerts/{id}/resolve` |
| 1.6.10 | 忽略预警 | 🟡 P1 | ❌ | `PUT /alerts/{id}/ignore` |
| 1.6.11 | 预警通知列表 | 🟡 P1 | ❌ | `GET /alert-notifications` |
| 1.6.12 | 标记通知已读 | 🟡 P1 | ❌ | `PUT /alert-notifications/{id}/read` |

#### 4.6.3 异常事件

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.6.13 | 异常事件列表 | 🟡 P1 | ❌ | `GET /exceptions` |
| 1.6.14 | 创建异常事件 | 🟡 P1 | ❌ | `POST /exceptions` |
| 1.6.15 | 异常事件详情 | 🟡 P1 | ❌ | `GET /exceptions/{id}` |
| 1.6.16 | 更新异常状态 | 🟡 P1 | ❌ | `PUT /exceptions/{id}/status` |
| 1.6.17 | 添加处理记录 | 🟡 P1 | ❌ | `POST /exceptions/{id}/actions` |
| 1.6.18 | 异常升级 | 🟡 P1 | ❌ | `POST /exceptions/{id}/escalate` |

#### 4.6.4 项目健康度快照

| 序号 | 任务 | 优先级 | 状态 | API 路径 |
|:----:|------|:------:|:----:|----------|
| 1.6.19 | 生成健康度快照 | 🟡 P1 | ❌ | 后台定时任务 |
| 1.6.20 | 健康度趋势查询 | 🟡 P1 | ❌ | `GET /projects/{id}/health-history` |
| 1.6.21 | 预警统计分析 | 🟢 P2 | ❌ | `GET /alerts/statistics` |

### 4.7 生产管理 API（M3-M4）🆕

> 参考设计文档：`project-progress-module/docs/PRODUCTION_MODULE_DESIGN.md`
> 核心流程：生产计划 → 任务派工 → 报工执行 → 完工入库

#### 4.7.1 车间与工位管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.1 | 车间列表 | 🔴 P0 | ❌ | `GET /workshops` | 机加/装配/调试 |
| 1.7.2 | 创建车间 | 🔴 P0 | ❌ | `POST /workshops` | |
| 1.7.3 | 更新车间 | 🟡 P1 | ❌ | `PUT /workshops/{id}` | |
| 1.7.4 | 车间详情 | 🔴 P0 | ❌ | `GET /workshops/{id}` | 含产能/人员 |
| 1.7.5 | 工位列表 | 🔴 P0 | ❌ | `GET /workshops/{id}/workstations` | |
| 1.7.6 | 创建工位 | 🔴 P0 | ❌ | `POST /workshops/{id}/workstations` | |
| 1.7.7 | 更新工位 | 🟡 P1 | ❌ | `PUT /workstations/{id}` | |
| 1.7.8 | 工位状态 | 🔴 P0 | ❌ | `GET /workstations/{id}/status` | 空闲/工作中 |
| 1.7.9 | 车间产能统计 | 🟡 P1 | ❌ | `GET /workshops/{id}/capacity` | |

#### 4.7.2 生产计划管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.10 | 生产计划列表 | 🔴 P0 | ❌ | `GET /production-plans` | 主计划/车间计划 |
| 1.7.11 | 创建生产计划 | 🔴 P0 | ❌ | `POST /production-plans` | |
| 1.7.12 | 更新生产计划 | 🔴 P0 | ❌ | `PUT /production-plans/{id}` | |
| 1.7.13 | 生产计划详情 | 🔴 P0 | ❌ | `GET /production-plans/{id}` | |
| 1.7.14 | 提交计划审批 | 🔴 P0 | ❌ | `PUT /production-plans/{id}/submit` | |
| 1.7.15 | 审批通过 | 🔴 P0 | ❌ | `PUT /production-plans/{id}/approve` | |
| 1.7.16 | 计划发布 | 🔴 P0 | ❌ | `PUT /production-plans/{id}/publish` | |
| 1.7.17 | 产能负荷分析 | 🟡 P1 | ❌ | `GET /production-plans/capacity-load` | |
| 1.7.18 | 排产日历 | 🟡 P1 | ❌ | `GET /production-plans/calendar` | |

#### 4.7.3 生产工单管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.19 | 工单列表 | 🔴 P0 | ❌ | `GET /work-orders` | 分页+筛选 |
| 1.7.20 | 创建工单 | 🔴 P0 | ❌ | `POST /work-orders` | |
| 1.7.21 | 工单详情 | 🔴 P0 | ❌ | `GET /work-orders/{id}` | |
| 1.7.22 | 更新工单 | 🔴 P0 | ❌ | `PUT /work-orders/{id}` | |
| 1.7.23 | 任务派工 | 🔴 P0 | ❌ | `PUT /work-orders/{id}/assign` | 指派人员/工位 |
| 1.7.24 | 批量派工 | 🟡 P1 | ❌ | `POST /work-orders/batch-assign` | |
| 1.7.25 | 开始工单 | 🔴 P0 | ❌ | `PUT /work-orders/{id}/start` | |
| 1.7.26 | 暂停工单 | 🟡 P1 | ❌ | `PUT /work-orders/{id}/pause` | |
| 1.7.27 | 恢复工单 | 🟡 P1 | ❌ | `PUT /work-orders/{id}/resume` | |
| 1.7.28 | 完成工单 | 🔴 P0 | ❌ | `PUT /work-orders/{id}/complete` | |
| 1.7.29 | 取消工单 | 🟡 P1 | ❌ | `PUT /work-orders/{id}/cancel` | |
| 1.7.30 | 工单进度 | 🔴 P0 | ❌ | `GET /work-orders/{id}/progress` | |

#### 4.7.4 报工系统

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.31 | 报工记录列表 | 🔴 P0 | ❌ | `GET /work-reports` | |
| 1.7.32 | 开工报告 | 🔴 P0 | ❌ | `POST /work-reports/start` | 扫码开工 |
| 1.7.33 | 进度上报 | 🔴 P0 | ❌ | `POST /work-reports/progress` | |
| 1.7.34 | 完工报告 | 🔴 P0 | ❌ | `POST /work-reports/complete` | 数量/合格数 |
| 1.7.35 | 暂停报告 | 🟡 P1 | ❌ | `POST /work-reports/pause` | |
| 1.7.36 | 报工详情 | 🔴 P0 | ❌ | `GET /work-reports/{id}` | |
| 1.7.37 | 报工审批 | 🔴 P0 | ❌ | `PUT /work-reports/{id}/approve` | 车间主管 |
| 1.7.38 | 批量审批 | 🟡 P1 | ❌ | `POST /work-reports/batch-approve` | |
| 1.7.39 | 我的报工记录 | 🔴 P0 | ❌ | `GET /work-reports/my` | 工人查看 |
| 1.7.40 | 工时统计 | 🟡 P1 | ❌ | `GET /work-reports/hours-summary` | 按人/工单 |

#### 4.7.5 生产领料

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.41 | 领料单列表 | 🔴 P0 | ❌ | `GET /material-requisitions` | |
| 1.7.42 | 创建领料单 | 🔴 P0 | ❌ | `POST /material-requisitions` | |
| 1.7.43 | 领料单详情 | 🔴 P0 | ❌ | `GET /material-requisitions/{id}` | |
| 1.7.44 | 领料单审批 | 🔴 P0 | ❌ | `PUT /material-requisitions/{id}/approve` | |
| 1.7.45 | 确认发料 | 🔴 P0 | ❌ | `PUT /material-requisitions/{id}/issue` | 仓库发料 |
| 1.7.46 | 退料申请 | 🟡 P1 | ❌ | `POST /material-returns` | |
| 1.7.47 | 退料审批 | 🟡 P1 | ❌ | `PUT /material-returns/{id}/approve` | |

#### 4.7.6 生产异常

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.48 | 生产异常列表 | 🔴 P0 | ❌ | `GET /production-exceptions` | |
| 1.7.49 | 上报异常 | 🔴 P0 | ❌ | `POST /production-exceptions` | 物料/设备/质量 |
| 1.7.50 | 异常详情 | 🔴 P0 | ❌ | `GET /production-exceptions/{id}` | |
| 1.7.51 | 处理异常 | 🔴 P0 | ❌ | `PUT /production-exceptions/{id}/handle` | |
| 1.7.52 | 关闭异常 | 🔴 P0 | ❌ | `PUT /production-exceptions/{id}/close` | |
| 1.7.53 | 异常统计 | 🟡 P1 | ❌ | `GET /production-exceptions/statistics` | 按类型/车间 |

#### 4.7.7 生产人员管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.54 | 生产人员列表 | 🔴 P0 | ❌ | `GET /workers` | |
| 1.7.55 | 创建生产人员 | 🔴 P0 | ❌ | `POST /workers` | 关联用户 |
| 1.7.56 | 更新人员信息 | 🟡 P1 | ❌ | `PUT /workers/{id}` | 技能/资质 |
| 1.7.57 | 人员技能矩阵 | 🟡 P1 | ❌ | `GET /workers/skill-matrix` | |
| 1.7.58 | 人员工时统计 | 🟡 P1 | ❌ | `GET /workers/{id}/hours` | |

#### 4.7.8 设备管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.59 | 设备列表 | 🟡 P1 | ❌ | `GET /equipment` | |
| 1.7.60 | 创建设备 | 🟡 P1 | ❌ | `POST /equipment` | |
| 1.7.61 | 设备详情 | 🟡 P1 | ❌ | `GET /equipment/{id}` | |
| 1.7.62 | 更新设备状态 | 🟡 P1 | ❌ | `PUT /equipment/{id}/status` | 运行/维护/故障 |
| 1.7.63 | 设备保养记录 | 🟢 P2 | ❌ | `GET /equipment/{id}/maintenance` | |
| 1.7.64 | 添加保养记录 | 🟢 P2 | ❌ | `POST /equipment/{id}/maintenance` | |

#### 4.7.9 生产报表

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.65 | 生产日报列表 | 🔴 P0 | ❌ | `GET /production-daily-reports` | |
| 1.7.66 | 提交生产日报 | 🔴 P0 | ❌ | `POST /production-daily-reports` | |
| 1.7.67 | 生产驾驶舱 | 🔴 P0 | ❌ | `GET /production/dashboard` | 经理看板 |
| 1.7.68 | 车间任务看板 | 🔴 P0 | ❌ | `GET /workshops/{id}/task-board` | 看板视图 |
| 1.7.69 | 生产效率报表 | 🟡 P1 | ❌ | `GET /reports/production-efficiency` | |
| 1.7.70 | 产能利用率 | 🟡 P1 | ❌ | `GET /reports/capacity-utilization` | |
| 1.7.71 | 人员绩效报表 | 🟡 P1 | ❌ | `GET /reports/worker-performance` | |

#### 4.7.10 工序字典

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 1.7.72 | 工序列表 | 🔴 P0 | ❌ | `GET /processes` | |
| 1.7.73 | 创建工序 | 🔴 P0 | ❌ | `POST /processes` | |
| 1.7.74 | 更新工序 | 🟡 P1 | ❌ | `PUT /processes/{id}` | |
| 1.7.75 | 工序标准工时 | 🟡 P1 | ❌ | `GET /processes/{id}/standard-hours` | |

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

### 5.4 资源排程与负荷管理 API（M5）

> 参考设计文档：`project-progress-module/backend/app/api/v1/workload.py`

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.4.1 | 工程师负荷统计 | 🟡 P1 | ❌ | `GET /workload/user/{id}` | 个人负荷 |
| 2.4.2 | 团队负荷统计 | 🟡 P1 | ❌ | `GET /workload/team` | 部门视角 |
| 2.4.3 | 资源负荷看板 | 🟡 P1 | ❌ | `GET /workload/dashboard` | |
| 2.4.4 | 负荷热力图 | 🟡 P1 | ❌ | `GET /workload/heatmap` | 按周展示 |
| 2.4.5 | 可用资源查询 | 🟡 P1 | ❌ | `GET /workload/available` | 资源调配 |
| 2.4.6 | 资源甘特图 | 🟢 P2 | ❌ | `GET /workload/gantt` | |
| 2.4.7 | 负荷超限预警 | 🟡 P1 | ❌ | 后台服务 | >110%预警 |

### 5.5 PMO 项目管理部 API（M5-M6）🆕

> 参考设计文档：`project-progress-module/docs/PMO_MODULE_DESIGN.md`
> 核心职责：项目立项、监控、变更、风险、结项

#### 5.5.1 立项管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.1 | 立项申请列表 | 🟡 P1 | ❌ | `GET /pmo/initiations` | 分页+筛选 |
| 2.5.2 | 创建立项申请 | 🟡 P1 | ❌ | `POST /pmo/initiations` | 销售提交 |
| 2.5.3 | 立项申请详情 | 🟡 P1 | ❌ | `GET /pmo/initiations/{id}` | |
| 2.5.4 | 更新立项申请 | 🟡 P1 | ❌ | `PUT /pmo/initiations/{id}` | |
| 2.5.5 | 提交立项评审 | 🟡 P1 | ❌ | `PUT /pmo/initiations/{id}/submit` | |
| 2.5.6 | 立项评审通过 | 🟡 P1 | ❌ | `PUT /pmo/initiations/{id}/approve` | 生成项目 |
| 2.5.7 | 立项评审驳回 | 🟡 P1 | ❌ | `PUT /pmo/initiations/{id}/reject` | |

#### 5.5.2 项目阶段门管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.8 | 项目阶段列表 | 🟡 P1 | ❌ | `GET /pmo/projects/{id}/phases` | 立项→设计→生产→交付→结项 |
| 2.5.9 | 阶段入口检查 | 🟡 P1 | ❌ | `POST /pmo/phases/{id}/entry-check` | |
| 2.5.10 | 阶段出口检查 | 🟡 P1 | ❌ | `POST /pmo/phases/{id}/exit-check` | |
| 2.5.11 | 阶段评审 | 🟡 P1 | ❌ | `POST /pmo/phases/{id}/review` | |
| 2.5.12 | 阶段推进 | 🟡 P1 | ❌ | `PUT /pmo/phases/{id}/advance` | |

#### 5.5.3 风险管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.13 | 风险列表 | 🟡 P1 | ❌ | `GET /pmo/projects/{id}/risks` | |
| 2.5.14 | 创建风险 | 🟡 P1 | ❌ | `POST /pmo/projects/{id}/risks` | 风险识别 |
| 2.5.15 | 风险评估 | 🟡 P1 | ❌ | `PUT /pmo/risks/{id}/assess` | 概率×影响 |
| 2.5.16 | 风险应对计划 | 🟡 P1 | ❌ | `PUT /pmo/risks/{id}/response` | |
| 2.5.17 | 风险状态更新 | 🟡 P1 | ❌ | `PUT /pmo/risks/{id}/status` | |
| 2.5.18 | 风险关闭 | 🟡 P1 | ❌ | `PUT /pmo/risks/{id}/close` | |

#### 5.5.4 项目会议管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.19 | 会议列表 | 🟢 P2 | ❌ | `GET /pmo/meetings` | |
| 2.5.20 | 创建会议 | 🟢 P2 | ❌ | `POST /pmo/meetings` | 立项会/周例会 |
| 2.5.21 | 会议详情 | 🟢 P2 | ❌ | `GET /pmo/meetings/{id}` | |
| 2.5.22 | 记录会议纪要 | 🟢 P2 | ❌ | `PUT /pmo/meetings/{id}/minutes` | 纪要+待办 |
| 2.5.23 | 会议待办跟踪 | 🟢 P2 | ❌ | `GET /pmo/meetings/{id}/actions` | |

#### 5.5.5 项目结项管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.24 | 结项申请 | 🟡 P1 | ❌ | `POST /pmo/projects/{id}/closure` | |
| 2.5.25 | 结项详情 | 🟡 P1 | ❌ | `GET /pmo/projects/{id}/closure` | |
| 2.5.26 | 结项评审 | 🟡 P1 | ❌ | `PUT /pmo/closures/{id}/review` | |
| 2.5.27 | 文档归档 | 🟢 P2 | ❌ | `POST /pmo/closures/{id}/archive` | |
| 2.5.28 | 经验教训 | 🟢 P2 | ❌ | `PUT /pmo/closures/{id}/lessons` | 知识沉淀 |

#### 5.5.6 PMO 驾驶舱

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.29 | PMO 驾驶舱数据 | 🟡 P1 | ❌ | `GET /pmo/dashboard` | 项目全景 |
| 2.5.30 | 项目状态周报 | 🟡 P1 | ❌ | `GET /pmo/weekly-report` | |
| 2.5.31 | 资源负荷总览 | 🟡 P1 | ❌ | `GET /pmo/resource-overview` | |
| 2.5.32 | 风险预警墙 | 🟡 P1 | ❌ | `GET /pmo/risk-wall` | |

### 5.6 售前技术支持 API（M6）🆕

> 参考设计文档：`project-progress-module/docs/PRESALE_SUPPORT_DESIGN.md`
> 核心流程：销售申请 → 售前接单 → 方案设计 → 交付评价

#### 5.6.1 支持工单管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.6.1 | 工单列表 | 🟡 P1 | ❌ | `GET /presale/tickets` | 销售/售前视角 |
| 2.6.2 | 创建支持申请 | 🟡 P1 | ❌ | `POST /presale/tickets` | 销售发起 |
| 2.6.3 | 工单详情 | 🟡 P1 | ❌ | `GET /presale/tickets/{id}` | |
| 2.6.4 | 接单确认 | 🟡 P1 | ❌ | `PUT /presale/tickets/{id}/accept` | 售前接单 |
| 2.6.5 | 更新进度 | 🟡 P1 | ❌ | `PUT /presale/tickets/{id}/progress` | |
| 2.6.6 | 提交交付物 | 🟡 P1 | ❌ | `POST /presale/tickets/{id}/deliverables` | |
| 2.6.7 | 完成工单 | 🟡 P1 | ❌ | `PUT /presale/tickets/{id}/complete` | |
| 2.6.8 | 满意度评价 | 🟡 P1 | ❌ | `PUT /presale/tickets/{id}/rating` | 销售评价 |
| 2.6.9 | 工单看板 | 🟡 P1 | ❌ | `GET /presale/tickets/board` | 看板视图 |

#### 5.6.2 技术方案管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.6.10 | 方案列表 | 🟡 P1 | ❌ | `GET /presale/solutions` | |
| 2.6.11 | 创建方案 | 🟡 P1 | ❌ | `POST /presale/solutions` | |
| 2.6.12 | 方案详情 | 🟡 P1 | ❌ | `GET /presale/solutions/{id}` | |
| 2.6.13 | 更新方案 | 🟡 P1 | ❌ | `PUT /presale/solutions/{id}` | |
| 2.6.14 | 成本估算 | 🟡 P1 | ❌ | `GET /presale/solutions/{id}/cost` | 成本拆解 |
| 2.6.15 | 方案审核 | 🟡 P1 | ❌ | `PUT /presale/solutions/{id}/review` | |
| 2.6.16 | 方案版本历史 | 🟢 P2 | ❌ | `GET /presale/solutions/{id}/versions` | |

#### 5.6.3 方案模板库

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.6.17 | 模板列表 | 🟡 P1 | ❌ | `GET /presale/templates` | 按行业/类型 |
| 2.6.18 | 创建模板 | 🟡 P1 | ❌ | `POST /presale/templates` | |
| 2.6.19 | 模板详情 | 🟡 P1 | ❌ | `GET /presale/templates/{id}` | |
| 2.6.20 | 从模板创建方案 | 🟡 P1 | ❌ | `POST /presale/templates/{id}/apply` | 一键套用 |
| 2.6.21 | 模板使用统计 | 🟢 P2 | ❌ | `GET /presale/templates/stats` | 复用率 |

#### 5.6.4 投标管理

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.6.22 | 投标记录列表 | 🟡 P1 | ❌ | `GET /presale/tenders` | |
| 2.6.23 | 创建投标记录 | 🟡 P1 | ❌ | `POST /presale/tenders` | |
| 2.6.24 | 投标详情 | 🟡 P1 | ❌ | `GET /presale/tenders/{id}` | |
| 2.6.25 | 更新投标结果 | 🟡 P1 | ❌ | `PUT /presale/tenders/{id}/result` | 中标/落标 |
| 2.6.26 | 投标分析报表 | 🟢 P2 | ❌ | `GET /presale/tenders/analysis` | 中标率分析 |

#### 5.6.5 售前统计

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.6.27 | 工作量统计 | 🟡 P1 | ❌ | `GET /presale/stats/workload` | |
| 2.6.28 | 响应时效统计 | 🟡 P1 | ❌ | `GET /presale/stats/response-time` | |
| 2.6.29 | 方案转化率 | 🟡 P1 | ❌ | `GET /presale/stats/conversion` | |
| 2.6.30 | 人员绩效 | 🟡 P1 | ❌ | `GET /presale/stats/performance` | |

### 5.7 个人任务中心 API（M6）🆕

> 参考设计文档：`project-progress-module/docs/TASK_CENTER_DESIGN.md`
> 核心功能：多来源任务聚合、智能排序、转办协作

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.7.1 | 我的任务列表 | 🔴 P0 | ❌ | `GET /task-center/my-tasks` | 聚合所有来源 |
| 2.7.2 | 任务概览统计 | 🔴 P0 | ❌ | `GET /task-center/overview` | 待办/逾期/本周 |
| 2.7.3 | 任务详情 | 🔴 P0 | ❌ | `GET /task-center/tasks/{id}` | |
| 2.7.4 | 更新任务进度 | 🔴 P0 | ❌ | `PUT /task-center/tasks/{id}/progress` | |
| 2.7.5 | 完成任务 | 🔴 P0 | ❌ | `PUT /task-center/tasks/{id}/complete` | |
| 2.7.6 | 创建个人任务 | 🟡 P1 | ❌ | `POST /task-center/tasks` | 自建任务 |
| 2.7.7 | 任务转办 | 🟡 P1 | ❌ | `POST /task-center/tasks/{id}/transfer` | |
| 2.7.8 | 接收转办任务 | 🟡 P1 | ❌ | `PUT /task-center/tasks/{id}/accept` | |
| 2.7.9 | 拒绝转办任务 | 🟡 P1 | ❌ | `PUT /task-center/tasks/{id}/reject` | |
| 2.7.10 | 任务评论 | 🟡 P1 | ❌ | `POST /task-center/tasks/{id}/comments` | 协作沟通 |
| 2.7.11 | 岗位职责任务生成 | 🟡 P1 | ❌ | 后台服务 | 自动生成 |
| 2.7.12 | 任务提醒服务 | 🟡 P1 | ❌ | 后台服务 | 到期提醒 |

#### 5.7.2 任务批量操作 🆕

> 参考设计文档：`project-progress-module/backend/app/api/v1/batch_operations.py`

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.7.13 | 批量完成任务 | 🟡 P1 | ❌ | `POST /task-center/batch/complete` | |
| 2.7.14 | 批量转办任务 | 🟡 P1 | ❌ | `POST /task-center/batch/transfer` | |
| 2.7.15 | 批量设置优先级 | 🟡 P1 | ❌ | `POST /task-center/batch/priority` | urgent/high/medium/low |
| 2.7.16 | 批量更新进度 | 🟡 P1 | ❌ | `POST /task-center/batch/progress` | |
| 2.7.17 | 批量催办任务 | 🟡 P1 | ❌ | `POST /task-center/batch/urge` | 发送催办通知 |
| 2.7.18 | 批量删除任务 | 🟡 P1 | ❌ | `POST /task-center/batch/delete` | 仅个人任务 |
| 2.7.19 | 批量开始任务 | 🟡 P1 | ❌ | `POST /task-center/batch/start` | |
| 2.7.20 | 批量暂停任务 | 🟡 P1 | ❌ | `POST /task-center/batch/pause` | |
| 2.7.21 | 批量打标签 | 🟢 P2 | ❌ | `POST /task-center/batch/tag` | |
| 2.7.22 | 批量操作统计 | 🟢 P2 | ❌ | `GET /task-center/batch/statistics` | 操作历史 |

### 5.8 缺料管理 API（M6）🆕（扩展）

> 参考设计文档：`project-progress-module/docs/SHORTAGE_MANAGEMENT_DESIGN.md`
> 核心流程：齐套检查 → 缺料预警 → 处理 → 闭环

#### 5.8.1 缺料上报

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.8.1 | 缺料上报列表 | 🔴 P0 | ❌ | `GET /shortage/reports` | |
| 2.8.2 | 创建缺料上报 | 🔴 P0 | ❌ | `POST /shortage/reports` | 车间扫码上报 |
| 2.8.3 | 上报详情 | 🔴 P0 | ❌ | `GET /shortage/reports/{id}` | |
| 2.8.4 | 确认上报 | 🔴 P0 | ❌ | `PUT /shortage/reports/{id}/confirm` | 仓管确认 |
| 2.8.5 | 处理上报 | 🔴 P0 | ❌ | `PUT /shortage/reports/{id}/handle` | |
| 2.8.6 | 解决上报 | 🔴 P0 | ❌ | `PUT /shortage/reports/{id}/resolve` | |

#### 5.8.2 到货跟踪

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.8.7 | 到货跟踪列表 | 🔴 P0 | ❌ | `GET /shortage/arrivals` | |
| 2.8.8 | 更新到货状态 | 🔴 P0 | ❌ | `PUT /shortage/arrivals/{id}/status` | |
| 2.8.9 | 创建跟催记录 | 🟡 P1 | ❌ | `POST /shortage/arrivals/{id}/follow-up` | |
| 2.8.10 | 确认收货 | 🔴 P0 | ❌ | `POST /shortage/arrivals/{id}/receive` | |
| 2.8.11 | 延迟预警 | 🔴 P0 | ❌ | 后台服务 | 自动标记延迟 |

#### 5.8.3 物料替代

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.8.12 | 替代申请列表 | 🟡 P1 | ❌ | `GET /shortage/substitutions` | |
| 2.8.13 | 创建替代申请 | 🟡 P1 | ❌ | `POST /shortage/substitutions` | |
| 2.8.14 | 技术审批 | 🟡 P1 | ❌ | `PUT /shortage/substitutions/{id}/tech-approve` | |
| 2.8.15 | 生产审批 | 🟡 P1 | ❌ | `PUT /shortage/substitutions/{id}/prod-approve` | |
| 2.8.16 | 执行替代 | 🟡 P1 | ❌ | `PUT /shortage/substitutions/{id}/execute` | |

#### 5.8.4 物料调拨

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.8.17 | 调拨申请列表 | 🟡 P1 | ❌ | `GET /shortage/transfers` | |
| 2.8.18 | 创建调拨申请 | 🟡 P1 | ❌ | `POST /shortage/transfers` | |
| 2.8.19 | 调拨审批 | 🟡 P1 | ❌ | `PUT /shortage/transfers/{id}/approve` | |
| 2.8.20 | 执行调拨 | 🟡 P1 | ❌ | `PUT /shortage/transfers/{id}/execute` | |

#### 5.8.5 缺料统计

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.8.21 | 缺料看板 | 🔴 P0 | ❌ | `GET /shortage/dashboard` | |
| 2.8.22 | 供应商交期分析 | 🟡 P1 | ❌ | `GET /shortage/supplier-delivery` | |
| 2.8.23 | 缺料日报 | 🟡 P1 | ❌ | `GET /shortage/daily-report` | |
| 2.8.24 | 缺料原因分析 | 🟢 P2 | ❌ | `GET /shortage/cause-analysis` | |

### 5.9 绩效管理 API（M6）🆕

> 参考设计文档：`project-progress-module/backend/app/api/v1/performance.py`
> 核心功能：多层级绩效视图、绩效对比、趋势分析、排行榜

#### 5.9.1 个人绩效

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.9.1 | 查看我的绩效 | 🟡 P1 | ❌ | `GET /performance/my` | 周/月/季度 |
| 2.9.2 | 查看指定人员绩效 | 🟡 P1 | ❌ | `GET /performance/user/{id}` | 权限控制 |
| 2.9.3 | 绩效趋势分析 | 🟡 P1 | ❌ | `GET /performance/trends/{user_id}` | 多期对比 |

#### 5.9.2 团队/部门绩效

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.9.4 | 团队绩效汇总 | 🟡 P1 | ❌ | `GET /performance/team/{team_id}` | 平均分/排名 |
| 2.9.5 | 部门绩效汇总 | 🟡 P1 | ❌ | `GET /performance/department/{dept_id}` | 等级分布 |
| 2.9.6 | 绩效排行榜 | 🟡 P1 | ❌ | `GET /performance/ranking` | 团队/部门/公司 |

#### 5.9.3 项目绩效

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.9.7 | 项目成员绩效 | 🟡 P1 | ❌ | `GET /performance/project/{project_id}` | 项目贡献 |
| 2.9.8 | 项目进展报告 | 🟡 P1 | ❌ | `GET /performance/project/{project_id}/progress` | 周报/月报 |
| 2.9.9 | 绩效对比 | 🟢 P2 | ❌ | `GET /performance/compare` | 多人对比 |

### 5.10 报表中心 API（M6）🆕

> 参考设计文档：`project-progress-module/backend/app/api/v1/reports.py`
> 核心功能：多角色视角报表、智能生成、导出分享

#### 5.10.1 报表配置

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.10.1 | 获取支持角色列表 | 🟡 P1 | ❌ | `GET /reports/roles` | 角色配置 |
| 2.10.2 | 获取报表类型列表 | 🟡 P1 | ❌ | `GET /reports/types` | 周报/月报/成本等 |
| 2.10.3 | 角色-报表权限矩阵 | 🟡 P1 | ❌ | `GET /reports/role-report-matrix` | 权限配置 |

#### 5.10.2 报表生成

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.10.4 | 生成报表 | 🟡 P1 | ❌ | `POST /reports/generate` | 按角色/类型 |
| 2.10.5 | 预览报表 | 🟡 P1 | ❌ | `GET /reports/preview/{report_type}` | 简化版预览 |
| 2.10.6 | 比较角色视角 | 🟢 P2 | ❌ | `POST /reports/compare-roles` | 多角色对比 |
| 2.10.7 | 导出报表 | 🟡 P1 | ❌ | `POST /reports/export` | xlsx/pdf/html |

#### 5.10.3 报表模板

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.10.8 | 获取报表模板列表 | 🟢 P2 | ❌ | `GET /reports/templates` | |
| 2.10.9 | 应用报表模板 | 🟢 P2 | ❌ | `POST /reports/templates/apply` | 套用模板 |

### 5.11 数据导入导出 API（M5-M6）🆕

> 参考设计文档：`project-progress-module/backend/app/api/v1/data_import.py`
> 核心功能：Excel模板导入、数据验证、多类型导出

#### 5.11.1 数据导入

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.11.1 | 下载导入模板 | 🟡 P1 | ❌ | `GET /import/templates/{type}` | 按类型下载 |
| 2.11.2 | 获取所有模板类型 | 🟡 P1 | ❌ | `GET /import/templates` | 项目/任务/人员/工时等 |
| 2.11.3 | 预览导入数据 | 🟡 P1 | ❌ | `POST /import/preview` | 上传预览 |
| 2.11.4 | 验证导入数据 | 🟡 P1 | ❌ | `POST /import/validate` | 格式校验 |
| 2.11.5 | 上传并导入数据 | 🟡 P1 | ❌ | `POST /import/upload` | 执行导入 |

#### 5.11.2 数据导出

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.11.6 | 导出项目列表 | 🟡 P1 | ❌ | `GET /import/export/project_list` | Excel |
| 2.11.7 | 导出项目详情 | 🟡 P1 | ❌ | `GET /import/export/project_detail` | 含任务/成本 |
| 2.11.8 | 导出任务列表 | 🟡 P1 | ❌ | `GET /import/export/task_list` | |
| 2.11.9 | 导出工时数据 | 🟡 P1 | ❌ | `GET /import/export/timesheet` | 按日期范围 |
| 2.11.10 | 导出负荷数据 | 🟡 P1 | ❌ | `GET /import/export/workload` | |

### 5.12 工时管理详细 API（M5-M6）🆕

> 参考设计文档：`project-progress-module/backend/app/api/v1/timesheet.py`
> 核心功能：周工时表、批量填报、审批流程

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.12.1 | 工时记录列表 | 🟡 P1 | ❌ | `GET /timesheets` | 分页+筛选 |
| 2.12.2 | 创建单条工时 | 🟡 P1 | ❌ | `POST /timesheets` | |
| 2.12.3 | 批量创建工时 | 🟡 P1 | ❌ | `POST /timesheets/batch` | |
| 2.12.4 | 更新工时记录 | 🟡 P1 | ❌ | `PUT /timesheets/{id}` | |
| 2.12.5 | 删除工时记录 | 🟡 P1 | ❌ | `DELETE /timesheets/{id}` | 仅草稿 |
| 2.12.6 | 提交工时 | 🟡 P1 | ❌ | `POST /timesheets/submit` | 草稿→待审核 |
| 2.12.7 | 审核工时 | 🟡 P1 | ❌ | `POST /timesheets/approve` | PM/部门审批 |
| 2.12.8 | 获取周工时表 | 🔴 P0 | ❌ | `GET /timesheets/week` | 按周展示 |
| 2.12.9 | 获取月度汇总 | 🟡 P1 | ❌ | `GET /timesheets/month-summary` | 月度统计 |
| 2.12.10 | 待审核列表 | 🟡 P1 | ❌ | `GET /timesheets/pending-approval` | 审核人视角 |
| 2.12.11 | 工时统计分析 | 🟡 P1 | ❌ | `GET /timesheets/statistics` | 多维统计 |

### 5.5 销售管理 API（O2C 线索到回款）🆕（M5-M6）

> 参考设计文档：`销售管理模块_线索到回款_设计文档.md`

#### 5.5.1 线索管理 (Lead)

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.1 | 线索列表 | 🔴 P0 | ❌ | `GET /leads` | 分页+筛选 |
| 2.5.2 | 创建线索 | 🔴 P0 | ❌ | `POST /leads` | |
| 2.5.3 | 线索详情 | 🔴 P0 | ❌ | `GET /leads/{id}` | |
| 2.5.4 | 更新线索 | 🔴 P0 | ❌ | `PUT /leads/{id}` | |
| 2.5.5 | 线索跟进记录 | 🟡 P1 | ❌ | `GET /leads/{id}/follow-ups` | |
| 2.5.6 | 添加跟进记录 | 🟡 P1 | ❌ | `POST /leads/{id}/follow-ups` | |
| 2.5.7 | 转为商机 | 🔴 P0 | ❌ | `PUT /leads/{id}/convert` | G1 阶段门 |
| 2.5.8 | 标记无效 | 🟡 P1 | ❌ | `PUT /leads/{id}/invalid` | |

#### 5.5.2 商机管理 (Opportunity)

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.9 | 商机列表 | 🔴 P0 | ❌ | `GET /opportunities` | 分页+筛选 |
| 2.5.10 | 创建商机 | 🔴 P0 | ❌ | `POST /opportunities` | |
| 2.5.11 | 商机详情 | 🔴 P0 | ❌ | `GET /opportunities/{id}` | |
| 2.5.12 | 更新商机 | 🔴 P0 | ❌ | `PUT /opportunities/{id}` | |
| 2.5.13 | 更新商机阶段 | 🔴 P0 | ❌ | `PUT /opportunities/{id}/stage` | 状态机流转 |
| 2.5.14 | 商机评分 | 🟡 P1 | ❌ | `PUT /opportunities/{id}/score` | 准入评估 |
| 2.5.15 | 赢单 | 🔴 P0 | ❌ | `PUT /opportunities/{id}/win` | G3 通过 |
| 2.5.16 | 丢单 | 🔴 P0 | ❌ | `PUT /opportunities/{id}/lose` | 记录原因 |
| 2.5.17 | 商机漏斗统计 | 🟡 P1 | ❌ | `GET /opportunities/funnel` | |

#### 5.5.3 报价管理 (Quote/CPQ)

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.18 | 报价列表 | 🔴 P0 | ❌ | `GET /quotes` | |
| 2.5.19 | 创建报价 | 🔴 P0 | ❌ | `POST /quotes` | |
| 2.5.20 | 报价详情 | 🔴 P0 | ❌ | `GET /quotes/{id}` | |
| 2.5.21 | 更新报价 | 🔴 P0 | ❌ | `PUT /quotes/{id}` | |
| 2.5.22 | 报价明细列表 | 🔴 P0 | ❌ | `GET /quotes/{id}/items` | |
| 2.5.23 | 添加报价明细 | 🔴 P0 | ❌ | `POST /quotes/{id}/items` | |
| 2.5.24 | 报价成本拆解 | 🟡 P1 | ❌ | `GET /quotes/{id}/cost-breakdown` | 毛利校验 |
| 2.5.25 | 提交审批 | 🔴 P0 | ❌ | `PUT /quotes/{id}/submit` | |
| 2.5.26 | 审批通过 | 🔴 P0 | ❌ | `PUT /quotes/{id}/approve` | |
| 2.5.27 | 审批驳回 | 🔴 P0 | ❌ | `PUT /quotes/{id}/reject` | |
| 2.5.28 | 发送客户 | 🟡 P1 | ❌ | `PUT /quotes/{id}/send` | |
| 2.5.29 | 报价版本历史 | 🟡 P1 | ❌ | `GET /quotes/{id}/versions` | |

#### 5.5.4 合同管理 (Contract)

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.30 | 合同列表 | 🔴 P0 | ❌ | `GET /contracts` | |
| 2.5.31 | 创建合同 | 🔴 P0 | ❌ | `POST /contracts` | 从报价转换 |
| 2.5.32 | 合同详情 | 🔴 P0 | ❌ | `GET /contracts/{id}` | |
| 2.5.33 | 更新合同 | 🔴 P0 | ❌ | `PUT /contracts/{id}` | |
| 2.5.34 | 合同审批 | 🔴 P0 | ❌ | `PUT /contracts/{id}/approve` | |
| 2.5.35 | 签订合同 | 🔴 P0 | ❌ | `PUT /contracts/{id}/sign` | G4 阶段门 |
| 2.5.36 | 从合同创建项目 | 🔴 P0 | ❌ | `POST /contracts/{id}/create-project` | 自动生成项目 |
| 2.5.37 | 合同付款节点 | 🔴 P0 | ❌ | `GET /contracts/{id}/payment-terms` | |
| 2.5.38 | 添加付款节点 | 🔴 P0 | ❌ | `POST /contracts/{id}/payment-terms` | 绑定里程碑 |
| 2.5.39 | 合同变更记录 | 🟡 P1 | ❌ | `GET /contracts/{id}/amendments` | |

#### 5.5.5 开票管理 (Invoice)

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.40 | 发票列表 | 🔴 P0 | ❌ | `GET /invoices` | |
| 2.5.41 | 申请开票 | 🔴 P0 | ❌ | `POST /invoices` | |
| 2.5.42 | 发票详情 | 🔴 P0 | ❌ | `GET /invoices/{id}` | |
| 2.5.43 | 开票审批 | 🔴 P0 | ❌ | `PUT /invoices/{id}/approve` | |
| 2.5.44 | 确认开具 | 🔴 P0 | ❌ | `PUT /invoices/{id}/issue` | |
| 2.5.45 | 作废发票 | 🟡 P1 | ❌ | `PUT /invoices/{id}/void` | |

#### 5.5.6 回款管理 (Collection)

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.46 | 回款记录列表 | 🔴 P0 | ❌ | `GET /payments` | |
| 2.5.47 | 登记回款 | 🔴 P0 | ❌ | `POST /payments` | |
| 2.5.48 | 回款详情 | 🔴 P0 | ❌ | `GET /payments/{id}` | |
| 2.5.49 | 核销发票 | 🔴 P0 | ❌ | `PUT /payments/{id}/match-invoice` | |
| 2.5.50 | 应收账龄分析 | 🟡 P1 | ❌ | `GET /receivables/aging` | |
| 2.5.51 | 逾期应收列表 | 🟡 P1 | ❌ | `GET /receivables/overdue` | |
| 2.5.52 | 应收账款统计 | 🟡 P1 | ❌ | `GET /receivables/summary` | |
| 2.5.53 | 收款提醒服务 | 🟡 P1 | ❌ | 后台服务 | 逾期预警 |

#### 5.5.7 销售报表与分析

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 2.5.54 | 销售漏斗报表 | 🟢 P2 | ❌ | `GET /reports/sales-funnel` | |
| 2.5.55 | 赢单/丢单分析 | 🟢 P2 | ❌ | `GET /reports/win-loss` | |
| 2.5.56 | 销售业绩统计 | 🟢 P2 | ❌ | `GET /reports/sales-performance` | |
| 2.5.57 | 客户贡献分析 | 🟢 P2 | ❌ | `GET /reports/customer-contribution` | |

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

### 6.6 研发项目管理 API 🆕

> 参考设计文档：`研发项目管理/` 目录下的设计文档
> 适用场景：IPO 合规、高新技术企业认定、研发费用加计扣除

#### 6.6.1 研发项目立项

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 3.6.1 | 研发项目列表 | 🟡 P1 | ❌ | `GET /rd-projects` | 分页+筛选 |
| 3.6.2 | 创建研发项目 | 🟡 P1 | ❌ | `POST /rd-projects` | 立项申请 |
| 3.6.3 | 研发项目详情 | 🟡 P1 | ❌ | `GET /rd-projects/{id}` | |
| 3.6.4 | 更新研发项目 | 🟡 P1 | ❌ | `PUT /rd-projects/{id}` | |
| 3.6.5 | 研发项目审批 | 🟡 P1 | ❌ | `PUT /rd-projects/{id}/approve` | 立项审批 |
| 3.6.6 | 研发项目结项 | 🟡 P1 | ❌ | `PUT /rd-projects/{id}/close` | 结项验收 |
| 3.6.7 | 研发项目分类 | 🟡 P1 | ❌ | `GET /rd-project-categories` | 自主/委托/合作 |
| 3.6.8 | 关联非标项目 | 🟢 P2 | ❌ | `PUT /rd-projects/{id}/link-project` | 关联交付项目 |

#### 6.6.2 工时记录系统

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 3.6.9 | 工时记录列表 | 🟡 P1 | ❌ | `GET /timesheets` | 按人员/项目 |
| 3.6.10 | 提交工时记录 | 🟡 P1 | ❌ | `POST /timesheets` | 日/周填报 |
| 3.6.11 | 更新工时记录 | 🟡 P1 | ❌ | `PUT /timesheets/{id}` | |
| 3.6.12 | 删除工时记录 | 🟡 P1 | ❌ | `DELETE /timesheets/{id}` | 未审批前 |
| 3.6.13 | 工时审批 | 🟡 P1 | ❌ | `PUT /timesheets/{id}/approve` | 部门审批 |
| 3.6.14 | 批量审批工时 | 🟡 P1 | ❌ | `PUT /timesheets/batch-approve` | |
| 3.6.15 | 我的工时汇总 | 🟡 P1 | ❌ | `GET /timesheets/my-summary` | 个人统计 |
| 3.6.16 | 项目工时汇总 | 🟡 P1 | ❌ | `GET /rd-projects/{id}/timesheet-summary` | 项目统计 |
| 3.6.17 | 部门工时汇总 | 🟡 P1 | ❌ | `GET /departments/{id}/timesheet-summary` | |
| 3.6.18 | 工时分配比例 | 🟢 P2 | ❌ | `GET /users/{id}/time-allocation` | 研发/非研发 |

#### 6.6.3 研发费用归集

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 3.6.19 | 研发费用列表 | 🟡 P1 | ❌ | `GET /rd-costs` | 按项目/类型 |
| 3.6.20 | 录入研发费用 | 🟡 P1 | ❌ | `POST /rd-costs` | |
| 3.6.21 | 更新研发费用 | 🟡 P1 | ❌ | `PUT /rd-costs/{id}` | |
| 3.6.22 | 费用类型列表 | 🟡 P1 | ❌ | `GET /rd-cost-types` | 人工/材料/折旧等 |
| 3.6.23 | 人工费用自动计算 | 🟡 P1 | ❌ | `POST /rd-costs/calc-labor` | 工时×时薪 |
| 3.6.24 | 项目费用汇总 | 🟡 P1 | ❌ | `GET /rd-projects/{id}/cost-summary` | 分类汇总 |
| 3.6.25 | 费用分摊规则 | 🟢 P2 | ❌ | `GET /rd-cost-allocation-rules` | 共享费用分摊 |
| 3.6.26 | 应用分摊规则 | 🟢 P2 | ❌ | `POST /rd-costs/apply-allocation` | |

#### 6.6.4 研发费用加计扣除报表

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| 3.6.27 | 研发费用辅助账 | 🟡 P1 | ❌ | `GET /reports/rd-auxiliary-ledger` | 税务要求 |
| 3.6.28 | 研发费用加计扣除明细 | 🟡 P1 | ❌ | `GET /reports/rd-deduction-detail` | |
| 3.6.29 | 高新企业研发费用表 | 🟢 P2 | ❌ | `GET /reports/rd-high-tech` | 高新认定 |
| 3.6.30 | 研发投入强度报表 | 🟢 P2 | ❌ | `GET /reports/rd-intensity` | 研发/营收 |
| 3.6.31 | 研发人员统计 | 🟡 P1 | ❌ | `GET /reports/rd-personnel` | 研发人员占比 |
| 3.6.32 | 导出研发费用报表 | 🟡 P1 | ❌ | `GET /reports/rd-export` | Excel/PDF |

---

## 补充模块：数据库与 API 补全任务 🆕

> 经全面对比设计文档，以下模块的数据库表和 API 存在缺失，需优先补充。

---

### S1. 缺料管理模块 - 数据库表补全

> 参考设计文档：`project-progress-module/docs/SHORTAGE_MANAGEMENT_DESIGN.md`
> 当前状态：仅有简化版 `shortage_alerts` 表，缺少完整业务表

#### S1.1 ORM 模型开发任务

| 序号 | 任务 | 优先级 | 状态 | 表名 | 说明 |
|:----:|------|:------:|:----:|------|------|
| S1.1.1 | 工单 BOM 明细模型 | 🔴 P0 | ❌ | `mat_work_order_bom` | BOM 用量、需求日期、关键物料标记 |
| S1.1.2 | 物料需求汇总模型 | 🔴 P0 | ❌ | `mat_material_requirement` | 库存/在途/缺料数量、满足方式 |
| S1.1.3 | 齐套检查记录模型 | 🔴 P0 | ❌ | `mat_kit_check` | 检查时间、齐套率、可开工确认 |
| S1.1.4 | 缺料预警模型（扩展） | 🔴 P0 | ❌ | `mat_shortage_alert` | 扩展现有表：预警级别、影响评估、处理方案 |
| S1.1.5 | 缺料上报模型 | 🔴 P0 | ❌ | `mat_shortage_report` | 车间上报、紧急程度、图片、确认状态 |
| S1.1.6 | 到货跟踪模型 | 🔴 P0 | ❌ | `mat_arrival_tracking` | PO 关联、承诺/预计/实际到货、延迟标记 |
| S1.1.7 | 物料替代申请模型 | 🟡 P1 | ❌ | `mat_substitution_request` | 原料/替代料、审批流程 |
| S1.1.8 | 物料调拨申请模型 | 🟡 P1 | ❌ | `mat_transfer_request` | 跨工单调拨、审批流程 |
| S1.1.9 | 预警处理日志模型 | 🟡 P1 | ❌ | `mat_alert_log` | 操作记录、状态变更追溯 |
| S1.1.10 | 缺料统计日报模型 | 🟡 P1 | ❌ | `mat_shortage_daily_report` | 每日齐套率、响应时效统计 |

#### S1.2 SQL 迁移脚本任务

| 序号 | 任务 | 优先级 | 状态 | 文件名 |
|:----:|------|:------:|:----:|--------|
| S1.2.1 | 生成 SQLite 迁移脚本 | 🔴 P0 | ❌ | `20260105_shortage_management_sqlite.sql` |
| S1.2.2 | 生成 MySQL 迁移脚本 | 🔴 P0 | ❌ | `20260105_shortage_management_mysql.sql` |

---

### S2. 缺料管理模块 - API 补全

> 当前任务清单已有部分缺料 API，以下为设计文档要求但缺失的完整 API

#### S2.1 齐套检查 API

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| S2.1.1 | 待检查工单列表 | 🔴 P0 | ❌ | `GET /kit-check/work-orders` | 未来 7 天开工工单 |
| S2.1.2 | 工单齐套详情 | 🔴 P0 | ❌ | `GET /kit-check/work-orders/{id}` | BOM 明细+库存+在途 |
| S2.1.3 | 执行齐套检查 | 🔴 P0 | ❌ | `POST /kit-check/work-orders/{id}/check` | 计算齐套率 |
| S2.1.4 | 确认开工 | 🔴 P0 | ❌ | `POST /kit-check/work-orders/{id}/confirm` | 强制开工确认 |
| S2.1.5 | 齐套检查历史 | 🟡 P1 | ❌ | `GET /kit-check/history` | 历史检查记录 |

#### S2.2 缺料上报 API（现场）

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| S2.2.1 | 上报列表 | 🔴 P0 | ❌ | `GET /shortage-reports` | 分页+状态筛选 |
| S2.2.2 | 提交缺料上报 | 🔴 P0 | ❌ | `POST /shortage-reports` | 扫码/选择物料 |
| S2.2.3 | 上报详情 | 🔴 P0 | ❌ | `GET /shortage-reports/{id}` | |
| S2.2.4 | 确认上报 | 🔴 P0 | ❌ | `POST /shortage-reports/{id}/confirm` | 仓管确认 |
| S2.2.5 | 处理上报 | 🔴 P0 | ❌ | `POST /shortage-reports/{id}/handle` | 开始处理 |
| S2.2.6 | 解决上报 | 🔴 P0 | ❌ | `POST /shortage-reports/{id}/resolve` | 关闭工单 |
| S2.2.7 | 驳回上报 | 🟡 P1 | ❌ | `POST /shortage-reports/{id}/reject` | 无效上报 |

#### S2.3 到货跟踪 API

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| S2.3.1 | 到货列表 | 🔴 P0 | ❌ | `GET /arrivals` | 在途物料列表 |
| S2.3.2 | 到货详情 | 🔴 P0 | ❌ | `GET /arrivals/{id}` | |
| S2.3.3 | 更新到货状态 | 🔴 P0 | ❌ | `PUT /arrivals/{id}/status` | 已发货/到厂/入库 |
| S2.3.4 | 创建跟催记录 | 🔴 P0 | ❌ | `POST /arrivals/{id}/follow-up` | 跟催供应商 |
| S2.3.5 | 确认收货 | 🔴 P0 | ❌ | `POST /arrivals/{id}/receive` | 质检+入库 |
| S2.3.6 | 延迟到货列表 | 🟡 P1 | ❌ | `GET /arrivals/delayed` | 延迟预警 |

#### S2.4 物料替代/调拨 API

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| S2.4.1 | 替代申请列表 | 🟡 P1 | ❌ | `GET /substitutions` | |
| S2.4.2 | 创建替代申请 | 🟡 P1 | ❌ | `POST /substitutions` | |
| S2.4.3 | 审批替代申请 | 🟡 P1 | ❌ | `POST /substitutions/{id}/approve` | 技术+生产审批 |
| S2.4.4 | 执行替代 | 🟡 P1 | ❌ | `POST /substitutions/{id}/execute` | |
| S2.4.5 | 调拨申请列表 | 🟡 P1 | ❌ | `GET /transfers` | |
| S2.4.6 | 创建调拨申请 | 🟡 P1 | ❌ | `POST /transfers` | |
| S2.4.7 | 审批调拨申请 | 🟡 P1 | ❌ | `POST /transfers/{id}/approve` | |
| S2.4.8 | 执行调拨 | 🟡 P1 | ❌ | `POST /transfers/{id}/execute` | |

#### S2.5 缺料统计分析 API

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| S2.5.1 | 缺料看板数据 | 🔴 P0 | ❌ | `GET /shortage/dashboard` | 齐套率分布+预警汇总 |
| S2.5.2 | 齐套率统计 | 🟡 P1 | ❌ | `GET /shortage/statistics/kit-rate` | 按项目/车间/时间 |
| S2.5.3 | 缺料原因分析 | 🟡 P1 | ❌ | `GET /shortage/statistics/cause-analysis` | Top N 原因 |
| S2.5.4 | 供应商交期分析 | 🟡 P1 | ❌ | `GET /shortage/statistics/supplier-delivery` | 准时率排名 |
| S2.5.5 | 获取缺料日报 | 🟡 P1 | ❌ | `GET /shortage/daily-report` | 每日汇总 |

---

### S3. 研发项目管理 - 数据库表补全

> 参考设计文档：`研发项目管理/` 目录
> 当前状态：API 任务已定义，但无独立数据库表

#### S3.1 ORM 模型开发任务

| 序号 | 任务 | 优先级 | 状态 | 表名 | 说明 |
|:----:|------|:------:|:----:|------|------|
| S3.1.1 | 研发项目主表模型 | 🟡 P1 | ❌ | `rd_project` | 自主/委托/合作研发、立项信息 |
| S3.1.2 | 研发项目分类模型 | 🟡 P1 | ❌ | `rd_project_category` | 分类字典 |
| S3.1.3 | 研发费用模型 | 🟡 P1 | ❌ | `rd_cost` | 人工/材料/折旧/其他 |
| S3.1.4 | 费用类型模型 | 🟡 P1 | ❌ | `rd_cost_type` | 六大费用类型 |
| S3.1.5 | 费用分摊规则模型 | 🟢 P2 | ❌ | `rd_cost_allocation_rule` | 共享费用分摊 |
| S3.1.6 | 研发报表记录模型 | 🟢 P2 | ❌ | `rd_report_record` | 报表生成记录 |

#### S3.2 SQL 迁移脚本任务

| 序号 | 任务 | 优先级 | 状态 | 文件名 |
|:----:|------|:------:|:----:|--------|
| S3.2.1 | 生成 SQLite 迁移脚本 | 🟡 P1 | ❌ | `20260105_rd_project_sqlite.sql` |
| S3.2.2 | 生成 MySQL 迁移脚本 | 🟡 P1 | ❌ | `20260105_rd_project_mysql.sql` |

---

### S4. 售后工单/知识库 - 数据库表新建

> 参考设计文档：`非标自动化项目管理系统_整体规划方案.md` 第三期功能
> 当前状态：API 任务已定义，但无数据库表

#### S4.1 ORM 模型开发任务

| 序号 | 任务 | 优先级 | 状态 | 表名 | 说明 |
|:----:|------|:------:|:----:|------|------|
| S4.1.1 | 售后工单主表模型 | 🟡 P1 | ❌ | `service_order` | 工单编号、客户、设备、问题描述 |
| S4.1.2 | 工单处理记录模型 | 🟡 P1 | ❌ | `service_order_action` | 处理过程、耗时、配件 |
| S4.1.3 | 设备服务档案模型 | 🟡 P1 | ❌ | `machine_service_history` | 设备维保记录汇总 |
| S4.1.4 | 知识库条目模型 | 🟢 P2 | ❌ | `knowledge_article` | 标题、内容、标签 |
| S4.1.5 | 知识分类模型 | 🟢 P2 | ❌ | `knowledge_category` | 分类树 |
| S4.1.6 | 问题解决方案模型 | 🟢 P2 | ❌ | `issue_solution` | 问题-方案关联 |

#### S4.2 SQL 迁移脚本任务

| 序号 | 任务 | 优先级 | 状态 | 文件名 |
|:----:|------|:------:|:----:|--------|
| S4.2.1 | 生成 SQLite 迁移脚本 | 🟡 P1 | ❌ | `20260105_service_knowledge_sqlite.sql` |
| S4.2.2 | 生成 MySQL 迁移脚本 | 🟡 P1 | ❌ | `20260105_service_knowledge_mysql.sql` |

---

### S5. 项目复盘 - 数据库表新建

> 参考设计文档：`非标自动化项目管理系统_整体规划方案.md` 第三期功能
> 当前状态：API 任务已定义，但无数据库表

#### S5.1 ORM 模型开发任务

| 序号 | 任务 | 优先级 | 状态 | 表名 | 说明 |
|:----:|------|:------:|:----:|------|------|
| S5.1.1 | 复盘报告主表模型 | 🟢 P2 | ❌ | `project_review` | 复盘时间、参与人、结论 |
| S5.1.2 | 经验教训模型 | 🟢 P2 | ❌ | `project_lesson` | 问题描述、根因、改进措施 |
| S5.1.3 | 最佳实践模型 | 🟢 P2 | ❌ | `project_best_practice` | 可复用经验沉淀 |

#### S5.2 SQL 迁移脚本任务

| 序号 | 任务 | 优先级 | 状态 | 文件名 |
|:----:|------|:------:|:----:|--------|
| S5.2.1 | 生成 SQLite 迁移脚本 | 🟢 P2 | ❌ | `20260105_project_review_sqlite.sql` |
| S5.2.2 | 生成 MySQL 迁移脚本 | 🟢 P2 | ❌ | `20260105_project_review_mysql.sql` |

---

### S6. 通知中心 - API 新建

> 当前状态：设计文档提及但任务清单完全缺失

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| S6.1 | 获取通知列表 | 🔴 P0 | ❌ | `GET /notifications` | 分页+已读筛选 |
| S6.2 | 获取未读数量 | 🔴 P0 | ❌ | `GET /notifications/unread-count` | 角标数字 |
| S6.3 | 标记单条已读 | 🔴 P0 | ❌ | `PUT /notifications/{id}/read` | |
| S6.4 | 批量标记已读 | 🟡 P1 | ❌ | `PUT /notifications/batch-read` | |
| S6.5 | 全部标记已读 | 🟡 P1 | ❌ | `PUT /notifications/read-all` | |
| S6.6 | 删除通知 | 🟢 P2 | ❌ | `DELETE /notifications/{id}` | |
| S6.7 | 通知设置 | 🟢 P2 | ❌ | `GET /notifications/settings` | 用户偏好 |
| S6.8 | 更新通知设置 | 🟢 P2 | ❌ | `PUT /notifications/settings` | |

---

### S7. 批量操作 API 补充

> 当前状态：部分已在 5.8 节，以下为补充完善

| 序号 | 任务 | 优先级 | 状态 | API 路径 | 说明 |
|:----:|------|:------:|:----:|----------|------|
| S7.1 | 批量提醒 | 🟡 P1 | ❌ | `POST /batch/remind` | 发送催办通知 |
| S7.2 | 批量打标签 | 🟡 P1 | ❌ | `POST /batch/tag` | 添加/移除标签 |
| S7.3 | 批量启动任务 | 🟡 P1 | ❌ | `POST /batch/start` | 批量开始 |
| S7.4 | 批量暂停任务 | 🟡 P1 | ❌ | `POST /batch/pause` | 批量暂停 |
| S7.5 | 批量删除 | 🟢 P2 | ❌ | `POST /batch/delete` | 仅限个人任务 |

---

### S8. 前端补充页面

#### S8.1 缺料管理页面

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| S8.1.1 | 齐套检查列表页 | 🔴 P0 | ❌ | 工单齐套状态一览 |
| S8.1.2 | 齐套检查详情页 | 🔴 P0 | ❌ | BOM 明细+缺料项+确认开工 |
| S8.1.3 | 缺料上报页（移动端） | 🔴 P0 | ❌ | 扫码+拍照+提交 |
| S8.1.4 | 到货跟踪页 | 🟡 P1 | ❌ | 在途物料+跟催 |
| S8.1.5 | 物料替代/调拨页 | 🟡 P1 | ❌ | 申请+审批 |
| S8.1.6 | 缺料统计分析页 | 🟡 P1 | ❌ | 图表+报表 |

#### S8.2 售后/知识库页面

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| S8.2.1 | 售后工单列表页 | 🟡 P1 | ❌ | 工单状态+筛选 |
| S8.2.2 | 售后工单详情页 | 🟡 P1 | ❌ | 处理记录+配件 |
| S8.2.3 | 知识库首页 | 🟢 P2 | ❌ | 搜索+分类 |
| S8.2.4 | 知识库详情页 | 🟢 P2 | ❌ | 内容+相关问题 |

#### S8.3 通知中心页面

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| S8.3.1 | 通知下拉面板 | 🔴 P0 | ❌ | 头部角标+快速预览 |
| S8.3.2 | 通知列表页 | 🔴 P0 | ❌ | 全部通知+批量操作 |
| S8.3.3 | 通知设置页 | 🟢 P2 | ❌ | 接收偏好 |

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
| F.2.11 | 🆕 齐套看板页 | 🔴 P0 | ❌ | 齐套率分布+预警汇总 |
| F.2.12 | 🆕 缺料预警页 | 🔴 P0 | ❌ | 预警列表+处理 |
| F.2.13 | 🆕 物料需求汇总页 | 🟡 P1 | ❌ | 多项目需求 |
| F.2.14 | 预警中心页 | 🔴 P0 | ❌ | 列表+统计 |
| F.2.15 | 异常管理页 | 🟡 P1 | ❌ | 列表+详情 |
| F.2.16 | 🆕 WBS 模板管理页 | 🔴 P0 | ❌ | 模板+任务 |
| F.2.17 | 🆕 项目任务列表页 | 🔴 P0 | ❌ | 任务+依赖 |
| F.2.18 | 🆕 甘特图页面 | 🔴 P0 | ❌ | 进度甘特图 |
| F.2.19 | 🆕 进度填报页 | 🔴 P0 | ❌ | 日报/周报 |
| F.2.20 | 🆕 进度看板页 | 🔴 P0 | ❌ | 多维看板 |

### 7.3 生产管理页面（第一期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.3.1 | 生产驾驶舱 | 🔴 P0 | ❌ | 经理总览看板 |
| F.3.2 | 车间任务看板 | 🔴 P0 | ❌ | 拖拽式看板 |
| F.3.3 | 生产计划列表页 | 🔴 P0 | ❌ | 计划+审批 |
| F.3.4 | 排产日历页 | 🟡 P1 | ❌ | 日历+甘特 |
| F.3.5 | 工单列表页 | 🔴 P0 | ❌ | 列表+筛选 |
| F.3.6 | 工单详情页 | 🔴 P0 | ❌ | 进度+报工记录 |
| F.3.7 | 派工管理页 | 🔴 P0 | ❌ | 批量派工 |
| F.3.8 | 报工列表页 | 🔴 P0 | ❌ | 待审批+已审批 |
| F.3.9 | 领料单管理页 | 🔴 P0 | ❌ | 申请+审批 |
| F.3.10 | 生产异常页 | 🔴 P0 | ❌ | 上报+处理 |
| F.3.11 | 车间/工位配置页 | 🟡 P1 | ❌ | 基础配置 |
| F.3.12 | 生产人员管理页 | 🟡 P1 | ❌ | 人员+技能 |
| F.3.13 | 设备管理页 | 🟡 P1 | ❌ | 设备+保养 |
| F.3.14 | 工序字典页 | 🟡 P1 | ❌ | 工序+工时 |
| F.3.15 | 生产报表页 | 🟡 P1 | ❌ | 效率+产能 |

### 7.4 生产移动端页面（第一期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.M.1 | 工人任务列表 | 🔴 P0 | ❌ | 我的任务 |
| F.M.2 | 扫码开工 | 🔴 P0 | ❌ | 扫码+开工 |
| F.M.3 | 进度上报 | 🔴 P0 | ❌ | 进度+数量 |
| F.M.4 | 完工报告 | 🔴 P0 | ❌ | 完工+质量 |
| F.M.5 | 异常上报 | 🔴 P0 | ❌ | 拍照+上报 |
| F.M.6 | 领料申请 | 🔴 P0 | ❌ | 移动领料 |
| F.M.7 | 我的工时 | 🟡 P1 | ❌ | 工时统计 |

### 7.5 协同页面（第二期）

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.5.1 | ECN 列表页 | 🔴 P0 | ❌ | 列表+状态筛选 |
| F.5.2 | ECN 详情页 | 🔴 P0 | ❌ | 流程+评估+任务 |
| F.5.3 | ECN 创建/编辑 | 🔴 P0 | ❌ | 多步骤表单 |
| F.5.4 | 外协订单列表 | 🔴 P0 | ❌ | 列表+筛选 |
| F.5.5 | 外协订单详情 | 🔴 P0 | ❌ | 进度+质检 |
| F.5.6 | 验收单列表 | 🔴 P0 | ❌ | FAT/SAT 分类 |
| F.5.7 | 验收执行页 | 🔴 P0 | ❌ | 检查项+问题 |
| F.5.8 | 资源负荷看板 | 🟡 P1 | ❌ | 甘特图+统计 |
| F.5.9 | 🆕 负荷热力图页 | 🟡 P1 | ❌ | 按周展示 |

### 7.5A PMO 项目管理部页面（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.5A.1 | PMO 驾驶舱 | 🟡 P1 | ❌ | 项目全景+预警+负荷 |
| F.5A.2 | 立项申请列表 | 🟡 P1 | ❌ | 列表+状态 |
| F.5A.3 | 立项申请表单 | 🟡 P1 | ❌ | 多步骤表单 |
| F.5A.4 | 立项评审页 | 🟡 P1 | ❌ | 评审+审批 |
| F.5A.5 | 项目阶段门页 | 🟡 P1 | ❌ | 阶段流转 |
| F.5A.6 | 风险管理页 | 🟡 P1 | ❌ | 列表+矩阵 |
| F.5A.7 | 项目会议管理 | 🟢 P2 | ❌ | 会议+纪要 |
| F.5A.8 | 项目结项页 | 🟡 P1 | ❌ | 结项+归档 |
| F.5A.9 | 项目状态周报 | 🟡 P1 | ❌ | 自动生成 |

### 7.5B 售前技术支持页面（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.5B.1 | 售前工作台 | 🟡 P1 | ❌ | 待办+统计 |
| F.5B.2 | 支持工单列表 | 🟡 P1 | ❌ | 销售/售前双视角 |
| F.5B.3 | 工单看板页 | 🟡 P1 | ❌ | 拖拽看板 |
| F.5B.4 | 支持申请表单 | 🟡 P1 | ❌ | 销售提交 |
| F.5B.5 | 工单处理页 | 🟡 P1 | ❌ | 售前处理 |
| F.5B.6 | 方案设计工作台 | 🟡 P1 | ❌ | 方案+成本 |
| F.5B.7 | 方案库页面 | 🟡 P1 | ❌ | 模板+案例 |
| F.5B.8 | 投标管理页 | 🟡 P1 | ❌ | 投标跟踪 |
| F.5B.9 | 售前统计报表 | 🟡 P1 | ❌ | 工作量+转化率 |

### 7.5C 个人任务中心页面（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.5C.1 | 任务中心首页 | 🔴 P0 | ❌ | 概览+紧急+今日 |
| F.5C.2 | 任务列表页 | 🔴 P0 | ❌ | 分类Tab+筛选 |
| F.5C.3 | 任务卡片组件 | 🔴 P0 | ❌ | 详情+快捷操作 |
| F.5C.4 | 任务详情抽屉 | 🔴 P0 | ❌ | 详情+评论+日志 |
| F.5C.5 | 任务转办弹窗 | 🟡 P1 | ❌ | 选人+原因 |
| F.5C.6 | 新建任务弹窗 | 🟡 P1 | ❌ | 个人任务 |
| F.5C.7 | 任务日历视图 | 🟢 P2 | ❌ | 日历展示 |

### 7.5D 缺料管理页面（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.5D.1 | 缺料管理看板 | 🔴 P0 | ❌ | 预警+齐套+到货 |
| F.5D.2 | 缺料上报列表 | 🔴 P0 | ❌ | 上报+处理 |
| F.5D.3 | 到货跟踪列表 | 🔴 P0 | ❌ | 在途+延迟 |
| F.5D.4 | 替代申请列表 | 🟡 P1 | ❌ | 申请+审批 |
| F.5D.5 | 调拨申请列表 | 🟡 P1 | ❌ | 申请+执行 |
| F.5D.6 | 缺料日报页 | 🟡 P1 | ❌ | 每日统计 |

### 7.5E 移动端缺料上报（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.5E.1 | 扫码上报页 | 🔴 P0 | ❌ | 扫工单+选物料 |
| F.5E.2 | 上报表单页 | 🔴 P0 | ❌ | 数量+拍照+描述 |
| F.5E.3 | 我的上报记录 | 🔴 P0 | ❌ | 查看进度 |
| F.5E.4 | 上报反馈页 | 🟡 P1 | ❌ | 处理结果 |

### 7.6 销售管理页面（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.6.1 | 线索列表页 | 🔴 P0 | ❌ | 列表+跟进 |
| F.6.2 | 线索详情页 | 🔴 P0 | ❌ | 跟进记录+转换 |
| F.6.3 | 商机列表页 | 🔴 P0 | ❌ | 列表+漏斗 |
| F.6.4 | 商机详情页 | 🔴 P0 | ❌ | 阶段流转 |
| F.6.5 | 商机看板页 | 🔴 P0 | ❌ | 销售漏斗看板 |
| F.6.6 | 报价列表页 | 🔴 P0 | ❌ | 列表+版本 |
| F.6.7 | 报价创建/编辑 | 🔴 P0 | ❌ | 成本拆解表单 |
| F.6.8 | 合同列表页 | 🔴 P0 | ❌ | 列表+状态 |
| F.6.9 | 合同详情页 | 🔴 P0 | ❌ | 付款节点+里程碑 |
| F.6.10 | 发票列表页 | 🔴 P0 | ❌ | 开票管理 |
| F.6.11 | 回款列表页 | 🔴 P0 | ❌ | 回款+核销 |
| F.6.12 | 应收账款页 | 🟡 P1 | ❌ | 账龄分析 |

### 7.7 决策与分析页面（第三期）

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.7.1 | 决策驾驶舱 | 🟢 P2 | ❌ | 综合看板 |
| F.7.2 | 成本分析页 | 🟢 P2 | ❌ | 图表+对比 |
| F.7.3 | 项目复盘页 | 🟢 P2 | ❌ | 表单+统计 |
| F.7.4 | 知识库页面 | 🟢 P2 | ❌ | 搜索+分类 |
| F.7.5 | 销售业绩报表 | 🟢 P2 | ❌ | 🆕 漏斗+转化 |

### 7.9 绩效管理页面（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.9.1 | 个人绩效页 | 🟡 P1 | ❌ | 我的绩效报告+趋势图 |
| F.9.2 | 团队绩效页 | 🟡 P1 | ❌ | 团队成员排名+等级分布 |
| F.9.3 | 部门绩效页 | 🟡 P1 | ❌ | 部门汇总+对比 |
| F.9.4 | 绩效排行榜页 | 🟡 P1 | ❌ | 多维度排行 |
| F.9.5 | 项目绩效页 | 🟡 P1 | ❌ | 项目成员贡献 |
| F.9.6 | 绩效对比页 | 🟢 P2 | ❌ | 多人绩效对比 |
| F.9.7 | 绩效趋势图组件 | 🟡 P1 | ❌ | 可复用图表组件 |

### 7.10 报表中心页面（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.10.1 | 报表中心首页 | 🟡 P1 | ❌ | 报表列表+快捷入口 |
| F.10.2 | 报表生成页 | 🟡 P1 | ❌ | 选择类型/角色/周期 |
| F.10.3 | 报表预览页 | 🟡 P1 | ❌ | 在线预览+图表 |
| F.10.4 | 多角色对比页 | 🟢 P2 | ❌ | 同一报表多视角 |
| F.10.5 | 报表模板管理 | 🟢 P2 | ❌ | 模板列表+配置 |
| F.10.6 | 报表导出组件 | 🟡 P1 | ❌ | xlsx/pdf/html导出 |

### 7.11 工时管理页面（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.11.1 | 周工时填报页 | 🔴 P0 | ❌ | 按周填报+任务分组 |
| F.11.2 | 工时日历页 | 🟡 P1 | ❌ | 日历视图工时 |
| F.11.3 | 工时审批页 | 🟡 P1 | ❌ | 待审批列表+批量审批 |
| F.11.4 | 我的工时统计 | 🟡 P1 | ❌ | 个人月度统计+图表 |
| F.11.5 | 项目工时统计 | 🟡 P1 | ❌ | 项目级工时汇总 |
| F.11.6 | 部门工时报表 | 🟡 P1 | ❌ | 部门工时分析 |

### 7.12 数据导入导出页面（第二期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.12.1 | 数据导入页 | 🟡 P1 | ❌ | 模板下载+上传+预览 |
| F.12.2 | 导入预览弹窗 | 🟡 P1 | ❌ | 数据预览+错误提示 |
| F.12.3 | 导入结果页 | 🟡 P1 | ❌ | 成功/失败统计 |
| F.12.4 | 数据导出页 | 🟡 P1 | ❌ | 选择类型+筛选导出 |

### 7.8 研发项目管理页面（第三期）🆕

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| F.8.1 | 研发项目列表页 | 🟡 P1 | ❌ | 列表+状态筛选 |
| F.8.2 | 研发项目详情页 | 🟡 P1 | ❌ | 基本信息+费用+工时 |
| F.8.3 | 研发项目立项表单 | 🟡 P1 | ❌ | 多步骤表单 |
| F.8.4 | 工时填报页 | 🟡 P1 | ❌ | 日历视图+快捷填报 |
| F.8.5 | 工时审批页 | 🟡 P1 | ❌ | 批量审批 |
| F.8.6 | 我的工时统计 | 🟡 P1 | ❌ | 个人工时看板 |
| F.8.7 | 研发费用录入页 | 🟡 P1 | ❌ | 分类录入表单 |
| F.8.8 | 研发费用汇总页 | 🟡 P1 | ❌ | 多维统计+图表 |
| F.8.9 | 研发费用报表页 | 🟡 P1 | ❌ | 辅助账+加计扣除 |
| F.8.10 | 研发投入分析页 | 🟢 P2 | ❌ | 研发强度+趋势 |

---

## 八、后台服务任务

| 序号 | 任务 | 优先级 | 状态 | 说明 |
|:----:|------|:------:|:----:|------|
| S.1 | 健康度自动计算服务 | 🔴 P0 | ❌ | 定时任务 |
| S.2 | 缺料预警生成服务 | 🔴 P0 | ❌ | 定时任务 |
| S.3 | 里程碑预警服务 | 🔴 P0 | ❌ | 定时任务 |
| S.4 | 🆕 任务延期预警服务 | 🔴 P0 | ❌ | 进度跟踪 |
| S.5 | 🆕 生产计划预警服务 | 🔴 P0 | ❌ | 生产管理 |
| S.6 | 🆕 报工超时提醒服务 | 🔴 P0 | ❌ | 生产管理 |
| S.7 | 外协交期预警服务 | 🟡 P1 | ❌ | 定时任务 |
| S.8 | 收款提醒服务 | 🟡 P1 | ❌ | 定时任务 |
| S.9 | 🆕 逾期应收预警服务 | 🟡 P1 | ❌ | O2C 模块 |
| S.10 | 预警升级服务 | 🟡 P1 | ❌ | 定时任务 |
| S.11 | 健康度快照服务 | 🟡 P1 | ❌ | 每日快照 |
| S.12 | 消息推送服务 | 🟡 P1 | ❌ | 企微/邮件 |
| S.13 | 🆕 商机阶段超时提醒 | 🟡 P1 | ❌ | O2C 模块 |
| S.14 | 🆕 进度汇总计算服务 | 🔴 P0 | ❌ | 自动汇总 |
| S.15 | 🆕 生产日报自动生成 | 🟡 P1 | ❌ | 生产管理 |
| S.16 | 🆕 设备保养提醒服务 | 🟢 P2 | ❌ | 生产管理 |
| S.17 | 🆕 每日齐套检查服务 | 🔴 P0 | ❌ | 缺料管理 |
| S.18 | 🆕 到货延迟检查服务 | 🔴 P0 | ❌ | 缺料管理 |
| S.19 | 🆕 缺料日报生成服务 | 🟡 P1 | ❌ | 缺料管理 |
| S.20 | 🆕 岗位职责任务生成 | 🟡 P1 | ❌ | 任务中心 |
| S.21 | 🆕 任务到期提醒服务 | 🔴 P0 | ❌ | 任务中心 |
| S.22 | 🆕 售前工单超时提醒 | 🟡 P1 | ❌ | 售前支持 |
| S.23 | 🆕 负荷超限预警服务 | 🟡 P1 | ❌ | 资源负荷 |

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

## 附录B：新增模块说明

| 模块 | 参考设计文档 | 新增任务数 |
|------|-------------|:----------:|
| 进度跟踪 | `进度跟踪模块_详细设计文档.md` | +27 |
| 齐套率与物料保障 | `采购与物料管理模块_详细设计文档.md` | +21 |
| 生产管理 | `project-progress-module/docs/PRODUCTION_MODULE_DESIGN.md` | +75 |
| PMO 项目管理部 | `project-progress-module/docs/PMO_MODULE_DESIGN.md` | +32 |
| 售前技术支持 | `project-progress-module/docs/PRESALE_SUPPORT_DESIGN.md` | +30 |
| 个人任务中心 | `project-progress-module/docs/TASK_CENTER_DESIGN.md` | +12 |
| 任务批量操作 | `project-progress-module/backend/app/api/v1/batch_operations.py` | +10 |
| 缺料管理（详细） | `project-progress-module/docs/SHORTAGE_MANAGEMENT_DESIGN.md` | +24 |
| 销售管理(O2C) | `销售管理模块_线索到回款_设计文档.md` | +57 |
| 研发项目管理 | `研发项目管理/` 目录 | +32 |
| 绩效管理 | `project-progress-module/backend/app/api/v1/performance.py` | +9 |
| 报表中心 | `project-progress-module/backend/app/api/v1/reports.py` | +9 |
| 工时管理详细 | `project-progress-module/backend/app/api/v1/timesheet.py` | +11 |
| 数据导入导出 | `project-progress-module/backend/app/api/v1/data_import.py` | +10 |
| 前端页面 | - | +120 |
| 后台服务 | - | +15 |
| **合计** | - | **+494** |

---

## 附录C：生产管理模块说明

**核心定位**：非标自动化企业的生产执行核心模块

**组织架构**：
- 生产部经理（统筹）
- 车间主管（机加/装配/调试）
- 生产工人（执行报工）

**核心流程**：
```
项目计划 → 生产计划 → 任务派工 → 领料 → 开工报工 → 进度上报 → 完工报告 → 质检入库
```

**功能范围**：
1. **车间/工位管理**：车间配置、工位管理、产能统计
2. **生产计划**：主生产计划、车间作业计划、排产日历
3. **生产工单**：工单创建、任务派工、进度跟踪
4. **报工系统**：扫码开工、进度上报、完工报告、工时审批
5. **生产领料**：领料申请、审批、发料确认
6. **生产异常**：异常上报、处理、统计分析
7. **生产报表**：生产日报、效率分析、产能利用率

**移动端支持**：
- 工人任务查看
- 扫码开工
- 进度/完工报告
- 异常上报
- 领料申请

---

## 附录D：project-progress-module 模块说明

**来源目录**：`claude 设计方案/project-progress-module/`

**包含设计文档**：
- `docs/PMO_MODULE_DESIGN.md` - 项目管理部模块
- `docs/PRESALE_SUPPORT_DESIGN.md` - 售前技术支持
- `docs/TASK_CENTER_DESIGN.md` - 个人任务中心
- `docs/SHORTAGE_MANAGEMENT_DESIGN.md` - 缺料管理详细设计
- `docs/PRODUCTION_MODULE_DESIGN.md` - 生产管理模块

**包含API参考**：
- `backend/app/api/v1/pmo.py` - PMO接口
- `backend/app/api/v1/presale.py` - 售前接口
- `backend/app/api/v1/task_center.py` - 任务中心接口
- `backend/app/api/v1/material.py` - 物料/缺料接口
- `backend/app/api/v1/workload.py` - 负荷管理接口
- `backend/app/api/v1/timesheet.py` - 工时管理接口
- `backend/app/api/v1/performance.py` - 绩效管理接口

---

## 附录E：研发项目管理模块说明

**适用场景**：
- IPO 合规要求
- 高新技术企业认定
- 研发费用加计扣除（175%）
- 研发投入强度统计

**核心功能**：
1. **研发项目立项**：自主研发/委托研发/合作研发分类管理
2. **工时记录系统**：研发人员工时填报、审批、统计
3. **研发费用归集**：人工费、材料费、折旧费、其他费用
4. **合规报表输出**：辅助账、加计扣除明细表、高新认定表

**与非标项目关系**：
- 非标项目中的研发活动可关联研发项目
- 研发人员工时可分配到多个项目
- 研发费用从非标项目成本中归集

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-01-03 | 初始版本，基础 API 任务清单 |
| v1.1 | 2026-01-04 | 新增进度跟踪模块、销售管理(O2C)模块 |
| v1.2 | 2026-01-04 | 新增研发项目管理模块（IPO合规） |
| v1.3 | 2026-01-04 | 新增生产管理模块、移动端页面 |
| v1.4 | 2026-01-04 | 扩展齐套率与物料保障模块 |
| v1.5 | 2026-01-04 | 新增PMO项目管理部、售前技术支持、个人任务中心、缺料管理详细模块 |
| v1.6 | 2026-01-04 | 新增绩效管理、报表中心、工时管理详细、数据导入导出、任务批量操作模块；补充前端页面 |
| v1.7 | 2026-01-04 | 🆕 **补全缺失模块**：缺料管理数据库表(10张)+API(30+端点)、研发项目数据库表(6张)、售后/知识库数据库表(6张)、项目复盘数据库表(3张)、通知中心API(8端点)、批量操作补充(5端点)、前端补充页面(13页) |

---

## 附录F：v1.6 新增模块说明

### 绩效管理模块
- **核心功能**：多层级绩效视图（个人→团队→部门→公司）
- **关键特性**：
  - 绩效指标：工时、任务完成率、质量、协作
  - 绩效等级：优秀(≥90)、良好(75-89)、合格(60-74)、待改进(<60)
  - 权限控制：总经理看全局、部门经理看本部门、项目经理看项目成员

### 报表中心模块
- **核心功能**：多角色视角智能报表
- **报表类型**：项目周报、项目月报、部门周报、部门月报、公司月报、成本分析、负荷分析、风险报告
- **导出格式**：Excel、PDF、HTML
- **特色功能**：同一报表可切换不同角色视角（总经理、部门经理、项目经理、工程师等）

### 工时管理详细模块
- **核心功能**：周工时表填报、审批流程
- **填报方式**：按周填报，任务分组展示
- **审批流程**：草稿→提交→待审核→已通过/已驳回
- **统计分析**：月度汇总、项目分布、加班统计

### 数据导入导出模块
- **导入类型**：项目、任务、人员、工时、客户、部门
- **导入流程**：下载模板→填写数据→上传预览→验证→导入
- **导出类型**：项目列表、项目详情、任务列表、工时数据、负荷数据

### 任务批量操作
- **支持操作**：批量完成、批量转办、批量设置优先级、批量更新进度、批量催办、批量开始/暂停、批量打标签
- **使用限制**：单次最多操作20-50个任务
- **权限控制**：删除操作仅限个人任务

---

## 附录G：v1.7 补充模块汇总

### 数据库表补充清单（共 25 张新表）

| 模块 | 新增表数 | 优先级 | 状态 | 说明 |
|------|:--------:|:------:|:----:|------|
| 缺料管理 | 10 | 🔴 P0 | ❌ | 齐套检查、上报、跟踪、替代、调拨、日报 |
| 研发项目 | 6 | 🟡 P1 | ❌ | 研发项目、费用归集、分摊规则 |
| 售后/知识库 | 6 | 🟡 P1 | ❌ | 工单、档案、知识条目、方案 |
| 项目复盘 | 3 | 🟢 P2 | ❌ | 复盘报告、经验教训、最佳实践 |

### API 补充清单（共 60+ 端点）

| 模块 | 新增端点 | 优先级 | 说明 |
|------|:--------:|:------:|------|
| 齐套检查 API | 5 | 🔴 P0 | 检查、确认、历史 |
| 缺料上报 API | 7 | 🔴 P0 | 上报、确认、处理、解决 |
| 到货跟踪 API | 6 | 🔴 P0 | 列表、状态、跟催、收货 |
| 替代/调拨 API | 8 | 🟡 P1 | 申请、审批、执行 |
| 缺料统计 API | 5 | 🟡 P1 | 看板、齐套率、原因分析 |
| 通知中心 API | 8 | 🔴 P0 | 列表、已读、设置 |
| 批量操作补充 | 5 | 🟡 P1 | 提醒、标签、启动、暂停 |

### 前端页面补充清单（共 13 页）

| 模块 | 新增页面 | 优先级 |
|------|:--------:|:------:|
| 缺料管理 | 6 | 🔴/🟡 P0-P1 |
| 售后/知识库 | 4 | 🟡/🟢 P1-P2 |
| 通知中心 | 3 | 🔴/🟢 P0-P2 |

---

*文档版本：v1.7*
*更新日期：2026-01-04*
