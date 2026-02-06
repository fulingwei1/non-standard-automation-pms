/**
 * 权限系统中文标签映射
 * 用于将英文模块名和权限名转换为中文显示
 */

// 模块名称中文映射
export const MODULE_LABELS = {
 system: "系统管理",
 project: "项目管理",
 advantage_product: "优势产品",
 advantage_products: "优势产品",
 assembly_kit: "装配套件",
  budget: "预算管理",
  business_support: "业务支持",
 cost: "成本管理",
 crm: "客户关系",
 customer: "客户管理",
 data_export: "数据导出",
 data_import: "数据导入",
 data_import_export: "数据导入导出",
 document: "文档管理",
 ecn: "工程变更",
 engineer: "工程师",
 finance: "财务管理",
 hourly_rate: "工时费率",
 hr: "人力资源",
 hr_management: "人力资源管理",
 installation_dispatch: "安装派遣",
 issue: "问题管理",
 machine: "设备管理",
 material: "物料管理",
  milestone: "里程碑",
 notification: "通知管理",
 organization: "组织架构",
 performance: "绩效管理",
 presales_integration: "售前集成",
 project_evaluation: "项目评价",
 project_role: "项目角色",
 purchase: "采购管理",
 qualification: "资质管理",
 report: "报表管理",
 scheduler: "调度管理",
 service: "服务管理",
 shortage_alert: "缺料预警",
 staff_matching: "人员匹配",
 stage: "阶段管理",
 supplier: "供应商",
  supply: "供应链",
 task_center: "任务中心",
 technical_spec: "技术规格",
 timesheet: "工时管理",
 work_log: "工作日志",
};

// 权限操作类型中文映射
export const ACTION_LABELS = {
  read: "查看",
 create: "创建",
 update: "更新",
 delete: "删除",
 manage: "管理",
 approve: "审批",
 submit: "提交",
 export: "导出",
 import: "导入",
 assign: "分配",
 view: "查看",
 edit: "编辑",
 list: "列表",
  detail: "详情",
  stat: "统计",
 statistics: "统计",
 config: "配置",
 configure: "配置",
 cancel: "取消",
 reject: "驳回",
 revoke: "撤销",
 transfer: "转移",
  sync: "同步",
 generate: "生成",
 download: "下载",
 upload: "上传",
 preview: "预览",
 calculate: "计算",
 evaluate: "评估",
 close: "关闭",
  reopen: "重开",
 escalate: "升级",
 resolve: "解决",
 verify: "验证",
 audit: "审计",
};

// 权限名称中文映射（用于将英文权限名转换为中文）
export const PERMISSION_NAME_LABELS = {
 // 系统管理
  "User Read": "用户查看",
 "User Manage": "用户管理",
 "Role Read": "角色查看",
 "Role Manage": "角色管理",
 "Permission Read": "权限查看",

 // 项目管理
 "Project Read": "项目查看",
 "Project Manage": "项目管理",
  "Milestone Read": "里程碑查看",
 "Milestone Manage": "里程碑管理",
 "Task Read": "任务查看",
 "Task Manage": "任务管理",
 "WBS Read": "WBS查看",
 "WBS Manage": "WBS管理",
 "Deliverable Read": "交付物查看",
 "Deliverable Submit": "交付物提交",
  "Deliverable Approve": "交付物审批",
 "Acceptance Read": "验收查看",
  "Acceptance Submit": "验收提交",
 "Acceptance Approve": "验收审批",
 "ECN Read": "工程变更查看",
 "ECN Submit": "工程变更提交",
 "ECN Approve": "工程变更审批",

 // 供应链
 "Purchase Read": "采购查看",
 "Purchase Manage": "采购管理",
 "Outsourcing Read": "外协查看",
 "Outsourcing Manage": "外协管理",

  // 财务
 "Payment Read": "付款查看",
 "Payment Approve": "付款审批",
 "Invoice Read": "发票查看",
 "Invoice Issue": "发票开具",

 // 人力资源
 "HR Read": "人力资源查看",
 "HR Manage": "人力资源管理",
 "HR Approve": "人力资源审批",
 "Employee Read": "员工查看",
 "Employee Manage": "员工管理",
 "Attendance Read": "考勤查看",
 "Attendance Manage": "考勤管理",

 // 销售
 "Sales Read": "销售查看",
 "Sales Manage": "销售管理",
 "Opportunity Read": "商机查看",
 "Opportunity Manage": "商机管理",
 "Quote Read": "报价查看",
 "Quote Manage": "报价管理",
 "Contract Read": "合同查看",
 "Contract Manage": "合同管理",

  // 通用
 "Dashboard View": "仪表盘查看",
 "Report View": "报表查看",
 "Report Export": "报表导出",
 "Notification Read": "通知查看",
  "Notification Manage": "通知管理",
};

/**
 * 获取模块的中文名称
 * @param {string} moduleCode - 模块编码
 * @returns {string} 中文名称
 */
export function getModuleLabel(moduleCode) {
 if (!moduleCode) return "未分类";
 return MODULE_LABELS[moduleCode] || moduleCode;
}

/**
 * 获取操作类型的中文名称
 * @param {string} action - 操作类型
 * @returns {string} 中文名称
 */
export function getActionLabel(action) {
 if (!action) return "-";
  return ACTION_LABELS[action.toLowerCase()] || action;
}
const ACTION_COLORS = {
 read: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
 view: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
 list: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
 detail: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
 create: 'bg-green-500/20 text-green-400 border-green-500/30',
 update: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
 edit: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
 delete: 'bg-red-500/20 text-red-400 border-red-500/30',
 approve: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
 submit: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  manage: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
 config: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  configure: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
 export: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
 import: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
};

export function getActionColor(action) {
 if (!action) return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
 return ACTION_COLORS[action.toLowerCase()] || 'bg-slate-500/20 text-slate-400 border-slate-500/30';
}


/**
 * 获取权限名称的中文显示
 * @param {string} permissionName - 权限名称
 * @returns {string} 中文名称
 */
export function getPermissionLabel(permissionName) {
 if (!permissionName) return "-";
 // 如果已经是中文，直接返回
 if (/[\u4e00-\u9fa5]/.test(permissionName)) {
  return permissionName;
 }
 // 尝试从映射中获取
 return PERMISSION_NAME_LABELS[permissionName] || permissionName;
}

/**
 * 智能生成权限的中文名称
 * 基于权限编码自动生成中文名称
 * @param {object} permission - 权限对象 {permission_code, permission_name, module, action}
 * @returns {string} 中文名称
 */
export function generatePermissionLabel(permission) {
 if (!permission) return "-";

  // 如果已有中文名称，直接使用
 if (permission.permission_name && /[\u4e00-\u9fa5]/.test(permission.permission_name)) {
 return permission.permission_name;
 }

  // 尝试从映射获取
 const mapped = PERMISSION_NAME_LABELS[permission.permission_name];
 if (mapped) return mapped;

 // 根据 module 和 action 自动生成
 const moduleLabel = getModuleLabel(permission.module);
 const actionLabel = getActionLabel(permission.action);

 if (moduleLabel && actionLabel && moduleLabel !== permission.module && actionLabel !== permission.action) {
 return `${moduleLabel}${actionLabel}`;
 }

 // 回退到原始名称
 return permission.permission_name || permission.permission_code || "-";
}
