/**
 * 项目结项管理 - 可复用对话框组件（统一导出）
 *
 * 【架构说明】
 * 本目录是结项功能的「可复用对话框组件库」和「公共工具函数」的权威位置。
 *
 * 组件关系：
 * - components/project-closure/（本目录）：存放可复用的对话框组件和工具函数
 * - CreateClosureDialog - 创建结项申请表单
 * - ReviewClosureDialog - 结项评审表单
 * - LessonsClosureDialog - 编辑经验教训表单
 * - ClosureDetailDialog - 结项详情查看（只读）
 * - ArchiveClosureDialog - 文档归档确认
 * - closureUtils.js - 状态徽章等公共工具函数（权威数据源）
 *
 * - pages/ProjectClosureManagement/：存放结项管理页面及其页面级子组件
 * - 页面级组件（ProjectClosureContent, ProjectClosureStats 等）仅在该页面使用
 * - 对话框组件通过 re-export 从本目录引入，不重复实现
 * - constants.js 从本目录的 closureUtils.js re-export，不重复定义
 */

export { default as CreateClosureDialog } from "./CreateClosureDialog";
export { default as ReviewClosureDialog } from "./ReviewClosureDialog";
export { default as LessonsClosureDialog } from "./LessonsClosureDialog";
export { default as ArchiveClosureDialog } from "./ArchiveClosureDialog";
export { default as ClosureDetailDialog } from "./ClosureDetailDialog";
export { STATUS_BADGES, getStatusBadge } from "./closureUtils";
