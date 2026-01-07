import { useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '../../lib/utils'
import { getRoleInfo, getNavForRole, hasProcurementAccess } from '../../lib/roleConfig'
import {
  LayoutDashboard,
  BarChart3,
  Briefcase,
  Box,
  ListTodo,
  ShoppingCart,
  Package,
  AlertTriangle,
  AlertCircle,
  ClipboardCheck,
  ClipboardList,
  FileText,
  Users,
  Settings,
  ChevronLeft,
  LogOut,
  Bell,
  Clock,
  Calendar,
  Kanban,
  Building2,
  Truck,
  PackagePlus,
  PackageMinus,
  Boxes,
  Target,
  CreditCard,
  Calculator,
  FileCheck,
  Receipt,
  UserCog,
  Shield,
  Cog,
  User,
  Wrench,
  BookOpen,
  Lightbulb,
  DollarSign,
  Archive,
  Crown,
  Award,
  TrendingUp,
  CheckCircle2,
  MessageSquare,
  Star,
} from 'lucide-react'

// Icon mapping
const iconMap = {
  LayoutDashboard,
  BarChart3,
  Briefcase,
  Kanban,
  Calendar,
  ListTodo,
  ShoppingCart,
  Package,
  AlertTriangle,
  AlertCircle,
  ClipboardList,
  ClipboardCheck,
  Bell,
  Clock,
  Settings,
  Building2,
  Truck,
  PackagePlus,
  PackageMinus,
  Boxes,
  Users,
  Target,
  CreditCard,
  Calculator,
  FileCheck,
  FileText,
  Receipt,
  UserCog,
  Shield,
  Cog,
  Wrench,
  BookOpen,
  Lightbulb,
  DollarSign,
  Archive,
  Crown,
  Award,
  TrendingUp,
  CheckCircle2,
  MessageSquare,
  Star,
}

// Default navigation groups (for admin and general use)
const defaultNavGroups = [
  {
    label: '概览',
    items: [
      { name: '仪表盘', path: '/', icon: 'LayoutDashboard' },
      { name: '运营大屏', path: '/operation', icon: 'BarChart3' },
    ],
  },
  {
    label: '项目管理',
    items: [
      { name: '项目看板', path: '/board', icon: 'Kanban' },
      { name: '项目列表', path: '/projects', icon: 'Briefcase' },
      { name: '排期看板', path: '/schedule', icon: 'Calendar' },
      { name: '任务中心', path: '/tasks', icon: 'ListTodo' },
    ],
  },
  {
    label: 'PMO 项目管理部',
    items: [
      { name: 'PMO 驾驶舱', path: '/pmo/dashboard', icon: 'LayoutDashboard' },
      { name: '立项管理', path: '/pmo/initiations', icon: 'FileText' },
      { name: '阶段管理', path: '/pmo/phases', icon: 'Target' },
      { name: '风险管理', path: '/pmo/risks', icon: 'AlertTriangle' },
      { name: '风险预警墙', path: '/pmo/risk-wall', icon: 'AlertTriangle' },
      { name: '项目结项', path: '/pmo/closure', icon: 'CheckCircle2' },
      { name: '项目复盘', path: '/projects/reviews', icon: 'FileText' },
      { name: '资源总览', path: '/pmo/resource-overview', icon: 'Users' },
      { name: '会议管理', path: '/pmo/meetings', icon: 'Calendar' },
      { name: '项目周报', path: '/pmo/weekly-report', icon: 'BarChart3' },
    ],
  },
  {
    label: '运营管理',
    items: [
      { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
      { name: '缺料管理', path: '/shortage', icon: 'Package' },
      { name: '齐套检查', path: '/kit-check', icon: 'CheckCircle2' },
      { name: '齐套分析', path: '/materials', icon: 'Package' },
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle', badge: '3' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '质量验收',
    items: [
      { name: '验收管理', path: '/acceptance', icon: 'ClipboardList' },
      { name: '审批中心', path: '/approvals', icon: 'ClipboardCheck', badge: '2' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '5' },
      { name: '岗位打卡', path: '/punch-in', icon: 'Clock' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
  {
    label: '系统管理',
    items: [
      { name: '用户管理', path: '/user-management', icon: 'Users' },
      { name: '角色管理', path: '/role-management', icon: 'Shield' },
    ],
    roles: ['admin', 'super_admin'], // 仅管理员可见
  },
  {
    label: '主数据管理',
    items: [
      { name: '客户管理', path: '/customer-management', icon: 'Building2' },
      { name: '供应商管理', path: '/supplier-management-data', icon: 'Truck' },
      { name: '部门管理', path: '/department-management', icon: 'Building2' },
    ],
    roles: ['admin', 'super_admin'], // 仅管理员可见
  },
]

// Engineer nav with workstation (Gantt/Calendar view)
const engineerNavGroups = [
  {
    label: '我的工作',
    items: [
      { name: '工作台', path: '/workstation', icon: 'LayoutDashboard' },
      { name: '任务中心', path: '/tasks', icon: 'ListTodo' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
    ],
  },
  {
    label: '监控与预警',
    items: [
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '5' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// PMC nav groups
const pmcNavGroups = [
  {
    label: '概览',
    items: [
      { name: '仪表盘', path: '/', icon: 'LayoutDashboard' },
      { name: '运营大屏', path: '/operation', icon: 'BarChart3' },
    ],
  },
  {
    label: '生产计划',
    items: [
      { name: '项目看板', path: '/board', icon: 'Kanban' },
      { name: '排期看板', path: '/schedule', icon: 'Calendar' },
      { name: '齐套分析', path: '/materials', icon: 'Package' },
    ],
  },
  {
    label: '采购跟踪',
    items: [
      { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
      { name: '缺料管理', path: '/shortage', icon: 'Package' },
      { name: '齐套检查', path: '/kit-check', icon: 'CheckCircle2' },
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle', badge: '3' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Buyer nav groups
const buyerNavGroups = [
  {
    label: '概览',
    items: [
      { name: '仪表盘', path: '/', icon: 'LayoutDashboard' },
    ],
  },
  {
    label: '采购管理',
    items: [
      { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
      { name: '供应商管理', path: '/suppliers', icon: 'Building2' },
      { name: '缺料管理', path: '/shortage', icon: 'Package' },
      { name: '到货跟踪', path: '/arrivals', icon: 'Truck' },
    ],
  },
  {
    label: '监控与预警',
    items: [
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// General Manager nav groups
const generalManagerNavGroups = [
  {
    label: '经营管理',
    items: [
      { name: '总经理工作台', path: '/gm-dashboard', icon: 'LayoutDashboard' },
      { name: '经营报表', path: '/business-reports', icon: 'BarChart3' },
      { name: '运营大屏', path: '/operation', icon: 'BarChart3' },
    ],
  },
  {
    label: '项目管理',
    items: [
      { name: '项目看板', path: '/board', icon: 'Kanban' },
      { name: '项目列表', path: '/projects', icon: 'Briefcase' },
      { name: '排期看板', path: '/schedule', icon: 'Calendar' },
    ],
  },
  {
    label: '审批与监控',
    items: [
      { name: '审批中心', path: '/approvals', icon: 'ClipboardCheck', badge: '8' },
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle', badge: '3' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '运营管理',
    items: [
      { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
      { name: '缺料管理', path: '/shortage', icon: 'Package' },
      { name: '齐套检查', path: '/kit-check', icon: 'CheckCircle2' },
      { name: '齐套分析', path: '/materials', icon: 'Package' },
      { name: '验收管理', path: '/acceptance', icon: 'ClipboardList' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '5' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Chairman nav groups
const chairmanNavGroups = [
  {
    label: '战略决策',
    items: [
      { name: '董事长工作台', path: '/chairman-dashboard', icon: 'LayoutDashboard' },
      { name: '经营报表', path: '/business-reports', icon: 'BarChart3' },
      { name: '战略分析', path: '/strategy-analysis', icon: 'Target' },
    ],
  },
  {
    label: '全面监控',
    items: [
      { name: '项目看板', path: '/board', icon: 'Kanban' },
      { name: '项目列表', path: '/projects', icon: 'Briefcase' },
      { name: '运营大屏', path: '/operation', icon: 'BarChart3' },
      { name: '销售业绩', path: '/sales-director-dashboard', icon: 'TrendingUp' },
    ],
  },
  {
    label: '重大事项',
    items: [
      { name: '审批中心', path: '/approvals', icon: 'ClipboardCheck', badge: '5' },
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle', badge: '3' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
      { name: '决策事项', path: '/key-decisions', icon: 'Crown' },
    ],
  },
  {
    label: '组织管理',
    items: [
      { name: '部门管理', path: '/departments', icon: 'Building2' },
      { name: '人员管理', path: '/employees', icon: 'Users' },
      { name: '绩效管理', path: '/performance', icon: 'Award' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '8' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Department manager nav groups
const deptManagerNavGroups = [
  {
    label: '概览',
    items: [
      { name: '仪表盘', path: '/', icon: 'LayoutDashboard' },
      { name: '运营大屏', path: '/operation', icon: 'BarChart3' },
    ],
  },
  {
    label: '项目管理',
    items: [
      { name: '项目看板', path: '/board', icon: 'Kanban' },
      { name: '排期看板', path: '/schedule', icon: 'Calendar' },
      { name: '任务中心', path: '/tasks', icon: 'ListTodo' },
    ],
  },
        {
          label: '团队管理',
          items: [
            { name: '审批中心', path: '/approvals', icon: 'ClipboardCheck', badge: '2' },
            { name: '预警中心', path: '/alerts', icon: 'AlertTriangle', badge: '3' },
            { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
          ],
        },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Production manager nav groups
const productionManagerNavGroups = [
  {
    label: '生产管理',
    items: [
      { name: '生产工作台', path: '/production-dashboard', icon: 'LayoutDashboard' },
      { name: '项目看板', path: '/board', icon: 'Kanban' },
      { name: '排期看板', path: '/schedule', icon: 'Calendar' },
    ],
  },
  {
    label: '运营管理',
    items: [
      { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
      { name: '缺料管理', path: '/shortage', icon: 'Package' },
      { name: '齐套检查', path: '/kit-check', icon: 'CheckCircle2' },
      { name: '齐套分析', path: '/materials', icon: 'Package' },
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle', badge: '3' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Assembler specific nav groups
const assemblerNavGroups = [
  {
    label: '我的工作',
    items: [
      { name: '装配任务', path: '/assembly-tasks', icon: 'Wrench' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
    ],
  },
  {
    label: '监控与预警',
    items: [
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '5' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Sales engineer nav groups
const salesNavGroups = [
  {
    label: '销售工作',
    items: [
      { name: '销售工作台', path: '/sales-dashboard', icon: 'LayoutDashboard' },
      { name: '客户管理', path: '/customers', icon: 'Building2' },
      { name: '商机看板', path: '/opportunities', icon: 'Target' },
    ],
  },
  {
    label: '销售管理',
    items: [
      { name: '线索评估', path: '/lead-assessment', icon: 'Target' },
      { name: '报价管理', path: '/sales/quotes', icon: 'Calculator' },
      { name: '合同管理', path: '/sales/contracts', icon: 'FileCheck' },
      { name: '应收账款', path: '/sales/receivables', icon: 'CreditCard' },
      { name: '回款跟踪', path: '/payments', icon: 'CreditCard' },
    ],
  },
  {
    label: '项目跟踪',
    items: [
      { name: '项目进度', path: '/sales-projects', icon: 'Briefcase' },
      { name: '项目看板', path: '/board', icon: 'Kanban' },
    ],
  },
  {
    label: '监控与预警',
    items: [
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '3' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Business support nav groups
const businessSupportNavGroups = [
  {
    label: '商务工作',
    items: [
      { name: '商务工作台', path: '/business-support', icon: 'LayoutDashboard' },
      { name: '客户管理', path: '/customers', icon: 'Building2' },
      { name: '投标管理', path: '/bidding', icon: 'Target' },
    ],
  },
  {
    label: '合同与订单',
    items: [
      { name: '合同管理', path: '/contracts', icon: 'FileCheck' },
      { name: '报价管理', path: '/quotations', icon: 'Calculator' },
      { name: '项目订单', path: '/sales-projects', icon: 'Briefcase' },
    ],
  },
  {
    label: '财务与发货',
    items: [
      { name: '回款跟踪', path: '/payments', icon: 'CreditCard' },
      { name: '对账开票', path: '/invoices', icon: 'Receipt' },
      { name: '出货管理', path: '/shipments', icon: 'Package' },
    ],
  },
  {
    label: '文档与归档',
    items: [
      { name: '文件管理', path: '/documents', icon: 'Archive' },
      { name: '验收管理', path: '/acceptance', icon: 'ClipboardList' },
    ],
  },
  {
    label: '监控与预警',
    items: [
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '3' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Procurement engineer nav groups
const procurementNavGroups = [
  {
    label: '采购工作',
    items: [
      { name: '采购工作台', path: '/procurement-dashboard', icon: 'LayoutDashboard' },
      { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
      { name: '采购申请', path: '/purchase-requests', icon: 'FileText' },
      { name: '从BOM生成订单', path: '/purchases/from-bom', icon: 'Package' },
      { name: '供应商管理', path: '/suppliers', icon: 'Building2' },
    ],
  },
  {
    label: '物料管理',
    items: [
      { name: '物料跟踪', path: '/materials', icon: 'Package' },
      { name: '收货管理', path: '/purchases/receipts', icon: 'Truck' },
      { name: '到货跟踪', path: '/arrivals', icon: 'Truck' },
      { name: '齐套分析', path: '/bom-analysis', icon: 'Boxes' },
    ],
  },
  {
    label: '成本控制',
    items: [
      { name: '预算管理', path: '/budgets', icon: 'CreditCard' },
      { name: '成本分析', path: '/cost-analysis', icon: 'BarChart3' },
    ],
  },
  {
    label: '监控与预警',
    items: [
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
      { name: '缺料预警', path: '/shortage-alert', icon: 'AlertTriangle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '2' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Procurement manager nav groups
const procurementManagerNavGroups = [
  {
    label: '概览',
    items: [
      { name: '仪表盘', path: '/', icon: 'LayoutDashboard' },
      { name: '采购工作台', path: '/procurement-manager-dashboard', icon: 'LayoutDashboard' },
    ],
  },
  {
    label: '采购管理',
    items: [
      { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
      { name: '供应商管理', path: '/suppliers', icon: 'Building2' },
      { name: '缺料管理', path: '/shortage', icon: 'Package' },
      { name: '到货跟踪', path: '/arrivals', icon: 'Truck' },
    ],
  },
  {
    label: '监控与预警',
    items: [
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Pre-sales technical engineer nav groups
const presalesNavGroups = [
  {
    label: '技术支持',
    items: [
      { name: '工作台', path: '/presales-dashboard', icon: 'LayoutDashboard' },
      { name: '任务中心', path: '/presales-tasks', icon: 'ListTodo' },
    ],
  },
  {
    label: '方案管理',
    items: [
      { name: '方案中心', path: '/solutions', icon: 'FileText' },
      { name: '需求调研', path: '/requirement-survey', icon: 'ClipboardList' },
      { name: '投标中心', path: '/bidding', icon: 'Target' },
    ],
  },
  {
    label: '知识库',
    items: [
      { name: '知识检索', path: '/knowledge-base', icon: 'BookOpen' },
    ],
  },
  {
    label: '监控与预警',
    items: [
      { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
      { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
    ],
  },
  {
    label: '个人中心',
    items: [
      { name: '通知中心', path: '/notifications', icon: 'Bell', badge: '2' },
      { name: '工时填报', path: '/timesheet', icon: 'Clock' },
      { name: '个人设置', path: '/settings', icon: 'Settings' },
    ],
  },
]

// Use the permission check function from roleConfig for consistency

// Filter navigation items based on role permissions
function filterNavItemsByRole(navGroups, role, isSuperuser = false) {
  // 超级管理员可以看到所有菜单
  if (isSuperuser) {
    return navGroups
  }
  
  const hasAccess = hasProcurementAccess(role, isSuperuser)
  
  // Paths that require procurement access (采购订单 and 齐套分析)
  const procurementPaths = ['/purchases', '/materials', '/bom-analysis', '/material-analysis']
  
  return navGroups.map(group => {
    // Check if group has role restrictions (e.g., system management groups)
    if (group.roles && group.roles.length > 0) {
      // Check if current role is in allowed roles
      const roleMatches = group.roles.some(allowedRole => {
        // Direct match
        if (role === allowedRole) return true
        // super_admin can access admin modules
        if (role === 'super_admin' && allowedRole === 'admin') return true
        // Chinese role name support
        if (role === '管理员' && (allowedRole === 'admin' || allowedRole === 'super_admin')) return true
        if ((role === 'admin' || role === 'super_admin') && allowedRole === 'admin') return true
        return false
      })
      if (!roleMatches) {
        return null // Filter out this group
      }
    }
    
    // Filter items in all groups
    return {
      ...group,
      items: group.items.filter(item => {
        // Filter 采购订单 and 齐套分析 based on role
        // These paths should only be visible to roles with procurement access
        if (procurementPaths.includes(item.path)) {
          return hasAccess
        }
        // Show all other items
        return true
      })
    }
  }).filter(group => {
    // Remove groups that are null or have no items after filtering
    return group && group.items && group.items.length > 0
  })
}

// Get navigation groups based on user role
function getNavGroupsForRole(role, isSuperuser = false) {
  // 超级管理员使用默认导航组（包含所有菜单）
  if (isSuperuser || role === 'super_admin' || role === 'admin' || role === '管理员' || role === '系统管理员') {
    return defaultNavGroups
  }
  
  let navGroups
  
  switch (role) {
    case 'chairman':
    case '董事长':
      navGroups = chairmanNavGroups
      break
    case 'gm':
    case '总经理':
      navGroups = generalManagerNavGroups
      break
    case 'assembler':
    case '装配技工':
      navGroups = assemblerNavGroups
      break
    case 'sales_director':
    case '销售总监':
      // 使用 roleConfig 中的配置，确保不包含问题管理
      navGroups = getNavForRole('sales_director')
      break
    case 'sales_manager':
    case '销售经理':
      // 使用 roleConfig 中的配置，确保不包含问题管理
      navGroups = getNavForRole('sales_manager')
      break
    case 'sales':
    case '销售工程师':
      navGroups = salesNavGroups
      break
    case 'business_support':
    case '商务支持':
    case '商务支持专员':
      navGroups = businessSupportNavGroups
      break
    case 'procurement':
    case '采购工程师':
    case '采购专员':
      navGroups = procurementNavGroups
      break
    case 'procurement_manager':
    case 'procurement_engineer':
    case '采购部经理':
      navGroups = procurementManagerNavGroups
      break
    case 'presales':
    case '售前技术工程师':
      navGroups = presalesNavGroups
      break
    case 'me_engineer':
    case 'ee_engineer':
    case 'sw_engineer':
    case 'te_engineer':
      navGroups = engineerNavGroups
      break
    case 'pmc':
      navGroups = pmcNavGroups
      break
    case 'buyer':
      navGroups = buyerNavGroups
      break
    case 'dept_manager':
      navGroups = deptManagerNavGroups
      break
    case 'production_manager':
    case '生产部经理':
    case '电机生产部经理':
      navGroups = productionManagerNavGroups
      break
    case 'manufacturing_director':
    case '制造总监':
      navGroups = [
        {
          label: '概览',
          items: [
            { name: '仪表盘', path: '/', icon: 'LayoutDashboard' },
            { name: '运营大屏', path: '/operation', icon: 'BarChart3' },
          ],
        },
        {
          label: '生产管理',
          items: [
            { name: '生产工作台', path: '/production-dashboard', icon: 'LayoutDashboard' },
            { name: '项目看板', path: '/board', icon: 'Kanban' },
            { name: '排期看板', path: '/schedule', icon: 'Calendar' },
          ],
        },
        {
          label: '运营管理',
          items: [
            { name: '采购订单', path: '/purchases', icon: 'ShoppingCart' },
            { name: '齐套分析', path: '/materials', icon: 'Package' },
            { name: '预警中心', path: '/alerts', icon: 'AlertTriangle', badge: '3' },
            { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
          ],
        },
        {
          label: '个人中心',
          items: [
            { name: '通知中心', path: '/notifications', icon: 'Bell' },
            { name: '个人设置', path: '/settings', icon: 'Settings' },
          ],
        },
      ]
      break
    case 'customer_service_manager':
    case '客服部经理':
      navGroups = [
        {
          label: '概览',
          items: [
            { name: '仪表盘', path: '/', icon: 'LayoutDashboard' },
          ],
        },
        {
          label: '客服管理',
          items: [
            { name: '工作台', path: '/customer-service-dashboard', icon: 'LayoutDashboard' },
            { name: '项目看板', path: '/board', icon: 'Kanban' },
            { name: '任务中心', path: '/tasks', icon: 'ListTodo' },
            { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
          ],
        },
        {
          label: '监控与预警',
          items: [
            { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
            { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
          ],
        },
        {
          label: '个人中心',
          items: [
            { name: '通知中心', path: '/notifications', icon: 'Bell' },
            { name: '个人设置', path: '/settings', icon: 'Settings' },
          ],
        },
      ]
      break
    case 'customer_service_engineer':
    case '客服工程师':
      navGroups = [
        {
          label: '我的工作',
          items: [
            { name: '工作台', path: '/customer-service-dashboard', icon: 'LayoutDashboard' },
            { name: '服务工单', path: '/service-tickets', icon: 'FileText' },
            { name: '服务记录', path: '/service-records', icon: 'ClipboardCheck' },
            { name: '客户沟通', path: '/customer-communications', icon: 'MessageSquare' },
            { name: '满意度调查', path: '/customer-satisfaction', icon: 'Star' },
            { name: '服务分析', path: '/service-analytics', icon: 'BarChart3' },
            { name: '知识库', path: '/service-knowledge-base', icon: 'BookOpen' },
            { name: '任务中心', path: '/tasks', icon: 'ListTodo' },
            { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
            { name: '工时填报', path: '/timesheet', icon: 'Clock' },
          ],
        },
        {
          label: '监控与预警',
          items: [
            { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
            { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
          ],
        },
        {
          label: '个人中心',
          items: [
            { name: '通知中心', path: '/notifications', icon: 'Bell' },
            { name: '个人设置', path: '/settings', icon: 'Settings' },
          ],
        },
      ]
      break
    case 'te_leader':
    case 'me_leader':
    case 'ee_leader':
      navGroups = [
        {
          label: '概览',
          items: [
            { name: '仪表盘', path: '/', icon: 'LayoutDashboard' },
          ],
        },
        {
          label: '团队管理',
          items: [
            { name: '项目看板', path: '/board', icon: 'Kanban' },
            { name: '任务中心', path: '/tasks', icon: 'ListTodo' },
            { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
          ],
        },
        {
          label: '监控与预警',
          items: [
            { name: '预警中心', path: '/alerts', icon: 'AlertTriangle' },
            { name: '问题管理', path: '/issues', icon: 'AlertCircle' },
          ],
        },
        {
          label: '个人中心',
          items: [
            { name: '通知中心', path: '/notifications', icon: 'Bell' },
            { name: '工时填报', path: '/timesheet', icon: 'Clock' },
            { name: '个人设置', path: '/settings', icon: 'Settings' },
          ],
        },
      ]
      break
    default:
      navGroups = defaultNavGroups
  }
  
  // Filter navigation items based on role permissions
  // Note: isSuperuser is already handled in getNavGroupsForRole, but we pass it here for consistency
  return navGroups
}

export function Sidebar({ collapsed = false, onToggle, onLogout, user }) {
  const location = useLocation()

  // Get user role from localStorage if not provided - memoized
  const currentUser = useMemo(() => {
    try {
      return user || JSON.parse(localStorage.getItem('user') || '{}')
    } catch (e) {
      console.warn('Failed to parse user from localStorage:', e)
      return {}
    }
  }, [user])

  const role = useMemo(() => currentUser?.role || 'admin', [currentUser])
  const isSuperuser = useMemo(() => currentUser?.is_superuser === true || currentUser?.isSuperuser === true, [currentUser])
  const roleInfo = useMemo(() => getRoleInfo(role), [role])

  // Get navigation groups based on role - memoized
  const navGroups = useMemo(() => {
    const groups = getNavGroupsForRole(role, isSuperuser)
    return filterNavItemsByRole(groups, role, isSuperuser)
  }, [role, isSuperuser])

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen z-40',
        'flex flex-col',
        'bg-surface-50/80 backdrop-blur-xl',
        'border-r border-white/5',
        'transition-all duration-300 ease-out',
        collapsed ? 'w-[72px]' : 'w-60'
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          'flex items-center h-16 px-4',
          'border-b border-white/5'
        )}
      >
        <div
          className={cn(
            'flex items-center justify-center',
            'w-10 h-10 rounded-xl',
            'bg-gradient-to-br from-violet-600 to-indigo-600',
            'shadow-lg shadow-violet-500/30'
          )}
        >
          <Box className="h-5 w-5 text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              className="ml-3 text-lg font-semibold text-white whitespace-nowrap overflow-hidden"
            >
              PMS 系统
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Role indicator */}
      {!collapsed && (
        <div className="px-4 py-3 border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500/20 to-indigo-500/20 flex items-center justify-center">
              <User className="w-4 h-4 text-violet-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {currentUser?.name || '用户'}
              </p>
              <p className="text-xs text-slate-500 truncate">
                {roleInfo.name}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto custom-scrollbar py-4 px-3">
        {navGroups.map((group, gi) => (
          <div key={gi} className="mb-6">
            <AnimatePresence>
              {!collapsed && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="px-3 mb-2 text-xs font-medium text-slate-500 uppercase tracking-wider"
                >
                  {group.label}
                </motion.p>
              )}
            </AnimatePresence>
            <div className="space-y-1">
              {group.items.map((item) => {
                const isActive = location.pathname === item.path
                const Icon = iconMap[item.icon] || Box
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'relative flex items-center gap-3 px-3 py-2.5 rounded-xl',
                      'text-sm font-medium transition-all duration-200',
                      'group',
                      isActive
                        ? 'text-white bg-white/[0.08]'
                        : 'text-slate-400 hover:text-white hover:bg-white/[0.04]',
                      collapsed && 'justify-center'
                    )}
                  >
                    {/* Active indicator */}
                    {isActive && (
                      <motion.div
                        layoutId="activeNav"
                        className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-full bg-primary"
                        transition={{ type: 'spring', duration: 0.5 }}
                      />
                    )}

                    <Icon
                      className={cn(
                        'h-5 w-5 flex-shrink-0',
                        isActive
                          ? 'text-primary'
                          : 'text-slate-500 group-hover:text-slate-300'
                      )}
                    />

                    <AnimatePresence>
                      {!collapsed && (
                        <motion.span
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: 'auto' }}
                          exit={{ opacity: 0, width: 0 }}
                          className="whitespace-nowrap overflow-hidden"
                        >
                          {item.name}
                        </motion.span>
                      )}
                    </AnimatePresence>

                    {/* Badge */}
                    {item.badge && !collapsed && (
                      <span className="ml-auto px-2 py-0.5 text-xs rounded-full bg-red-500/20 text-red-400">
                        {item.badge}
                      </span>
                    )}

                    {/* Tooltip for collapsed state */}
                    {collapsed && (
                      <div
                        className={cn(
                          'absolute left-full ml-2 px-3 py-1.5 rounded-lg',
                          'bg-surface-200 text-white text-sm whitespace-nowrap',
                          'opacity-0 invisible group-hover:opacity-100 group-hover:visible',
                          'transition-all duration-200 z-50'
                        )}
                      >
                        {item.name}
                        <div className="absolute left-0 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-surface-200 rotate-45" />
                      </div>
                    )}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-white/5 space-y-1">
        {onLogout && (
          <button
            onClick={onLogout}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl',
              'text-sm font-medium text-red-400',
              'hover:text-red-300 hover:bg-red-500/10',
              'transition-all duration-200',
              collapsed && 'justify-center'
            )}
          >
            <LogOut className="h-5 w-5" />
            {!collapsed && <span>退出登录</span>}
          </button>
        )}

        {onToggle && (
          <button
            onClick={onToggle}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl',
              'text-sm font-medium text-slate-400',
              'hover:text-white hover:bg-white/[0.04]',
              'transition-all duration-200',
              collapsed && 'justify-center'
            )}
          >
            <ChevronLeft
              className={cn(
                'h-5 w-5 transition-transform duration-300',
                collapsed && 'rotate-180'
              )}
            />
            {!collapsed && <span>收起侧边栏</span>}
          </button>
        )}
      </div>
    </aside>
  )
}

export default Sidebar
