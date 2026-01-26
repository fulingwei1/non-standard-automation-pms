/**
 * Sidebar工具函数
 *
 * 统一菜单策略：所有用户看到相同的菜单结构，通过权限控制功能开放
 * - 有权限的菜单项正常显示
 * - 无权限的菜单项灰显，鼠标悬停显示"需要XX权限"
 */

import { defaultNavGroups } from "./sidebarConfig";

/**
 * 过滤导航组（保留组级别的 roles 过滤）
 * 注意：菜单项级别的权限在 NavGroup 组件中通过 checkPermission 处理
 */
export function filterNavItemsByRole(navGroups, role, isSuperuser = false) {
  // 超级管理员可以看到所有菜单
  if (isSuperuser) {
    return navGroups;
  }

  return navGroups
    .map((group) => {
      // 检查组级别的角色限制（如系统管理模块）
      if (group.roles && group.roles.length > 0) {
        const roleMatches = group.roles.some((allowedRole) => {
          if (role === allowedRole) return true;
          if (role === "super_admin" && allowedRole === "admin") return true;
          if (role === "管理员" && (allowedRole === "admin" || allowedRole === "super_admin")) return true;
          if ((role === "admin" || role === "super_admin") && allowedRole === "admin") return true;
          return false;
        });
        if (!roleMatches) {
          return null; // 过滤掉整个组
        }
      }

      // 过滤空的 items（如财务管理目前是空的）
      if (!group.items || group.items.length === 0) {
        return null;
      }

      return group;
    })
    .filter((group) => group !== null);
}

/**
 * 获取导航组 - 统一返回 defaultNavGroups
 *
 * 所有角色使用相同的菜单结构，权限由 NavGroup/NavItem 组件根据 permission 字段控制
 */
export function getNavGroupsForRole(role, isSuperuser = false) {
  // 所有角色都使用统一的菜单结构
  // 权限控制在组件层面通过 checkPermission 实现
  return defaultNavGroups;
}
