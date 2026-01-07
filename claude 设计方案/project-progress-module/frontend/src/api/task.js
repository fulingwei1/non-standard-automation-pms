/**
 * 项目进度管理 - API 调用模块
 */
import axios from 'axios'

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 200) {
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// ===== 项目管理 =====
export const getProjectList = (params) => request.get('/projects', { params })
export const getProjectDetail = (id) => request.get(`/projects/${id}`)
export const createProject = (data) => request.post('/projects', data)
export const updateProject = (id, data) => request.put(`/projects/${id}`, data)
export const getProjectProgress = (id) => request.get(`/projects/${id}/progress`)

// ===== 任务管理 =====
export const getWbsTree = (projectId) => request.get(`/tasks/${projectId}/wbs`)
export const getGanttData = (projectId) => request.get(`/tasks/${projectId}/gantt`)
export const createTask = (data) => request.post('/tasks', data)
export const updateTask = (id, data) => request.put(`/tasks/${id}`, data)
export const updateTaskProgress = (id, data) => request.put(`/tasks/${id}/progress`, data)
export const batchUpdateProgress = (data) => request.put('/tasks/batch-progress', data)
export const updateTaskStatus = (id, data) => request.put(`/tasks/${id}/status`, data)
export const updateTaskDates = (id, data) => request.put(`/tasks/${id}/dates`, data)
export const calculateCriticalPath = (projectId) => request.post(`/tasks/${projectId}/calculate-cpm`)
export const getMyTasks = (params) => request.get('/tasks/my-tasks', { params })
export const getTodayTasks = () => request.get('/tasks/my-tasks/today')

// ===== 依赖关系 =====
export const createDependency = (data) => request.post('/tasks/dependencies', data)
export const deleteDependency = (id) => request.delete(`/tasks/dependencies/${id}`)

// ===== 工时管理 =====
export const submitTimesheet = (data) => request.post('/timesheets', data)
export const getTimesheetList = (params) => request.get('/timesheets', { params })
export const approveTimesheet = (id, data) => request.put(`/timesheets/${id}/approve`, data)

// ===== 负荷管理 =====
export const getTeamWorkload = (params) => request.get('/workload', { params })
export const getMyWorkload = (params) => request.get('/workload/my', { params })
export const getWorkloadForecast = (params) => request.get('/workload/forecast', { params })

// ===== 看板 =====
export const getPortfolioDashboard = () => request.get('/dashboard/portfolio')
export const getProjectDashboard = (id) => request.get(`/dashboard/project/${id}`)
export const getWorkspaceDashboard = () => request.get('/dashboard/workspace')

// ===== 预警 =====
export const getAlertList = (params) => request.get('/alerts', { params })
export const handleAlert = (id, data) => request.put(`/alerts/${id}/handle`, data)

// ===== 任务分配 =====
export const assignTask = (taskId, data) => request.post(`/tasks/${taskId}/assign`, data)
export const getTaskAssignments = (taskId) => request.get(`/tasks/${taskId}/assignments`)

export default request
