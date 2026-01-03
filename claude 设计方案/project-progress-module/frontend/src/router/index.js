import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '工作台' }
  },
  {
    path: '/projects',
    name: 'ProjectList',
    component: () => import('@/views/ProjectList.vue'),
    meta: { title: '项目列表' }
  },
  {
    path: '/project/:id',
    name: 'ProjectDetail',
    component: () => import('@/views/ProjectDashboard.vue'),
    props: route => ({ projectId: parseInt(route.params.id) }),
    meta: { title: '项目看板' }
  },
  {
    path: '/project/:id/gantt',
    name: 'ProjectGantt',
    component: () => import('@/views/ProjectGantt.vue'),
    props: route => ({ projectId: parseInt(route.params.id) }),
    meta: { title: '甘特图' }
  },
  {
    path: '/project/:id/wbs',
    name: 'ProjectWbs',
    component: () => import('@/views/ProjectWbs.vue'),
    props: route => ({ projectId: parseInt(route.params.id) }),
    meta: { title: 'WBS任务' }
  },
  {
    path: '/project/:id/tasks',
    name: 'ProjectTasks',
    component: () => import('@/views/ProjectTasks.vue'),
    props: route => ({ projectId: parseInt(route.params.id) }),
    meta: { title: '任务列表' }
  },
  {
    path: '/project/:id/alerts',
    name: 'ProjectAlerts',
    component: () => import('@/views/ProjectAlerts.vue'),
    props: route => ({ projectId: parseInt(route.params.id) }),
    meta: { title: '预警管理' }
  },
  {
    path: '/my-tasks',
    name: 'MyTasks',
    component: () => import('@/views/MyTasks.vue'),
    meta: { title: '我的任务' }
  },
  {
    path: '/task-center',
    name: 'TaskCenter',
    component: () => import('@/views/TaskCenter.vue'),
    meta: { title: '任务中心' }
  },
  {
    path: '/kanban',
    name: 'KanbanView',
    component: () => import('@/views/KanbanView.vue'),
    meta: { title: '任务看板' }
  },
  {
    path: '/presale/tickets',
    name: 'PresaleTickets',
    component: () => import('@/views/PresaleTickets.vue'),
    meta: { title: '售前支持工单' }
  },
  {
    path: '/pmo/dashboard',
    name: 'PmoDashboard',
    component: () => import('@/views/PmoDashboard.vue'),
    meta: { title: '项目管理驾驶舱' }
  },
  {
    path: '/production/dashboard',
    name: 'ProductionDashboard',
    component: () => import('@/views/ProductionDashboard.vue'),
    meta: { title: '生产管理驾驶舱' }
  },
  {
    path: '/timesheet',
    name: 'Timesheet',
    component: () => import('@/views/TimesheetPage.vue'),
    meta: { title: '工时填报' }
  },
  {
    path: '/workload',
    name: 'Workload',
    component: () => import('@/views/WorkloadPage.vue'),
    meta: { title: '负荷管理' }
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/AlertsPage.vue'),
    meta: { title: '预警中心' }
  },
  {
    path: '/performance',
    name: 'Performance',
    component: () => import('@/views/PerformancePage.vue'),
    meta: { title: '绩效中心' }
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/ReportsPage.vue'),
    meta: { title: '报表中心' }
  },
  // 数据导入
  {
    path: '/import',
    name: 'DataImport',
    component: () => import('@/views/DataImportPage.vue'),
    meta: { title: '数据导入', permission: 'system:import' }
  },
  // 系统管理模块
  {
    path: '/system/users',
    name: 'UserManage',
    component: () => import('@/views/system/UserManage.vue'),
    meta: { title: '用户管理', permission: 'system:user:view' }
  },
  {
    path: '/system/roles',
    name: 'RoleManage',
    component: () => import('@/views/system/RoleManage.vue'),
    meta: { title: '角色管理', permission: 'system:role:view' }
  },
  {
    path: '/system/menus',
    name: 'MenuManage',
    component: () => import('@/views/system/MenuManage.vue'),
    meta: { title: '菜单管理', permission: 'system:menu:view' }
  },
  {
    path: '/system/depts',
    name: 'DeptManage',
    component: () => import('@/views/system/DeptManage.vue'),
    meta: { title: '部门管理', permission: 'system:dept:view' }
  },
  {
    path: '/system/logs',
    name: 'OperationLog',
    component: () => import('@/views/system/OperationLog.vue'),
    meta: { title: '操作日志', permission: 'system:log:view' }
  },
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在', public: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 项目进度管理系统` : '项目进度管理系统'
  
  // 公开页面直接放行
  if (to.meta.public) {
    next()
    return
  }
  
  // 检查登录状态
  const token = localStorage.getItem('token')
  if (!token) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }
  
  next()
})

export default router
