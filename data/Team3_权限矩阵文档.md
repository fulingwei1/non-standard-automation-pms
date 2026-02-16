# 系统权限矩阵文档

**版本：** v1.0  
**日期：** 2026-02-16  
**系统：** 非标自动化项目管理系统

---

## 一、权限体系概览

### 1.1 权限总量
- **总权限数：** 125个
- **模块数：** 12个主要模块
- **角色数：** 20个预定义角色
- **数据权限范围：** 4种（ALL, DEPARTMENT, OWN, CUSTOM）

### 1.2 权限编码规范

**格式：** `模块:操作`

**示例：**
- `user:create` - 创建用户
- `project:view` - 查看项目
- `material:edit` - 编辑物料

**操作类型：**
- `create` - 创建
- `view` / `list` - 查看/列表
- `edit` / `update` - 编辑/更新
- `delete` - 删除
- `approve` - 审批
- `export` - 导出
- `import` - 导入
- `manage` - 管理（综合权限）

---

## 二、模块权限清单

### 2.1 用户管理模块 (user:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| user:create | 创建用户 | 添加新用户账户 | Admin |
| user:view | 查看用户 | 查看用户详情 | Admin, Manager |
| user:list | 用户列表 | 查看用户列表 | Admin, Manager |
| user:edit | 编辑用户 | 修改用户信息 | Admin |
| user:delete | 删除用户 | 删除用户账户 | Admin |
| user:reset_password | 重置密码 | 重置用户密码 | Admin |
| user:assign_role | 分配角色 | 给用户分配角色 | Admin |
| user:export | 导出用户 | 导出用户数据 | Admin |

**权限组合建议：**
- 基础查看：`user:view` + `user:list`
- 完整管理：`user:*`（所有权限）

---

### 2.2 角色管理模块 (role:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| role:create | 创建角色 | 添加新角色 | Admin |
| role:view | 查看角色 | 查看角色详情 | Admin, Manager |
| role:list | 角色列表 | 查看角色列表 | Admin, Manager |
| role:edit | 编辑角色 | 修改角色信息 | Admin |
| role:delete | 删除角色 | 删除角色 | Admin |
| role:assign_permission | 分配权限 | 给角色分配权限 | Admin |
| role:manage_data_scope | 管理数据权限 | 配置角色数据范围 | Admin |

---

### 2.3 项目管理模块 (project:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| project:create | 创建项目 | 新建项目 | Admin, Manager |
| project:view | 查看项目 | 查看项目详情 | All |
| project:list | 项目列表 | 查看项目列表 | All |
| project:edit | 编辑项目 | 修改项目信息 | Admin, Manager, PM |
| project:delete | 删除项目 | 删除项目 | Admin |
| project:close | 关闭项目 | 关闭/归档项目 | Admin, Manager |
| project:member_manage | 成员管理 | 添加/移除项目成员 | Admin, Manager, PM |
| project:milestone_manage | 里程碑管理 | 管理项目里程碑 | Admin, Manager, PM |
| project:document_upload | 上传文档 | 上传项目文档 | Admin, Manager, PM, Member |
| project:budget_view | 查看预算 | 查看项目预算 | Admin, Manager, PM, Finance |
| project:budget_edit | 编辑预算 | 修改项目预算 | Admin, Manager, Finance |
| project:cost_view | 查看成本 | 查看项目成本 | Admin, Manager, PM, Finance |
| project:approve | 项目审批 | 审批项目申请 | Admin, Manager |

---

### 2.4 物料管理模块 (material:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| material:create | 创建物料 | 添加新物料 | Admin, MaterialManager |
| material:view | 查看物料 | 查看物料详情 | All |
| material:list | 物料列表 | 查看物料列表 | All |
| material:edit | 编辑物料 | 修改物料信息 | Admin, MaterialManager |
| material:delete | 删除物料 | 删除物料 | Admin |
| material:import | 导入物料 | 批量导入物料 | Admin, MaterialManager |
| material:export | 导出物料 | 导出物料数据 | Admin, MaterialManager |

---

### 2.5 BOM管理模块 (bom:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| bom:create | 创建BOM | 创建物料清单 | Admin, Engineer |
| bom:view | 查看BOM | 查看物料清单 | All |
| bom:edit | 编辑BOM | 修改物料清单 | Admin, Engineer |
| bom:delete | 删除BOM | 删除物料清单 | Admin |
| bom:approve | 审批BOM | 审批物料清单 | Admin, Manager |
| bom:export | 导出BOM | 导出物料清单 | Admin, Engineer |

---

### 2.6 采购管理模块 (purchase:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| purchase:create | 创建采购 | 创建采购订单 | Admin, PurchaseManager |
| purchase:view | 查看采购 | 查看采购订单 | All |
| purchase:list | 采购列表 | 查看采购列表 | All |
| purchase:edit | 编辑采购 | 修改采购订单 | Admin, PurchaseManager |
| purchase:delete | 删除采购 | 删除采购订单 | Admin |
| purchase:approve | 审批采购 | 审批采购订单 | Admin, Manager, PurchaseManager |
| purchase:receive | 到货登记 | 登记物料到货 | Admin, PurchaseManager, Warehouse |
| purchase:return | 退货处理 | 处理物料退货 | Admin, PurchaseManager |

---

### 2.7 生产管理模块 (production:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| production:plan_create | 创建计划 | 创建生产计划 | Admin, ProductionManager |
| production:plan_view | 查看计划 | 查看生产计划 | All |
| production:plan_edit | 编辑计划 | 修改生产计划 | Admin, ProductionManager |
| production:work_order_create | 创建工单 | 创建生产工单 | Admin, ProductionManager |
| production:work_order_view | 查看工单 | 查看生产工单 | All |
| production:work_order_edit | 编辑工单 | 修改生产工单 | Admin, ProductionManager, Worker |
| production:report | 生产报工 | 报告生产进度 | Worker |
| production:exception | 异常处理 | 处理生产异常 | Admin, ProductionManager |

---

### 2.8 质量管理模块 (quality:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| quality:check | 质量检验 | 执行质量检验 | Admin, QualityInspector |
| quality:view | 查看质检 | 查看质检记录 | All |
| quality:approve | 审批质检 | 审批质检结果 | Admin, QualityManager |
| quality:report | 质量报告 | 生成质量报告 | Admin, QualityManager |
| quality:exception_handle | 异常处理 | 处理质量异常 | Admin, QualityManager |

---

### 2.9 销售管理模块 (sales:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| sales:lead_create | 创建线索 | 创建销售线索 | Admin, SalesManager, Sales |
| sales:lead_view | 查看线索 | 查看销售线索 | Admin, SalesManager, Sales |
| sales:opportunity_create | 创建商机 | 创建销售商机 | Admin, SalesManager, Sales |
| sales:opportunity_view | 查看商机 | 查看销售商机 | Admin, SalesManager, Sales |
| sales:quote_create | 创建报价 | 创建报价单 | Admin, SalesManager, Sales |
| sales:quote_view | 查看报价 | 查看报价单 | Admin, SalesManager, Sales |
| sales:quote_approve | 审批报价 | 审批报价单 | Admin, SalesManager |
| sales:contract_create | 创建合同 | 创建销售合同 | Admin, SalesManager |
| sales:contract_view | 查看合同 | 查看销售合同 | Admin, SalesManager, Sales |
| sales:contract_approve | 审批合同 | 审批销售合同 | Admin, Manager |

---

### 2.10 财务管理模块 (finance:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| finance:invoice_create | 创建发票 | 创建发票 | Admin, FinanceManager |
| finance:invoice_view | 查看发票 | 查看发票 | Admin, FinanceManager, Finance |
| finance:payment_create | 创建付款 | 创建付款记录 | Admin, FinanceManager |
| finance:payment_view | 查看付款 | 查看付款记录 | Admin, FinanceManager, Finance |
| finance:receivable_view | 查看应收 | 查看应收账款 | Admin, FinanceManager, Finance |
| finance:report | 财务报表 | 查看财务报表 | Admin, FinanceManager, CEO |
| finance:approve | 财务审批 | 审批财务单据 | Admin, FinanceManager |

---

### 2.11 人力资源模块 (hr:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| hr:employee_create | 创建员工 | 添加员工档案 | Admin, HRManager |
| hr:employee_view | 查看员工 | 查看员工信息 | Admin, HRManager, Manager |
| hr:employee_edit | 编辑员工 | 修改员工信息 | Admin, HRManager |
| hr:attendance_view | 查看考勤 | 查看考勤记录 | Admin, HRManager, Manager |
| hr:salary_view | 查看薪资 | 查看薪资信息 | Admin, HRManager |
| hr:contract_manage | 合同管理 | 管理劳动合同 | Admin, HRManager |
| hr:performance_manage | 绩效管理 | 管理绩效考核 | Admin, HRManager, Manager |

---

### 2.12 系统管理模块 (system:*)

| 权限编码 | 权限名称 | 说明 | 适用角色 |
|---------|---------|------|---------|
| system:config | 系统配置 | 修改系统配置 | Admin |
| system:log_view | 查看日志 | 查看系统日志 | Admin |
| system:audit_view | 查看审计 | 查看审计日志 | Admin |
| system:backup | 数据备份 | 执行数据备份 | Admin |
| system:restore | 数据恢复 | 恢复数据 | Admin |
| system:monitor | 系统监控 | 查看系统监控 | Admin |

---

## 三、角色权限矩阵

### 3.1 管理员角色

#### SuperAdmin / Admin
**数据权限范围：** ALL（全局）

| 模块 | 权限 | 说明 |
|------|------|------|
| 所有模块 | ALL | 拥有所有权限（125个） |

#### SystemAdmin
**数据权限范围：** ALL（全局）

| 模块 | 权限 | 说明 |
|------|------|------|
| 用户管理 | ALL | 完整的用户管理权限 |
| 角色管理 | ALL | 完整的角色管理权限 |
| 系统管理 | ALL | 完整的系统管理权限 |
| 其他模块 | VIEW | 仅查看权限 |

---

### 3.2 业务管理角色

#### Manager（部门经理）
**数据权限范围：** DEPARTMENT（本部门）

| 模块 | 权限列表 |
|------|---------|
| 用户管理 | view, list |
| 角色管理 | view, list |
| 项目管理 | create, view, list, edit, approve, member_manage, milestone_manage |
| 物料管理 | view, list |
| 采购管理 | view, list, approve |
| 生产管理 | view, list, approve |
| 质量管理 | view, approve |
| 销售管理 | view, approve |
| 财务管理 | view |
| 人力资源 | employee_view, attendance_view, performance_manage |

#### ProjectManager（项目经理）
**数据权限范围：** 所管理的项目

| 模块 | 权限列表 |
|------|---------|
| 项目管理 | create, view, list, edit, member_manage, milestone_manage, document_upload, budget_view, cost_view |
| 物料管理 | view, list |
| 采购管理 | view, list |
| 生产管理 | plan_view, work_order_view |
| 质量管理 | view |

#### PurchaseManager（采购经理）
**数据权限范围：** DEPARTMENT

| 模块 | 权限列表 |
|------|---------|
| 物料管理 | create, view, list, edit, import, export |
| 采购管理 | ALL |
| 供应商管理 | ALL |

#### ProductionManager（生产经理）
**数据权限范围：** DEPARTMENT

| 模块 | 权限列表 |
|------|---------|
| 生产管理 | ALL |
| 物料管理 | view, list |
| 质量管理 | view |
| 设备管理 | view, list |

#### QualityManager（质量经理）
**数据权限范围：** DEPARTMENT

| 模块 | 权限列表 |
|------|---------|
| 质量管理 | ALL |
| 生产管理 | view, list |
| 物料管理 | view, list |

---

### 3.3 普通员工角色

#### Employee（普通员工）
**数据权限范围：** OWN（个人）

| 模块 | 权限列表 |
|------|---------|
| 项目管理 | view, list, document_upload（仅参与的项目） |
| 工时管理 | create, view, list, edit（自己的工时） |
| 任务管理 | view, list, edit（自己的任务） |

#### Sales（销售人员）
**数据权限范围：** OWN + 客户范围

| 模块 | 权限列表 |
|------|---------|
| 销售管理 | lead_create, lead_view, opportunity_create, opportunity_view, quote_create, quote_view, contract_view |
| 客户管理 | create, view, list, edit |
| 项目管理 | view, list |

#### Engineer（工程师）
**数据权限范围：** 所参与的项目

| 模块 | 权限列表 |
|------|---------|
| 项目管理 | view, list, document_upload |
| BOM管理 | create, view, edit, export |
| 物料管理 | view, list |
| 生产管理 | view, list |

#### Worker（生产工人）
**数据权限范围：** 所分配的工单

| 模块 | 权限列表 |
|------|---------|
| 生产管理 | work_order_view, report |
| 质量管理 | check |
| 物料管理 | view（仅工单相关） |

---

## 四、数据权限范围详解

### 4.1 ALL - 全局访问权限
- **适用角色：** SuperAdmin, Admin, SystemAdmin
- **访问范围：** 所有数据，包括所有租户（如果是多租户系统）
- **典型场景：** 系统管理员、超级管理员

### 4.2 DEPARTMENT - 部门级权限
- **适用角色：** Manager, PurchaseManager, ProductionManager
- **访问范围：** 本部门及下属部门的数据
- **过滤规则：**
  ```sql
  WHERE department_id IN (
    SELECT id FROM departments 
    WHERE parent_path LIKE CONCAT(current_user_department, '%')
  )
  ```

### 4.3 OWN - 个人数据权限
- **适用角色：** Employee, Sales（部分数据）
- **访问范围：** 仅个人创建或分配的数据
- **过滤规则：**
  ```sql
  WHERE created_by = current_user_id
  OR assigned_to = current_user_id
  ```

### 4.4 CUSTOM - 自定义权限范围
- **适用角色：** 根据业务需求配置
- **访问范围：** 通过数据权限规则表配置
- **典型场景：**
  - 跨部门项目团队
  - 特殊权限分配
  - 临时权限授予

**配置示例：**
```json
{
  "user_id": 123,
  "data_scope_rules": [
    {
      "rule_type": "INCLUDE",
      "target_type": "DEPARTMENT",
      "target_ids": [10, 20, 30]
    },
    {
      "rule_type": "INCLUDE",
      "target_type": "PROJECT",
      "target_ids": [100, 200]
    },
    {
      "rule_type": "EXCLUDE",
      "target_type": "PROJECT",
      "target_ids": [150]
    }
  ]
}
```

---

## 五、权限检查流程

### 5.1 请求处理流程
```
用户请求
    ↓
认证中间件（验证Token）
    ↓
权限检查（检查功能权限）
    ↓
数据范围过滤（应用数据权限）
    ↓
业务逻辑处理
    ↓
返回结果
```

### 5.2 权限检查伪代码
```python
def check_permission(user: User, permission: str) -> bool:
    # 1. 超级管理员跳过检查
    if user.is_superuser and user.tenant_id is None:
        return True
    
    # 2. 获取用户角色
    roles = get_user_roles(user.id)
    
    # 3. 检查角色是否拥有该权限
    for role in roles:
        if permission in role.permissions:
            return True
    
    return False

def apply_data_scope(query: Query, user: User, model: Model):
    # 1. 获取用户的数据权限范围
    data_scope = get_user_data_scope(user)
    
    # 2. 根据范围类型应用过滤
    if data_scope == "ALL":
        return query  # 不过滤
    elif data_scope == "DEPARTMENT":
        return query.filter(model.department_id.in_(user_departments))
    elif data_scope == "OWN":
        return query.filter(
            or_(
                model.created_by == user.id,
                model.assigned_to == user.id
            )
        )
    elif data_scope == "CUSTOM":
        return apply_custom_rules(query, user, model)
```

---

## 六、权限管理最佳实践

### 6.1 权限分配原则
1. **最小权限原则：** 仅授予完成工作所需的最小权限
2. **职责分离：** 关键操作需要多人协作（如审批）
3. **定期审查：** 定期审查权限分配，回收不必要的权限
4. **权限继承：** 利用角色继承减少重复配置

### 6.2 安全建议
1. **避免直接分配权限给用户：** 通过角色分配权限
2. **记录权限变更：** 所有权限变更都应有审计日志
3. **临时权限管理：** 临时权限应设置过期时间
4. **敏感权限二次确认：** 删除、导出等敏感操作需要二次确认

### 6.3 性能优化
1. **权限缓存：** 将用户权限缓存15分钟
2. **批量检查：** 一次性获取用户所有权限，避免多次查询
3. **索引优化：** 在权限表上建立合适的索引
4. **懒加载：** 仅在需要时才进行数据权限过滤

---

## 七、常见问题和解决方案

### Q1: 如何处理跨部门项目的权限？
**A:** 使用CUSTOM数据权限范围，配置项目成员的访问规则。

### Q2: 新员工应该分配什么权限？
**A:** 分配Employee角色，根据具体岗位添加对应的专业角色（Sales, Engineer等）。

### Q3: 如何实现"代理审批"功能？
**A:** 创建临时权限规则，设置代理期间和代理权限范围。

### Q4: 如何撤销已授予的权限？
**A:** 
1. 从用户-角色关联表中删除记录
2. 清除权限缓存
3. 记录审计日志

---

## 八、附录

### A. 快速参考表

**超级管理员（SuperAdmin）：** 125个权限（ALL）  
**管理员（Admin）：** 125个权限（ALL）  
**部门经理（Manager）：** ~80个权限（DEPARTMENT）  
**项目经理（ProjectManager）：** ~40个权限（PROJECT）  
**普通员工（Employee）：** ~15个权限（OWN）

### B. 权限代码示例

```python
# 检查用户是否有权限
from app.core.security import check_permission

if check_permission(current_user, "project:edit"):
    # 执行编辑操作
    pass

# 使用装饰器
from app.core.security import require_permission

@require_permission("project:delete")
def delete_project(project_id: int):
    # 删除项目
    pass

# 应用数据权限过滤
from app.core.permissions import apply_data_scope

query = db.query(Project)
query = apply_data_scope(query, current_user, Project)
projects = query.all()
```

---

**文档维护：** Team 3  
**最后更新：** 2026-02-16  
**版本：** v1.0
