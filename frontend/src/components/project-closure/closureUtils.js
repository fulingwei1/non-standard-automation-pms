/**
 * 项目结项管理 - 工具函数
 *
 * 【架构说明】
 * 这是项目结项功能的公共工具函数，作为结项相关状态、标签等的权威数据源（Single Source of Truth）。
 * - components/project-closure/ 中的对话框组件直接使用本文件
 * - pages/ProjectClosureManagement/constants.js 从本文件 re-export，不再重复定义
 */

// 状态徽章配置（包含所有可能的结项状态）
export const STATUS_BADGES = {
 DRAFT: { label: "草稿", variant: "secondary" },
 SUBMITTED: { label: "已提交", variant: "info" },
 REVIEWED: { label: "已评审", variant: "success" },
 ARCHIVED: { label: "已归档", variant: "secondary" },
};

export const getStatusBadge = (status) => {
 return STATUS_BADGES[status] || STATUS_BADGES.DRAFT;
};
