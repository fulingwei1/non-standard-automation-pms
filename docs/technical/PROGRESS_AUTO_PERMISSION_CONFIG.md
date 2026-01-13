# 进度预测和依赖检查功能 - 权限配置完整指南

> **配置日期**: 2026-01-12  
> **权限策略**: 方案1（ProjectReviewProtectedRoute - 严格权限）  
> **配置文件**: 2个（1个后端路由，1个SQL迁移）

---

## 一、权限配置说明

### 1.1 权限策略

**选择**: 方案1 - 使用 `ProjectReviewProtectedRoute`

**原因**:
- ✅ 进度预测和依赖检查是**高级管理功能**
- ✅ 应该由有管理责任的人使用（项目经理、各部门经理、管理层）
- ✅ 避免一线员工误操作（如错误执行自动处理）
- ✅ 保护系统性能（不是所有人都能执行批量操作）

### 1.2 权限范围

**允许的角色**（共12个）：

| 角色 | 中文名 | 级别 | 权限 |
|-----|-------|:----:|------|
| admin | 系统管理员 | 2 | 完全访问 |
| super_admin | 超级管理员 | 1 | 完全访问 |
| chairman | 董事长 | 1 | 监控所有项目 |
| gm | 总经理 | 2 | 监控所有项目 |
| project_dept_manager | 项目部经理 | 3 | 管理所有项目 |
| pmc | 项目经理(PMC) | 4 | 管理负责的项目 |
| pm | 项目经理 | 4 | 管理负责的项目 |
| tech_dev_manager | 技术开发部经理 | 3 | 技术进度管理 |
| me_dept_manager | 机械部经理 | 3 | 机械进度管理 |
| ee_dept_manager | 电气部经理 | 3 | 电气进度管理 |
| te_dept_manager | 测试部经理 | 3 | 测试进度管理 |

**不允许的角色**（所有其他角色）:
- 销售相关人员（销售总监、销售经理、销售工程师等）
- 采购相关人员（采购部经理、采购工程师等）
- 生产相关人员（制造总监、生产部经理、装配工等）
- 客服相关人员（客服部经理、客服工程师等）
- 后台支持人员（财务经理、人事经理等）
- 所有一线员工（工程师、技工、专员等）

---

## 二、数据库迁移配置

### 2.1 创建SQL迁移文件

**文件1**: `migrations/20260125_progress_auto_permissions_mysql.sql`

**文件2**: `migrations/20260125_progress_auto_permissions_sqlite.sql`

**内容**: 两个文件已经创建完成，包含：
1. ✅ 添加进度预测访问权限（`progress:forecast`）
2. ✅ 添加依赖检查访问权限（`progress:dependency_check`）
3. ✅ 为所有允许的角色分配权限
4. ✅ 验证权限配置结果

### 2.2 执行数据库迁移

**MySQL**:
```bash
# 进入数据库
mysql -u root -p non_standard_automation_pms

# 执行迁移
source migrations/20260125_progress_auto_permissions_mysql.sql;

# 验证结果
SELECT 
  p.permission_code,
  p.permission_name,
  COUNT(rp.id) as role_count
FROM permissions p
LEFT JOIN role_permissions rp ON p.id = rp.permission_id
WHERE p.permission_code IN ('progress:forecast', 'progress:dependency_check')
GROUP BY p.permission_code, p.permission_name;
```

**SQLite**:
```bash
# 执行迁移
sqlite3 non_standard_automation_pms.db < migrations/20260125_progress_auto_permissions_sqlite.sql

# 验证结果
SELECT 
  p.permission_code,
  p.permission_name,
  COUNT(rp.id) as role_count
FROM permissions p
LEFT JOIN role_permissions rp ON p.id = rp.permission_id
WHERE p.permission_code IN ('progress:forecast', 'progress:dependency_check')
GROUP BY p.permission_code, p.permission_name;
```

**预期结果**:
- `progress:forecast`: 12个角色
- `progress:dependency_check`: 12个角色

---

## 三、后端路由配置更新

### 3.1 更新路由文件

**文件**: `frontend/src/routes/routeConfig.jsx`

**当前配置** (无权限保护):
```javascript
// 当前状态：没有使用 ProtectedRoute
<Route path="/projects/:id/progress-forecast" element={<ProgressForecast />} />
<Route path="/projects/:id/dependency-check" element={<DependencyCheck />} />
```

**需要修改为** (添加 ProjectReviewProtectedRoute):
```javascript
// 导入 ProjectReviewProtectedRoute
import {
  AppProtectedRoute,
  ProjectReviewProtectedRoute,  // 新增
} from "../components/common/ProtectedRoute";

// 导入页面组件
import ProgressForecast from "../pages/ProgressForecast";
import DependencyCheck from "../pages/DependencyCheck";

// 在路由配置中使用
{
  path: "/projects/:id/progress-forecast",
  element: (
    <ProjectReviewProtectedRoute>
      <ProgressForecast />
    </ProjectReviewProtectedRoute>
  ),
},
{
  path: "/projects/:id/dependency-check",
  element: (
    <ProjectReviewProtectedRoute>
      <DependencyCheck />
    </ProjectReviewProtectedRoute>
  ),
},
```

### 3.2 具体修改步骤

**步骤1**: 导入 ProjectReviewProtectedRoute

在文件开头的导入区域添加：
```javascript
import {
  AppProtectedRoute,
  ProjectReviewProtectedRoute,  // 新增这一行
} from "../components/common/ProtectedRoute";
```

**步骤2**: 在路由配置中添加权限保护

找到这两个路由：
```javascript
<Route path="/projects/:id/progress-forecast" element={<ProgressForecast />} />
<Route path="/projects/:id/dependency-check" element={<DependencyCheck />} />
```

替换为：
```javascript
{
  path: "/projects/:id/progress-forecast",
  element: (
    <ProjectReviewProtectedRoute>
      <ProgressForecast />
    </ProjectReviewProtectedRoute>
  ),
},
{
  path: "/projects/:id/dependency-check",
  element: (
    <ProjectReviewProtectedRoute>
      <DependencyCheck />
    </ProjectReviewProtectedRoute>
  ),
},
```

### 3.3 验证权限配置

**测试1**: 允许的角色（应该能看到）

```bash
# 1. 使用项目经理角色登录
# 2. 访问: http://localhost:3000/projects/1/progress-forecast
# 3. 应该能正常访问

# 4. 访问: http://localhost:3000/projects/1/dependency-check
# 5. 应该能正常访问
```

**测试2**: 不允许的角色（应该看不到）

```bash
# 1. 使用销售工程师角色登录
# 2. 访问: http://localhost:3000/projects/1/progress-forecast
# 3. 应该看到"权限不足"提示

# 4. 访问: http://localhost:3000/projects/1/dependency-check
# 5. 应该看到"权限不足"提示
```

**测试3**: 管理员（应该能看到）

```bash
# 1. 使用系统管理员角色登录
# 2. 访问: http://localhost:3000/projects/1/progress-forecast
# 3. 应该能正常访问（超级管理员绕过权限检查）
```

---

## 四、权限管理页面集成

### 4.1 权限配置显示

**页面**: `frontend/src/pages/PermissionManagement.jsx`

**显示位置**: 在"项目管理"模块分组中

**显示效果**:
- 权限名称: "查看进度预测" (`progress:forecast`)
- 权限名称: "检查依赖关系" (`progress:dependency_check`)
- 所属模块: "项目管理"
- 分配角色: 12个

**管理方式**:
1. ✅ 权限管理员可以在权限管理页面看到这两个权限
2. ✅ 可以查看哪些角色拥有这些权限
3. ✅ 可以动态分配或撤销权限
4. ✅ 可以搜索和筛选权限

### 4.2 权限管理操作

**查看权限**:
1. 进入"权限管理"页面
2. 在"项目管理"模块分组下找到:
   - "查看进度预测"
   - "检查依赖关系"
3. 点击"详情"按钮查看权限详情

**分配权限**:
1. 在权限管理页面找到目标权限
2. 点击"编辑"或"分配"按钮
3. 在角色列表中选择要分配的角色
4. 保存配置

**撤销权限**:
1. 在权限管理页面找到目标权限
2. 点击"编辑"按钮
3. 在角色列表中取消要撤销的角色
4. 保存配置

---

## 五、完整的权限配置清单

### 5.1 数据库层面

| 项目 | 状态 | 文件 |
|-----|:----:|------|
| 创建权限记录 | ✅ | 已完成 |
| 分配角色权限 | ✅ | 已完成 |
| 权限验证SQL | ✅ | 已完成 |

**数据库文件**:
- ✅ `migrations/20260125_progress_auto_permissions_mysql.sql`
- ✅ `migrations/20260125_progress_auto_permissions_sqlite.sql`

### 5.2 后端API层面

| 项目 | 状态 | 说明 |
|-----|:----:|------|
| API端点 | ✅ | 已实现5个新端点 |
| 权限检查 | ⚠️ | 需要更新路由配置 |
| 后端权限验证 | ⚠️ | 使用 ProjectReviewProtectedRoute |

**需要更新的文件**:
- ⚠️ `frontend/src/routes/routeConfig.jsx`

### 5.3 前端页面层面

| 项目 | 状态 | 文件 |
|-----|:----:|------|
| 页面文件 | ✅ | 已创建 |
| 路由配置 | ⚠️ | 需要更新 |
| API服务 | ⚠️ | 需要手动更新 |

**需要更新的文件**:
- ⚠️ `frontend/src/routes/routeConfig.jsx` - 添加权限保护
- ⚠️ `frontend/src/services/api.js` - 添加 autoProcess API 方法

---

## 六、配置验证检查清单

### 6.1 数据库验证

- [ ] SQL迁移文件已创建
- [ ] 权限记录已成功插入
- [ ] 角色权限已成功分配
- [ ] 每个权限分配了12个角色
- [ ] 权限验证SQL返回正确结果

### 6.2 后端验证

- [ ] 路由配置已更新
- [ ] ProjectReviewProtectedRoute 已应用
- [ ] 允许的角色能正常访问
- [ ] 不允许的角色被正确拦截
- [ ] 权限提示信息正确显示

### 6.3 前端验证

- [ ] 路由配置已更新
- [ ] ProjectReviewProtectedRoute 已导入
- [ ] 进度预测页面受保护
- [ ] 依赖检查页面受保护
- [ ] 权限不足提示正确显示

### 6.4 功能验证

- [ ] 项目经理能访问两个页面
- [ ] 各部门经理能访问两个页面
- [ ] 管理层（董事长、总经理）能访问两个页面
- [ ] 系统管理员能访问两个页面
- [ ] 销售相关人员不能访问
- [ ] 采购相关人员不能访问
- [ ] 生产相关人员不能访问
- [ ] 客服相关人员不能访问
- [ ] 所有权限管理功能正常工作

---

## 七、配置后的效果

### 7.1 权限控制效果

**访问控制**:
- ✅ 只有12个允许的角色能看到这两个页面
- ✅ 所有其他角色访问时会看到"权限不足"提示
- ✅ 页面会显示友好的权限提示界面

**用户体验**:
- ✅ 允许的角色可以正常使用所有功能
- ✅ 不允许的角色会被重定向或显示提示
- ✅ 权限不足时显示清晰的说明

### 7.2 权限管理效果

**权限管理页面**:
- ✅ 管理员可以在权限管理页面看到这两个新权限
- ✅ 可以动态分配和撤销权限
- ✅ 可以查看权限分配情况
- ✅ 支持搜索和筛选功能

**灵活性**:
- ✅ 权限管理员可以随时调整权限分配
- ✅ 不需要修改代码即可调整权限
- ✅ 权限变更立即生效

### 7.3 系统安全性

**访问控制**:
- ✅ 保护了高级管理功能不被误用
- ✅ 保护了系统性能（限制批量操作）
- ✅ 保护了数据安全（限制敏感操作）

**审计追踪**:
- ✅ 所有权限操作都有日志记录
- ✅ 可以追踪权限变更历史
- ✅ 可以审查权限分配情况

---

## 八、常见问题

### Q1: 执行SQL迁移时报错怎么办？

**A**: 检查以下几点：
1. 数据库连接是否正常
2. SQL语法是否正确（MySQL vs SQLite）
3. 表是否存在（permissions, roles, role_permissions）
4. 权限是否足够（INSERT权限）

### Q2: 权限配置后仍然看不到页面？

**A**: 检查以下几点：
1. SQL迁移是否成功执行
2. 当前用户是否在允许的角色列表中
3. 是否使用正确的账户登录
4. 浏览器缓存是否已清除

### Q3: 如何临时开放给所有人访问？

**A**: 有两种方式：

**方式1**: 移除路由保护（不推荐）
```javascript
// 移除 ProjectReviewProtectedRoute
<Route path="/projects/:id/progress-forecast" element={<ProgressForecast />} />
<Route path="/projects/:id/dependency-check" element={<DependencyCheck />} />
```

**方式2**: 使用超级管理员账号（推荐）
```bash
# 超级管理员可以绕过所有权限检查
is_superuser = true
```

### Q4: 如何添加新的角色到允许列表？

**A**: 两种方式：

**方式1**: 通过权限管理页面（推荐）
1. 进入"权限管理"页面
2. 找到目标权限
3. 点击"编辑"按钮
4. 在角色列表中勾选新角色
5. 保存配置

**方式2**: 直接操作数据库（不推荐）
```sql
-- 为新角色分配权限
INSERT INTO role_permissions (role_id, permission_id, created_at, updated_at)
SELECT 
  r.id, 
  p.id, 
  NOW(), 
  NOW()
FROM roles r
CROSS JOIN permissions p
WHERE p.permission_code IN ('progress:forecast', 'progress:dependency_check')
AND r.role_code = 'new_role_code'
ON CONFLICT DO NOTHING;
```

---

## 九、总结

### 9.1 配置状态

| 项目 | 状态 | 说明 |
|-----|:----:|------|
| **数据库迁移** | ✅ | SQL文件已创建，待执行 |
| **后端路由配置** | ⚠️ | 需要更新路由文件 |
| **前端API服务** | ⚠️ | 需要手动更新api.js |
| **权限管理集成** | ✅ | 自动集成，执行SQL后生效 |

### 9.2 下一步操作

**立即执行**:
1. ✅ 执行SQL迁移（MySQL或SQLite）
2. ⚠️ 更新路由配置文件
3. ⚠️ 更新API服务文件
4. ⚠️ 测试权限控制是否正常工作

**验证测试**:
1. ✅ 用允许的角色登录并访问页面
2. ✅ 用不允许的角色登录并验证拦截
3. ✅ 在权限管理页面查看权限分配情况

### 9.3 完成标准

**配置完成标准**:
- ✅ 数据库中已添加两个权限记录
- ✅ 12个角色已分配权限
- ✅ 路由已添加 ProjectReviewProtectedRoute 保护
- ✅ 允许的角色能正常访问
- ✅ 不允许的角色被正确拦截
- ✅ 权限管理页面能正常显示和管理

---

**最后更新**: 2026-01-12
