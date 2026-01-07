import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getProjectList, getMyTasks as fetchMyTasks, getAlerts } from '@/api/task'
import { login as loginApi, logout as logoutApi, getUserInfo } from '@/api/auth'

// 用户状态
export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || 'null') || {
    user_id: null,
    username: '',
    real_name: '',
    dept_id: null,
    dept_name: '',
    roles: []
  })
  const permissions = ref([])
  const menus = ref([])

  const isLoggedIn = computed(() => !!token.value && !!userInfo.value?.user_id)
  const userName = computed(() => userInfo.value?.real_name || userInfo.value?.username || '')
  const userId = computed(() => userInfo.value?.user_id)
  const roles = computed(() => userInfo.value?.roles || [])

  // 登录
  async function login(loginForm) {
    try {
      const res = await loginApi(loginForm)
      if (res.code === 200) {
        token.value = res.data.access_token
        refreshToken.value = res.data.refresh_token
        userInfo.value = res.data.user
        permissions.value = res.data.user.permissions || []
        menus.value = res.data.user.menus || []
        
        localStorage.setItem('token', token.value)
        localStorage.setItem('refreshToken', refreshToken.value)
        localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
        
        return { success: true }
      }
      return { success: false, message: res.message }
    } catch (error) {
      return { success: false, message: error.response?.data?.detail || error.message || '登录失败' }
    }
  }

  // 登出
  async function logout() {
    try {
      await logoutApi()
    } catch (e) {
      // 即使API失败也清除本地状态
    }
    token.value = ''
    refreshToken.value = ''
    userInfo.value = { user_id: null, username: '', real_name: '', dept_id: null, dept_name: '', roles: [] }
    permissions.value = []
    menus.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('userInfo')
  }

  // 获取用户信息
  async function fetchUserInfo() {
    try {
      const res = await getUserInfo()
      if (res.code === 200) {
        userInfo.value = res.data
        permissions.value = res.data.permissions || []
        menus.value = res.data.menus || []
        localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
      }
    } catch (e) {
      console.error('获取用户信息失败', e)
    }
  }

  // 检查权限
  function hasPermission(permCode) {
    if (permissions.value.includes('*')) return true
    return permissions.value.includes(permCode)
  }

  // 检查角色
  function hasRole(roleCode) {
    return roles.value.some(r => r.role_code === roleCode)
  }

  // 设置用户（兼容旧代码）
  function setUser(user) {
    userInfo.value = user
  }
  
  return { 
    token, refreshToken, userInfo, permissions, menus,
    isLoggedIn, userName, userId, roles,
    login, logout, fetchUserInfo, hasPermission, hasRole, setUser 
  }
})

// 项目状态
export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const loading = ref(false)
  
  async function loadProjects(params = {}) {
    loading.value = true
    try {
      const res = await getProjectList(params)
      if (res.code === 200) {
        projects.value = res.data.list || []
      }
    } finally {
      loading.value = false
    }
  }
  
  function setCurrentProject(project) {
    currentProject.value = project
  }
  
  const activeProjects = computed(() => 
    projects.value.filter(p => p.status === '进行中')
  )
  
  const projectCount = computed(() => ({
    total: projects.value.length,
    active: projects.value.filter(p => p.status === '进行中').length,
    completed: projects.value.filter(p => p.status === '已完成').length,
    delayed: projects.value.filter(p => p.health_status === '红').length
  }))
  
  return { 
    projects, 
    currentProject, 
    loading, 
    loadProjects, 
    setCurrentProject,
    activeProjects,
    projectCount
  }
})

// 任务状态
export const useTaskStore = defineStore('task', () => {
  const myTasks = ref([])
  const todayTasks = ref([])
  const loading = ref(false)
  
  async function loadMyTasks(params = {}) {
    loading.value = true
    try {
      const res = await fetchMyTasks(params)
      if (res.code === 200) {
        myTasks.value = res.data.list || []
      }
    } finally {
      loading.value = false
    }
  }
  
  const tasksByStatus = computed(() => {
    const groups = { pending: [], inProgress: [], completed: [], blocked: [] }
    myTasks.value.forEach(task => {
      switch (task.status) {
        case '未开始': groups.pending.push(task); break
        case '进行中': groups.inProgress.push(task); break
        case '已完成': groups.completed.push(task); break
        case '阻塞': groups.blocked.push(task); break
      }
    })
    return groups
  })
  
  const overdueTasks = computed(() => 
    myTasks.value.filter(t => t.is_overdue)
  )
  
  const urgentTasks = computed(() => 
    myTasks.value.filter(t => t.priority <= 2 && t.status !== '已完成')
  )
  
  return { 
    myTasks, 
    todayTasks, 
    loading, 
    loadMyTasks,
    tasksByStatus,
    overdueTasks,
    urgentTasks
  }
})

// 预警状态
export const useAlertStore = defineStore('alert', () => {
  const alerts = ref([])
  const unreadCount = ref(0)
  const loading = ref(false)
  
  async function loadAlerts(params = {}) {
    loading.value = true
    try {
      const res = await getAlerts({ status: '待处理', ...params })
      if (res.code === 200) {
        alerts.value = res.data.list || []
        unreadCount.value = res.data.total || 0
      }
    } finally {
      loading.value = false
    }
  }
  
  function markAsRead(alertId) {
    const alert = alerts.value.find(a => a.alert_id === alertId)
    if (alert) {
      alert.status = '已处理'
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }
  
  const criticalAlerts = computed(() => 
    alerts.value.filter(a => a.alert_level === '红')
  )
  
  return { 
    alerts, 
    unreadCount, 
    loading, 
    loadAlerts, 
    markAsRead,
    criticalAlerts
  }
})

// 工时状态
export const useTimesheetStore = defineStore('timesheet', () => {
  const weekData = ref({})
  const monthSummary = ref({ total: 0, standard: 0, overtime: 0 })
  
  function setWeekData(data) {
    weekData.value = data
  }
  
  function updateEntry(assignId, date, hours) {
    if (!weekData.value[assignId]) {
      weekData.value[assignId] = {}
    }
    weekData.value[assignId][date] = hours
  }
  
  const weekTotal = computed(() => {
    let total = 0
    for (const taskId in weekData.value) {
      for (const date in weekData.value[taskId]) {
        total += weekData.value[taskId][date] || 0
      }
    }
    return total
  })
  
  return { 
    weekData, 
    monthSummary, 
    setWeekData, 
    updateEntry,
    weekTotal
  }
})

// 全局UI状态
export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const theme = ref('light')
  const loading = ref(false)
  
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
  
  function setTheme(t) {
    theme.value = t
    document.documentElement.setAttribute('data-theme', t)
  }
  
  function setLoading(val) {
    loading.value = val
  }
  
  return { 
    sidebarCollapsed, 
    theme, 
    loading,
    toggleSidebar, 
    setTheme,
    setLoading
  }
})
