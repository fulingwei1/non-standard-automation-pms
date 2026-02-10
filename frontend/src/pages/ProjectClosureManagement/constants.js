/**
 * 项目结项管理 - 常量定义
 *
 * 【架构说明】
 * 状态徽章和工具函数统一定义在 components/project-closure/closureUtils.js 中，
 * 本文件作为 re-export 层，避免重复定义。如需新增结项相关常量，
 * 通用的（如状态徽章）请加到 closureUtils.js，页面专用的可加在本文件中。
 */
export { STATUS_BADGES, getStatusBadge } from "../../components/project-closure/closureUtils";
