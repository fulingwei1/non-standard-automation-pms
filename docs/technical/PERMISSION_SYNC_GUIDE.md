# 权限配置同步指南

> **重要**：当前端和后端的权限配置不一致时，会导致用户无法访问某些功能。

---

## 一、权限配置位置

### 前端权限配置
**文件**: `frontend/src/lib/roleConfig.js`

**函数**:
- `hasFinanceAccess(role, isSuperuser)` - 财务模块权限
- `hasProcurementAccess(role, isSuperuser)` - 采购模块权限
- `hasProductionAccess(role, isSuperuser)` - 生产模块权限
- `hasProjectReviewAccess(role, isSuperuser)` - 项目评审权限

### 后端权限配置
**文件**: `app/core/security.py`

**函数**:
- `has_finance_access(user: User)` - 财务模块权限
- `has_procurement_access(user: User)` - 采购模块权限
- `has_production_access(user: User)` - 生产模块权限
- `has_project_review_access(user: User)` - 项目评审权限

---

## 二、同步规则

### 规则1：角色列表必须一致

**前端配置示例**:
```javascript
export function hasFinanceAccess(role, isSuperuser = false) {
  if (isSuperuser) return true;
  const allowedRoles = [
    'admin', 'super_admin', 'chairman', 'gm',
    'finance_manager', 'business_support',
    // ... 其他角色
  ];
  return allowedRoles.includes(role);
}
```

**后端配置示例**:
```python
def has_finance_access(user: User) -> bool:
    if user.is_superuser:
        return True
    finance_roles = [
        'admin', 'super_admin', 'chairman', 'gm',
        'finance_manager', 'business_support',
        # ... 其他角色（必须与前端一致）
    ]
    # ... 检查逻辑
```

### 规则2：同时支持英文和中文角色名

后端需要同时检查：
- `role_code`（英文角色代码，如 `business_support`）
- `role_name`（中文角色名，如 `商务支持`）

### 规则3：添加注释说明

在函数开头添加注释，说明需要与前端保持同步：
```python
def has_finance_access(user: User) -> bool:
    """
    检查用户是否有财务管理模块的访问权限
    
    注意：此配置需要与前端 frontend/src/lib/roleConfig.js 中的 
    hasFinanceAccess() 保持同步。当修改前端权限时，请同步更新此函数。
    """
```

---

## 三、同步检查清单

修改权限配置时，请确认：

- [ ] 前端 `roleConfig.js` 中的角色列表已更新
- [ ] 后端 `security.py` 中的角色列表已更新
- [ ] 后端同时检查了 `role_code` 和 `role_name`
- [ ] 添加了同步说明注释
- [ ] 测试了相关角色的访问权限

---

## 四、当前权限配置状态

### 财务模块权限（hasFinanceAccess / has_finance_access）

**已同步角色**（2026-01-XX）:
- ✅ 管理层：admin, super_admin, chairman, gm
- ✅ 财务部门：finance_manager, finance, accountant
- ✅ 销售部门：sales_director, sales_manager, sales, business_support, presales_manager, presales
- ✅ 项目管理部门：project_dept_manager, pmc, pm

**同步状态**: ✅ 已同步

---

## 五、常见问题

### Q1: 为什么修改了前端权限，用户还是无法访问？

**A**: 检查后端权限配置是否已同步更新。前端只控制菜单显示，后端控制API访问。

### Q2: 如何快速检查权限是否同步？

**A**: 对比以下文件中的角色列表：
- `frontend/src/lib/roleConfig.js` → `hasFinanceAccess()`
- `app/core/security.py` → `has_finance_access()`

### Q3: 角色代码大小写不一致怎么办？

**A**: 后端使用 `.lower()` 统一转换为小写进行比较，前端也需要保持一致。

---

## 六、自动化同步方案（未来）

### 方案1：共享配置文件

创建一个共享的权限配置文件（如 `permissions.json`），前后端都从此文件读取：

```json
{
  "finance": {
    "roles": [
      "admin", "super_admin", "chairman", "gm",
      "finance_manager", "business_support"
    ]
  }
}
```

### 方案2：后端API提供权限配置

前端通过API获取权限配置，确保始终与后端一致：

```javascript
// 前端
const financeRoles = await api.get('/system/permissions/finance')
```

### 方案3：构建时验证

在构建脚本中添加检查，确保前后端权限配置一致：

```bash
# scripts/check-permissions.sh
python scripts/validate_permissions.py
```

---

## 七、修改权限配置的标准流程

1. **确定需求**：明确哪些角色需要访问哪些模块
2. **更新前端**：修改 `frontend/src/lib/roleConfig.js`
3. **更新后端**：修改 `app/core/security.py`
4. **添加注释**：在函数中添加同步说明
5. **测试验证**：使用相关角色登录测试
6. **更新文档**：更新此文档的"当前权限配置状态"部分

---

**最后更新**: 2026-01-XX  
**维护者**: 开发团队
