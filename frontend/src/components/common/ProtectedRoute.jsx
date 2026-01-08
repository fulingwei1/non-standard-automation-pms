/**
 * Generic Protected Route Component
 * Provides role-based access control for routes
 */

import { Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { hasProcurementAccess, hasFinanceAccess, hasProductionAccess, hasProjectReviewAccess } from '../../lib/roleConfig'
import { Button } from '../ui/button'

/**
 * Permission check function type
 * @typedef {(role: string) => boolean} PermissionChecker
 */

/**
 * Generic route protection component
 * @param {Object} props
 * @param {React.ReactNode} props.children - Child components to render if authorized
 * @param {PermissionChecker} props.checkPermission - Function to check if user has permission
 * @param {string} props.permissionName - Name of the permission (for error message)
 * @param {string} props.redirectTo - Path to redirect if not authenticated (default: '/')
 */
export function ProtectedRoute({
  children,
  checkPermission,
  permissionName = '此功能',
  redirectTo = '/'
}) {
  const userStr = localStorage.getItem('user')

  if (!userStr) {
    console.warn('ProtectedRoute: No user in localStorage, redirecting to', redirectTo)
    return <Navigate to={redirectTo} replace />
  }

  let user = null
  let role = null
  let isSuperuser = false

  try {
    user = JSON.parse(userStr)
    role = user.role
    isSuperuser = user.is_superuser === true || user.isSuperuser === true
    console.log('ProtectedRoute: User role =', role, ', isSuperuser =', isSuperuser, ', permissionName =', permissionName)
  } catch (e) {
    console.warn('Invalid user data in localStorage:', e)
    localStorage.removeItem('user')
    return <Navigate to={redirectTo} replace />
  }

  // 超级管理员绕过所有权限检查
  if (isSuperuser) {
    console.log('ProtectedRoute: Superuser bypass, rendering children')
    return children
  }

  // 管理员角色也应该绕过权限检查
  if (role === 'admin' || role === 'super_admin' || role === '管理员' || role === '系统管理员') {
    console.log('ProtectedRoute: Admin role bypass, rendering children')
    return children
  }

  const hasPermission = checkPermission ? checkPermission(role) : true
  console.log('ProtectedRoute: checkPermission result =', hasPermission)

  if (!role || !hasPermission) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center justify-center h-[60vh] text-center"
      >
        <div className="text-6xl mb-4">🔒</div>
        <h1 className="text-2xl font-semibold text-white mb-2">无权限访问</h1>
        <p className="text-slate-400 mb-4">您没有权限访问{permissionName}</p>
        <Button
          onClick={() => window.history.back()}
          variant="default"
          className="mt-4"
        >
          返回上一页
        </Button>
      </motion.div>
    )
  }
  
  return children
}

/**
 * Procurement-specific protected route
 * Wrapper for ProtectedRoute with procurement permission check
 */
export function ProcurementProtectedRoute({ children }) {
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
      checkPermission={(role) => hasProcurementAccess(role, isSuperuser)}
      permissionName="采购和物料管理模块"
    >
      {children}
    </ProtectedRoute>
  )
}

/**
 * Finance-specific protected route
 * Wrapper for ProtectedRoute with finance permission check
 */
export function FinanceProtectedRoute({ children }) {
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
      checkPermission={(role) => hasFinanceAccess(role, isSuperuser)}
      permissionName="财务管理模块"
    >
      {children}
    </ProtectedRoute>
  )
}

/**
 * Production-specific protected route
 * Wrapper for ProtectedRoute with production permission check
 */
export function ProductionProtectedRoute({ children }) {
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
      checkPermission={(role) => hasProductionAccess(role, isSuperuser)}
      permissionName="生产管理模块"
    >
      {children}
    </ProtectedRoute>
  )
}

/**
 * Project Review-specific protected route
 * Wrapper for ProtectedRoute with project review permission check
 */
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