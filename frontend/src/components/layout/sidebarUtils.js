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
 *
 * 注意：菜单项级别的权限在 NavGroup 组件中通过 checkPermission 处理
 *
 * @deprecated 组级别的 roles 字段应迁移为 permission 字段，
 *   由 NavGroup 统一通过 PermissionContext 检查。
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
        // 使用 permission 字段优先（新方式），role 匹配作为兜底
        if (group.permission) {
          // 新方式：由调用方通过 PermissionContext 检查
          // 此处仅做标记，实际检查在 NavGroup 组件中
          return group;
        }
        // 旧方式：角色字符串匹配（过渡期保留）
        const roleMatches = group.roles.includes(role);
        if (!roleMatches) {
          return null;
        }
      }

      // 过滤空的 items
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
export function getNavGroupsForRole(role, _isSuperuser = false) {
  return defaultNavGroups;
}
