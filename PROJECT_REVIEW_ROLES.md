# 项目复盘模块角色权限说明

## 可见角色

根据项目复盘的业务特性（项目结项后的复盘总结、经验沉淀），以下角色可以访问项目复盘模块：

### 1. 管理层角色 ✅
- **董事长** (chairman) - 查看所有项目的复盘报告
- **总经理** (gm) - 查看所有项目的复盘报告
- **部门经理** (dept_manager) - 查看本部门项目的复盘报告
- **项目部门经理** (project_dept_manager) - 查看所有项目的复盘报告

### 2. 项目管理角色 ✅
- **项目经理** (pm) - 查看和创建所负责项目的复盘报告
- **技术负责人** (te) - 查看和参与相关项目的复盘报告

### 3. 系统管理角色 ✅
- **系统管理员** (admin) - 查看所有项目的复盘报告
- **超级管理员** (super_admin) - 查看所有项目的复盘报告

### 4. 其他相关角色 ✅
- **PMC计划员** (pmc) - 查看所有项目的复盘报告（用于生产计划参考）
- **品质工程师** (qa) - 查看所有项目的复盘报告（用于质量改进）

## 权限级别

### 查看权限（只读）
所有上述角色都可以：
- 查看复盘报告列表
- 查看复盘报告详情
- 查看经验教训
- 查看最佳实践

### 创建/编辑权限
以下角色可以创建和编辑复盘报告：
- 项目经理 (pm) - 只能创建/编辑自己负责的项目
- 项目部门经理 (project_dept_manager) - 可以创建/编辑所有项目
- 系统管理员 (admin, super_admin) - 可以创建/编辑所有项目

### 发布/归档权限
以下角色可以发布和归档复盘报告：
- 项目部门经理 (project_dept_manager)
- 系统管理员 (admin, super_admin)
- 总经理 (gm)
- 董事长 (chairman)

## 实现建议

### 1. 在导航菜单中添加项目复盘入口

在 `frontend/src/components/layout/Sidebar.jsx` 的 PMO 模块中添加：

```javascript
{
  label: 'PMO 项目管理部',
  items: [
    // ... 现有菜单项
    { name: '项目结项', path: '/pmo/closure', icon: 'CheckCircle2' },
    { name: '项目复盘', path: '/projects/reviews', icon: 'FileText' }, // 新增
    // ... 其他菜单项
  ],
}
```

### 2. 添加权限检查函数

在 `frontend/src/lib/roleConfig.js` 中添加：

```javascript
// 检查角色是否有项目复盘模块的访问权限
export function hasProjectReviewAccess(roleCode, isSuperuser = false) {
  if (isSuperuser) return true
  
  const reviewRoles = [
    'chairman', '董事长',
    'gm', '总经理',
    'admin', 'super_admin', '系统管理员', '管理员',
    'dept_manager', '部门经理',
    'project_dept_manager', '项目部门经理',
    'pm', '项目经理',
    'te', '技术负责人',
    'pmc', 'PMC计划员',
    'qa', '品质工程师',
  ]
  return reviewRoles.includes(roleCode)
}
```

### 3. 创建权限保护组件

在 `frontend/src/components/common/ProtectedRoute.jsx` 中添加：

```javascript
export function ProjectReviewProtectedRoute({ children }) {
  const userStr = localStorage.getItem('user')
  let isSuperuser = false
  if (userStr) {
    try {
      const user = JSON.parse(userStr)
      isSuperuser = user.is_superuser === true || user.isSuperuser === true
    } catch {
      // ignore
    }
  }
  
  return (
    <ProtectedRoute
      checkPermission={(role) => hasProjectReviewAccess(role, isSuperuser)}
      permissionName="项目复盘模块"
    >
      {children}
    </ProtectedRoute>
  )
}
```

### 4. 在路由中应用权限保护

在 `frontend/src/App.jsx` 中：

```javascript
import { ProjectReviewProtectedRoute } from './components/common/ProtectedRoute'

// 在路由中使用
<Route path="/projects/reviews" element={
  <ProjectReviewProtectedRoute>
    <ProjectReviewList />
  </ProjectReviewProtectedRoute>
} />
<Route path="/projects/reviews/:reviewId" element={
  <ProjectReviewProtectedRoute>
    <ProjectReviewDetail />
  </ProjectReviewProtectedRoute>
} />
```

## 数据权限范围

根据角色的 `dataScope` 配置：

- **all** (董事长、总经理、管理员、PMC、QA) - 可以查看所有项目的复盘报告
- **department** (部门经理) - 可以查看本部门项目的复盘报告
- **project** (项目经理、技术负责人) - 可以查看自己参与的项目复盘报告

## 总结

项目复盘模块主要面向：
1. **管理层** - 用于战略决策和经验总结
2. **项目管理层** - 用于项目管理和经验沉淀
3. **质量管理人员** - 用于质量改进

建议采用与项目结项管理类似的权限控制策略。


