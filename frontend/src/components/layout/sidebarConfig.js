/**
 * Sidebar导航配置
 *
 * 统一菜单策略：所有用户看到相同的菜单结构，通过权限控制功能开放
 * - 有权限的菜单项正常显示
 * - 无权限的菜单项灰显，鼠标悬停显示"需要XX权限"
 */

// 从模块重新导出配置
export { defaultNavGroups } from "./sidebarConfig/default";
