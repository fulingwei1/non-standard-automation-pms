/**
 * Sidebar工具函数
 * 包含导航过滤和角色匹配逻辑
 */

import {
  getNavForRole,
  hasProcurementAccess
} from "../../lib/roleConfig";
import {
  defaultNavGroups,
  engineerNavGroups,
  pmoDirectorNavGroups,
  pmcNavGroups,
  buyerNavGroups,
  productionManagerNavGroups,
  assemblerNavGroups,
  salesNavGroups,
  businessSupportNavGroups,
  procurementNavGroups,
  procurementManagerNavGroups,
  presalesNavGroups,
  manufacturingDirectorNavGroups,
  customerServiceManagerNavGroups,
  customerServiceEngineerNavGroups,
  teamLeaderNavGroups
} from "./sidebarConfig";

// Filter navigation items based on role permissions
export function filterNavItemsByRole(navGroups, role, isSuperuser = false) {
  // 超级管理员可以看到所有菜单
  if (isSuperuser) {
    return navGroups;
  }

  const hasAccess = hasProcurementAccess(role, isSuperuser);

  // Paths that require procurement access (采购订单 and 齐套分析)
  const procurementPaths = ["/purchases", "/materials", "/material-analysis"];

  return navGroups
    .map((group) => {
      // Check if group has role restrictions (e.g., system management groups)
      if (group.roles && group.roles.length > 0) {
        // Check if current role is in allowed roles
        const roleMatches = group.roles.some((allowedRole) => {
          // Direct match
          if (role === allowedRole) {return true;}
          // super_admin can access admin modules
          if (role === "super_admin" && allowedRole === "admin") {return true;}
          // Chinese role name support
          if (
            role === "管理员" &&
            (allowedRole === "admin" || allowedRole === "super_admin")
          )
            {return true;}
          if (
            (role === "admin" || role === "super_admin") &&
            allowedRole === "admin"
          )
            {return true;}
          return false;
        });
        if (!roleMatches) {
          return null; // Filter out this group
        }
      }

      // Filter items in all groups
      return {
        ...group,
        items: group.items.filter((item) => {
          // Filter 采购订单 and 齐套分析 based on role
          // These paths should only be visible to roles with procurement access
          if (procurementPaths.includes(item.path)) {
            return hasAccess;
          }
          // Show all other items
          return true;
        })
      };
    })
    .filter((group) => {
      // Remove groups that are null or have no items after filtering
      return group && group.items && group.items.length > 0;
    });
}

// Get navigation groups based on user role
export function getNavGroupsForRole(role, isSuperuser = false) {
  // 超级管理员使用默认导航组（包含所有菜单）
  if (
    isSuperuser ||
    role === "super_admin" ||
    role === "admin" ||
    role === "管理员" ||
    role === "系统管理员"
  ) {
    return defaultNavGroups;
  }

  let navGroups;

  switch (role) {
    case "chairman":
    case "董事长":
      navGroups = getNavForRole("chairman");
      break;
    case "gm":
    case "总经理":
      navGroups = getNavForRole("gm");
      break;
    case "assembler":
    case "assembler_mechanic":
    case "assembler_electrician":
    case "装配技工":
    case "装配钳工":
    case "装配电工":
      navGroups = assemblerNavGroups;
      break;
    case "sales_director":
    case "销售总监":
      // 使用 roleConfig 中的配置，确保不包含问题管理
      navGroups = getNavForRole("sales_director");
      break;
    case "sales_manager":
    case "销售经理":
      // 使用 roleConfig 中的配置，确保不包含问题管理
      navGroups = getNavForRole("sales_manager");
      break;
    case "sales":
    case "销售工程师":
      navGroups = salesNavGroups;
      break;
    case "business_support":
    case "商务支持":
    case "商务支持专员":
      navGroups = businessSupportNavGroups;
      break;
    case "procurement":
    case "采购工程师":
    case "采购专员":
      navGroups = procurementNavGroups;
      break;
    case "procurement_manager":
    case "procurement_engineer":
    case "采购部经理":
      navGroups = procurementManagerNavGroups;
      break;
    case "presales":
    case "售前技术工程师":
      navGroups = presalesNavGroups;
      break;
    case "me_engineer":
    case "ee_engineer":
    case "sw_engineer":
    case "te_engineer":
    case "rd_engineer":
    case "机械工程师":
    case "电气工程师":
    case "软件工程师":
    case "测试工程师":
    case "研发工程师":
      navGroups = engineerNavGroups;
      break;
    case "tech_dev_manager":
    case "me_dept_manager":
    case "me_mgr":
    case "te_dept_manager":
    case "ee_dept_manager":
    case "ee_mgr":
    case "技术开发部经理":
    case "机械部经理":
    case "测试部经理":
    case "电气部经理":
      navGroups = getNavForRole("dept_manager");
      break;
    case "presales_manager":
    case "售前经理":
      navGroups = presalesNavGroups;
      break;
    case "finance_manager":
    case "财务经理":
      navGroups = [
        {
          label: "财务管理",
          items: [
            {
              name: "财务工作台",
              path: "/finance-manager-dashboard",
              icon: "LayoutDashboard"
            },
            {
              name: "财务成本",
              path: "/cost-quotes/financial-costs",
              icon: "DollarSign"
            },
            { name: "成本核算", path: "/costs", icon: "Calculator" },
            {
              name: "付款审批",
              path: "/payment-approval",
              icon: "ClipboardCheck"
            },
            { name: "项目结算", path: "/settlement", icon: "FileText" },
            { name: "财务报表", path: "/financial-reports", icon: "BarChart3" },
            { name: "决策驾驶舱", path: "/executive-dashboard", icon: "Gauge" }
          ]
        },
        {
          label: "监控与预警",
          items: [{ name: "预警中心", path: "/alerts", icon: "AlertTriangle" }]
        },
        {
          label: "个人中心",
          items: [
            { name: "通知中心", path: "/notifications", icon: "Bell" },
            {
              name: "知识管理",
              path: "/knowledge-base",
              icon: "BookOpen"
            },
            { name: "个人设置", path: "/settings", icon: "Settings" }
          ]
        }
      ];
      break;
    case "hr_manager":
    case "人事经理":
      navGroups = getNavForRole("hr_manager");
      break;
    case "PMO_DIR":
    case "项目管理部总监":
      navGroups = pmoDirectorNavGroups;
      break;
    case "pmc":
    case "pm":
    case "project_dept_manager":
    case "项目经理":
    case "项目部经理":
      navGroups = pmcNavGroups;
      break;
    case "buyer":
      navGroups = buyerNavGroups;
      break;
    case "dept_manager":
      navGroups = getNavForRole("dept_manager");
      break;
    case "production_manager":
    case "生产部经理":
    case "电机生产部经理":
      navGroups = productionManagerNavGroups;
      break;
    case "manufacturing_director":
    case "制造总监":
      navGroups = manufacturingDirectorNavGroups;
      break;
    case "customer_service_manager":
    case "客服部经理":
      navGroups = customerServiceManagerNavGroups;
      break;
    case "customer_service_engineer":
    case "客服工程师":
      navGroups = customerServiceEngineerNavGroups;
      break;
    case "te_leader":
    case "me_leader":
    case "ee_leader":
      navGroups = teamLeaderNavGroups;
      break;
    default:
      navGroups = defaultNavGroups;
  }

  // Filter navigation items based on role permissions
  // Note: isSuperuser is already handled in getNavGroupsForRole, but we pass it here for consistency
  return navGroups;
}
