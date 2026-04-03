# Approvals 模块访问控制评估

> 基于 2026-03-25 代码现状分析，非空话文档。

---

## 一、核心结论：Approvals 不应该走 data_scope

**审批模块的访问模型与 engineer_performance / sales 本质不同。**

| 维度 | engineer_performance | approvals |
|------|---------------------|-----------|
| 数据归属 | 每条记录归属一个人/部门 | 一个审批实例涉及 5+ 种角色 |
| 查询语义 | "我能看哪些人的绩效" | "我参与了哪些审批" |
| 范围维度 | 组织架构（部门/BU/团队） | 流程参与关系 |
| 典型过滤 | `WHERE dept_id IN (...)` | `WHERE user_id IN (发起人, 审批人, 抄送人, 代理人)` |

engineer_performance 的 `EngPerfScopeContext` 用 `scope_type=DEPT/TEAM/OWN` 按组织架构切数据——这对绩效合理，因为"部门经理看本部门绩效"是天然需求。

但审批不一样：
- **财务总监**审批全公司的报销单，不是因为他 data_scope=ALL，而是因为流程把他设为审批人
- **项目经理**能看到跨部门的合同审批，不是因为他在那个部门，而是因为他是发起人
- **行政助理**代理 CEO 审批，不是因为她有权限，而是因为委托配置生效

如果机械套 data_scope，会出现两类问题：
1. **过度限制**：DEPT 范围的审批人看不到跨部门审批单（但他确实是审批人）
2. **过度放开**：ALL 范围的管理员能看所有审批详情（但他不是参与人，不应该看到表单数据）

---

## 二、推荐模型：participant_scope（参与人可见性）

### 2.1 核心规则

一个用户能看到某审批实例，**当且仅当**他是以下角色之一：

| 角色 | 判定条件 | 可见范围 |
|------|---------|---------|
| 发起人 | `instance.initiator_id == user_id` | 完整详情 + 操作日志 |
| 当前/历史审批人 | `task.assignee_id == user_id` | 完整详情 + 操作日志 |
| 代理审批人 | `task.original_assignee_id != NULL AND task.assignee_id == user_id` | 同审批人 |
| 抄送人 | `cc.cc_user_id == user_id` | 基本信息 + 当前状态（不含表单详情） |
| 模板管理员 | 有 `approval:template:manage` 权限 | 仅模板/流程定义，不含实例数据 |
| 审批管理员 | 有 `approval:admin` 权限（新增） | 全部实例，用于异常处理/终止 |

### 2.2 实现方案：`is_participant` 查询

不需要新建 scope 表，直接用现有数据：

```python
def get_visible_instances(db, user_id, is_admin=False):
    """返回用户可见的审批实例 ID 集合"""
    if is_admin:
        return db.query(ApprovalInstance.id)  # 管理员看全部

    # 我发起的
    initiated = db.query(ApprovalInstance.id).filter(
        ApprovalInstance.initiator_id == user_id
    )
    # 我审批的（含代理）
    tasked = db.query(ApprovalTask.instance_id).filter(
        ApprovalTask.assignee_id == user_id
    )
    # 抄送我的
    cc_ed = db.query(ApprovalCarbonCopy.instance_id).filter(
        ApprovalCarbonCopy.cc_user_id == user_id
    )

    return initiated.union(tasked).union(cc_ed)
```

### 2.3 与 data_scope 的唯一交集

**审批管理后台**（如果需要做"审批运营看板"）可以复用 data_scope 按部门过滤发起人所在部门。但这是可选的增强，不是核心模型。

---

## 三、当前代码中最危险的接口

### 🔴 P0 — 直接越权风险

| 接口 | 文件:行 | 问题 |
|------|---------|------|
| `GET /approvals` | `instances.py:88` | **零过滤**，任何有 `approval:view` 权限的人能列出全部审批实例（含标题、状态、发起人） |
| `GET /approvals/{id}` | `instances.py:128` | **零校验**，能看任意审批的完整详情：表单数据、审批人列表、操作日志 |
| `GET /approval-tasks/{id}` | `tasks.py:31` | **零校验**，能看任意任务详情（含实例标题、审批人信息） |
| `GET /approvals/by-entity/{type}/{id}` | `instances.py:252` | **零过滤**，通过业务实体反查审批，可遍历所有合同/报价单的审批状态 |

### 🟡 P1 — 操作类越权风险

| 接口 | 文件:行 | 问题 |
|------|---------|------|
| `POST /approval-tasks/{id}/remind` | `tasks.py:204` | 任何人可对任意任务催办（应限发起人或同节点审批人） |
| `POST /approval-tasks/instances/{id}/add-cc` | `tasks.py:231` | 任何人可给任意实例加抄送（应限发起人或当前审批人） |
| `POST /approval-tasks/instances/{id}/comments` | `tasks.py:258` | 任何人可在任意实例下评论（应限参与人） |
| `POST /approvals/{id}/terminate` | `instances.py:229` | 仅检查 `approval:approve` 权限，未校验是否为管理员角色 |

### 🟢 P2 — 已有保护的接口（无需改动）

| 接口 | 保护机制 |
|------|---------|
| `POST /approval-tasks/{id}/approve` | `_get_and_validate_task` 校验 `assignee_id == user_id` |
| `POST /approval-tasks/{id}/reject` | 同上 |
| `POST /approval-tasks/{id}/transfer` | 同上 |
| `POST /approvals/{id}/withdraw` | engine 校验 `initiator_id == current_user.id` |
| `PUT /delegates/{id}` | 校验 `delegate.user_id == current_user.id` |
| `DELETE /delegates/{id}` | 同上 |
| `DELETE /comments/{id}` | 校验 `comment.user_id == current_user.id` |
| `GET /pending/mine` | 按 `assignee_id == current_user.id` 过滤 |
| `GET /pending/initiated` | 按 `initiator_id == current_user.id` 过滤 |
| `GET /pending/cc` | 按 `cc_user_id == current_user.id` 过滤 |
| `GET /pending/processed` | 按 `assignee_id == current_user.id` 过滤 |

---

## 四、Sprint 4/5 改造建议

### Sprint 4（本轮，最小安全补丁）

**目标：堵住 P0 越权，不改架构。**

#### 4.1 新建 `app/services/approval_engine/visibility.py`

```python
def check_instance_visible(db, instance_id, user_id, is_admin=False) -> bool:
    """检查用户是否有权查看该审批实例"""
    if is_admin:
        return True
    instance = db.query(ApprovalInstance).get(instance_id)
    if not instance:
        return False
    # 发起人
    if instance.initiator_id == user_id:
        return True
    # 审批人（含代理）
    has_task = db.query(ApprovalTask).filter(
        ApprovalTask.instance_id == instance_id,
        ApprovalTask.assignee_id == user_id,
    ).first()
    if has_task:
        return True
    # 抄送人
    has_cc = db.query(ApprovalCarbonCopy).filter(
        ApprovalCarbonCopy.instance_id == instance_id,
        ApprovalCarbonCopy.cc_user_id == user_id,
    ).first()
    return bool(has_cc)
```

#### 4.2 修改 4 个 P0 接口

- `GET /approvals` → 加 `WHERE instance_id IN (visible_instances_subquery)`
- `GET /approvals/{id}` → 调用 `check_instance_visible`，不可见则 403
- `GET /approval-tasks/{id}` → 先查 task.instance_id，再 `check_instance_visible`
- `GET /approvals/by-entity/{type}/{id}` → 同 list，加 visible 过滤

#### 4.3 修改 3 个 P1 接口

- `POST .../remind` → 限发起人 + 同实例参与人
- `POST .../add-cc` → 限发起人 + 当前审批人
- `POST .../comments` → 限参与人

**预估改动量：~150 行，集中在 visibility.py + 4 个 endpoint 文件。**

### Sprint 5（下轮，可选增强）

| 增强项 | 说明 |
|--------|------|
| 审批管理员角色 | 新增 `approval:admin` 权限，允许运营人员查看全部实例、终止异常流程 |
| 抄送人脱敏 | 抄送人只能看摘要信息，不返回 form_data 字段 |
| 审批中心列表优化 | 前端"全部审批"tab 调用 visible 子查询，替代当前无过滤列表 |
| data_scope 可选叠加 | 如果需要"部门审批管理员"，可在 admin 角色上叠加 data_scope 限制可管理的部门范围 |
| 查询性能优化 | 如果 visible 子查询慢，考虑物化视图或 `approval_participant` 宽表 |

---

## 五、总结

```
不要对 approvals 套 data_scope。

审批的访问控制本质是"参与人可见性"，不是"组织架构数据范围"。
发起人、审批人、代理人、抄送人——这四种角色决定了谁能看到什么。

Sprint 4 只需要一个 check_instance_visible 函数 + 修 4 个接口。
不需要新表、不需要新的 scope 配置、不需要改 RoleDataScope。
```
