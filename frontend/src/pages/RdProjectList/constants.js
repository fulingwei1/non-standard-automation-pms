// Animation variants
export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
};

export const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

// Status badge mapping
export const statusMap = {
  DRAFT: { label: "草稿", color: "secondary" },
  APPROVED: { label: "已审批", color: "success" },
  IN_PROGRESS: { label: "进行中", color: "primary" },
  COMPLETED: { label: "已完成", color: "success" },
  CANCELLED: { label: "已取消", color: "danger" },
};

export const approvalStatusMap = {
  PENDING: { label: "待审批", color: "warning" },
  APPROVED: { label: "已通过", color: "success" },
  REJECTED: { label: "已驳回", color: "danger" },
};

export const categoryTypeMap = {
  SELF: { label: "自主研发", color: "primary" },
  ENTRUST: { label: "委托研发", color: "info" },
  COOPERATION: { label: "合作研发", color: "success" },
};

export const DEFAULT_PAGINATION = {
  page: 1,
  page_size: 20,
  total: 0,
  pages: 0,
};

export const DEFAULT_FORM_DATA = {
  project_name: "",
  category_id: "",
  category_type: "SELF",
  initiation_date: "",
  planned_start_date: "",
  planned_end_date: "",
  project_manager_id: null,
  initiation_reason: "",
  research_goal: "",
  research_content: "",
  expected_result: "",
  budget_amount: "",
  linked_project_id: null,
  remark: "",
};
