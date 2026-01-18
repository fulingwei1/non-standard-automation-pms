/**
 * 项目结项管理 - 工具函数
 */

// 状态徽章配置
export const getStatusBadge = (status) => {
  const badges = {
    DRAFT: { label: "草稿", variant: "secondary" },
    REVIEWED: { label: "已评审", variant: "success" },
    ARCHIVED: { label: "已归档", variant: "secondary" },
  };
  return badges[status] || badges.DRAFT;
};
