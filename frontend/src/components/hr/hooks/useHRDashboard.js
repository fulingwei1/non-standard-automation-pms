/**
 * useHRDashboard Hook
 * 管理 HR Dashboard 核心数据和状态
 */
import { useState, useEffect, useCallback } from 'react'
import { employeeApi, departmentApi } from '../../../services/api'

export function useHRDashboard() {
  const [selectedTab, setSelectedTab] = useState('overview')
  const [statisticsPeriod, setStatisticsPeriod] = useState('month')
  const [employees, setEmployees] = useState([])
  const [departments, setDepartments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterDepartment, setFilterDepartment] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [statsLoading, setStatsLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  // 加载员工列表
  const loadEmployees = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        skip: 0,
        limit: 100,
      }
      const response = await employeeApi.list(params)
      const employeeList = response.data || []

      // 前端筛选（临时方案，待后端支持keyword/department/is_active参数）
      let filtered = employeeList
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        filtered = filtered.filter(
          (emp) =>
            (emp.name && emp.name.toLowerCase().includes(keyword)) ||
            (emp.employee_code &&
              emp.employee_code.toLowerCase().includes(keyword)) ||
            (emp.phone && emp.phone.includes(keyword))
        )
      }
      if (filterDepartment !== 'all') {
        filtered = filtered.filter((emp) => emp.department === filterDepartment)
      }
      if (filterStatus !== 'all') {
        filtered = filtered.filter((emp) =>
          filterStatus === 'active' ? emp.is_active : !emp.is_active
        )
      }
      setEmployees(filtered)
      setError(null)
    } catch (error) {
      console.error('加载员工列表失败:', error)
      setError(
        error.response?.data?.detail || error.message || '加载员工列表失败'
      )
      setEmployees([])
    } finally {
      setLoading(false)
    }
  }, [searchKeyword, filterDepartment, filterStatus])

  // 加载部门列表
  const loadDepartments = useCallback(async () => {
    try {
      const response = await departmentApi.list({})
      setDepartments(response.data || [])
    } catch (error) {
      console.error('加载部门列表失败:', error)
      // 部门加载失败不影响主流程，使用空数组
      setDepartments([])
    }
  }, [])

  // 当切换到员工管理 Tab 时加载数据
  useEffect(() => {
    if (selectedTab === 'employees') {
      loadEmployees()
      loadDepartments()
    }
  }, [selectedTab, loadEmployees, loadDepartments])

  // 刷新数据
  const refresh = useCallback(async () => {
    setRefreshing(true)
    try {
      if (selectedTab === 'employees') {
        await Promise.all([loadEmployees(), loadDepartments()])
      }
    } finally {
      setRefreshing(false)
    }
  }, [selectedTab, loadEmployees, loadDepartments])

  return {
    // Tab 状态
    selectedTab,
    setSelectedTab,
    statisticsPeriod,
    setStatisticsPeriod,
    // 数据
    employees,
    departments,
    // 加载状态
    loading,
    statsLoading,
    refreshing,
    error,
    // 筛选条件
    searchKeyword,
    setSearchKeyword,
    filterDepartment,
    setFilterDepartment,
    filterStatus,
    setFilterStatus,
    // 操作方法
    loadEmployees,
    loadDepartments,
    refresh,
  }
}
