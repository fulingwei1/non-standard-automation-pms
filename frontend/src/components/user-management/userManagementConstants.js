// 用户管理业务配置
export const USER_STATUS = {
  ACTIVE: 'active', // 活跃
  INACTIVE: 'inactive', // 非活跃
  SUSPENDED: 'suspended', // 暂停
  PENDING: 'pending' // 待激活
};

export const USER_ROLE = {
  ADMIN: 'admin', // 管理员
  MANAGER: 'manager', // 经理
  SUPERVISOR: 'supervisor', // 主管
  ENGINEER: 'engineer', // 工程师
  TECHNICIAN: 'technician', // 技术员
  SALESPERSON: 'salesperson', // 销售员
  CUSTOMER_SERVICE: 'customer_service', // 客服
  FINANCE: 'finance', // 财务
  HR: 'hr', // 人力资源
  OPERATIONS: 'operations' // 运营
};

export const USER_DEPARTMENT = {
  ENGINEERING: 'engineering', // 工程部
  SALES: 'sales', // 销售部
  CUSTOMER_SERVICE: 'customer_service', // 客服部
  FINANCE: 'finance', // 财务部
  HR: 'hr', // 人力资源部
  OPERATIONS: 'operations', // 运营部
  MANAGEMENT: 'management', // 管理层
  IT: 'it', // IT部
  QUALITY: 'quality', // 质量部
  MARKETING: 'marketing' // 市场部
};

export const USER_PERMISSION = {
  // 用户管理权限
  USER_CREATE: 'user_create', // 创建用户
  USER_READ: 'user_read', // 查看用户
  USER_UPDATE: 'user_update', // 更新用户
  USER_DELETE: 'user_delete', // 删除用户

  // 角色管理权限
  ROLE_CREATE: 'role_create', // 创建角色
  ROLE_READ: 'role_read', // 查看角色
  ROLE_UPDATE: 'role_update', // 更新角色
  ROLE_DELETE: 'role_delete', // 删除角色

  // 项目管理权限
  PROJECT_CREATE: 'project_create', // 创建项目
  PROJECT_READ: 'project_read', // 查看项目
  PROJECT_UPDATE: 'project_update', // 更新项目
  PROJECT_DELETE: 'project_delete', // 删除项目

  // 系统管理权限
  SYSTEM_CONFIG: 'system_config', // 系统配置
  DATA_EXPORT: 'data_export', // 数据导出
  REPORT_VIEW: 'report_view', // 查看报表
  ANALYTICS: 'analytics' // 数据分析
};

export const USER_GENDER = {
  MALE: 'male', // 男性
  FEMALE: 'female', // 女性
  OTHER: 'other' // 其他
};

export const EMPLOYMENT_TYPE = {
  FULL_TIME: 'full_time', // 全职
  PART_TIME: 'part_time', // 兼职
  CONTRACT: 'contract', // 合同工
  INTERN: 'intern', // 实习生
  CONSULTANT: 'consultant' // 顾问
};

// 标签配置
export const USER_STATUS_LABELS = {
  [USER_STATUS.ACTIVE]: '活跃',
  [USER_STATUS.INACTIVE]: '非活跃',
  [USER_STATUS.SUSPENDED]: '暂停',
  [USER_STATUS.PENDING]: '待激活'
};

export const USER_ROLE_LABELS = {
  [USER_ROLE.ADMIN]: '管理员',
  [USER_ROLE.MANAGER]: '经理',
  [USER_ROLE.SUPERVISOR]: '主管',
  [USER_ROLE.ENGINEER]: '工程师',
  [USER_ROLE.TECHNICIAN]: '技术员',
  [USER_ROLE.SALESPERSON]: '销售员',
  [USER_ROLE.CUSTOMER_SERVICE]: '客服',
  [USER_ROLE.FINANCE]: '财务',
  [USER_ROLE.HR]: '人力资源',
  [USER_ROLE.OPERATIONS]: '运营'
};

export const USER_DEPARTMENT_LABELS = {
  [USER_DEPARTMENT.ENGINEERING]: '工程部',
  [USER_DEPARTMENT.SALES]: '销售部',
  [USER_DEPARTMENT.CUSTOMER_SERVICE]: '客服部',
  [USER_DEPARTMENT.FINANCE]: '财务部',
  [USER_DEPARTMENT.HR]: '人力资源部',
  [USER_DEPARTMENT.OPERATIONS]: '运营部',
  [USER_DEPARTMENT.MANAGEMENT]: '管理层',
  [USER_DEPARTMENT.IT]: 'IT部',
  [USER_DEPARTMENT.QUALITY]: '质量部',
  [USER_DEPARTMENT.MARKETING]: '市场部'
};

export const USER_PERMISSION_LABELS = {
  [USER_PERMISSION.USER_CREATE]: '创建用户',
  [USER_PERMISSION.USER_READ]: '查看用户',
  [USER_PERMISSION.USER_UPDATE]: '更新用户',
  [USER_PERMISSION.USER_DELETE]: '删除用户',
  [USER_PERMISSION.ROLE_CREATE]: '创建角色',
  [USER_PERMISSION.ROLE_READ]: '查看角色',
  [USER_PERMISSION.ROLE_UPDATE]: '更新角色',
  [USER_PERMISSION.ROLE_DELETE]: '删除角色',
  [USER_PERMISSION.PROJECT_CREATE]: '创建项目',
  [USER_PERMISSION.PROJECT_READ]: '查看项目',
  [USER_PERMISSION.PROJECT_UPDATE]: '更新项目',
  [USER_PERMISSION.PROJECT_DELETE]: '删除项目',
  [USER_PERMISSION.SYSTEM_CONFIG]: '系统配置',
  [USER_PERMISSION.DATA_EXPORT]: '数据导出',
  [USER_PERMISSION.REPORT_VIEW]: '查看报表',
  [USER_PERMISSION.ANALYTICS]: '数据分析'
};

export const USER_GENDER_LABELS = {
  [USER_GENDER.MALE]: '男性',
  [USER_GENDER.FEMALE]: '女性',
  [USER_GENDER.OTHER]: '其他'
};

export const EMPLOYMENT_TYPE_LABELS = {
  [EMPLOYMENT_TYPE.FULL_TIME]: '全职',
  [EMPLOYMENT_TYPE.PART_TIME]: '兼职',
  [EMPLOYMENT_TYPE.CONTRACT]: '合同工',
  [EMPLOYMENT_TYPE.INTERN]: '实习生',
  [EMPLOYMENT_TYPE.CONSULTANT]: '顾问'
};

// 状态颜色配置
export const USER_STATUS_COLORS = {
  [USER_STATUS.ACTIVE]: '#10B981', // 绿色
  [USER_STATUS.INACTIVE]: '#6B7280', // 灰色
  [USER_STATUS.SUSPENDED]: '#EF4444', // 红色
  [USER_STATUS.PENDING]: '#F59E0B' // 橙色
};

export const ROLE_COLORS = {
  [USER_ROLE.ADMIN]: '#DC2626', // 红色
  [USER_ROLE.MANAGER]: '#EA580C', // 橙色
  [USER_ROLE.SUPERVISOR]: '#CA8A04', // 黄色
  [USER_ROLE.ENGINEER]: '#16A34A', // 绿色
  [USER_ROLE.TECHNICIAN]: '#059669', // 深绿色
  [USER_ROLE.SALESPERSON]: '#0891B2', // 青色
  [USER_ROLE.CUSTOMER_SERVICE]: '#2563EB', // 蓝色
  [USER_ROLE.FINANCE]: '#7C3AED', // 紫色
  [USER_ROLE.HR]: '#DB2777', // 粉色
  [USER_ROLE.OPERATIONS]: '#64748B' // 灰蓝色
};

export const DEPARTMENT_COLORS = {
  [USER_DEPARTMENT.ENGINEERING]: '#059669',
  [USER_DEPARTMENT.SALES]: '#2563EB',
  [USER_DEPARTMENT.CUSTOMER_SERVICE]: '#7C3AED',
  [USER_DEPARTMENT.FINANCE]: '#DC2626',
  [USER_DEPARTMENT.HR]: '#DB2777',
  [USER_DEPARTMENT.OPERATIONS]: '#0891B2',
  [USER_DEPARTMENT.MANAGEMENT]: '#EA580C',
  [USER_DEPARTMENT.IT]: '#6366F1',
  [USER_DEPARTMENT.QUALITY]: '#CA8A04',
  [USER_DEPARTMENT.MARKETING]: '#EC4899'
};

// 统计配置
export const USER_STATS_CONFIG = {
  TOTAL_USERS: 'total_users',
  ACTIVE_USERS: 'active_users',
  INACTIVE_USERS: 'inactive_users',
  SUSPENDED_USERS: 'suspended_users',
  PENDING_USERS: 'pending_users',
  USERS_BY_ROLE: 'users_by_role',
  USERS_BY_DEPARTMENT: 'users_by_department',
  NEW_USERS_THIS_MONTH: 'new_users_this_month',
  USER_GROWTH_RATE: 'user_growth_rate'
};

// 默认角色权限配置
export const DEFAULT_ROLE_PERMISSIONS = {
  [USER_ROLE.ADMIN]: [
  USER_PERMISSION.USER_CREATE, USER_PERMISSION.USER_READ, USER_PERMISSION.USER_UPDATE, USER_PERMISSION.USER_DELETE,
  USER_PERMISSION.ROLE_CREATE, USER_PERMISSION.ROLE_READ, USER_PERMISSION.ROLE_UPDATE, USER_PERMISSION.ROLE_DELETE,
  USER_PERMISSION.PROJECT_CREATE, USER_PERMISSION.PROJECT_READ, USER_PERMISSION.PROJECT_UPDATE, USER_PERMISSION.PROJECT_DELETE,
  USER_PERMISSION.SYSTEM_CONFIG, USER_PERMISSION.DATA_EXPORT, USER_PERMISSION.REPORT_VIEW, USER_PERMISSION.ANALYTICS],

  [USER_ROLE.MANAGER]: [
  USER_PERMISSION.USER_READ, USER_PERMISSION.USER_UPDATE,
  USER_PERMISSION.ROLE_READ,
  USER_PERMISSION.PROJECT_CREATE, USER_PERMISSION.PROJECT_READ, USER_PERMISSION.PROJECT_UPDATE,
  USER_PERMISSION.DATA_EXPORT, USER_PERMISSION.REPORT_VIEW, USER_PERMISSION.ANALYTICS],

  [USER_ROLE.SUPERVISOR]: [
  USER_PERMISSION.USER_READ,
  USER_PERMISSION.PROJECT_READ, USER_PERMISSION.PROJECT_UPDATE,
  USER_PERMISSION.REPORT_VIEW],

  [USER_ROLE.ENGINEER]: [
  USER_PERMISSION.PROJECT_READ, USER_PERMISSION.PROJECT_UPDATE,
  USER_PERMISSION.REPORT_VIEW],

  [USER_ROLE.TECHNICIAN]: [
  USER_PERMISSION.PROJECT_READ, USER_PERMISSION.PROJECT_UPDATE],

  [USER_ROLE.SALESPERSON]: [
  USER_PERMISSION.PROJECT_CREATE, USER_PERMISSION.PROJECT_READ, USER_PERMISSION.PROJECT_UPDATE,
  USER_PERMISSION.REPORT_VIEW],

  [USER_ROLE.CUSTOMER_SERVICE]: [
  USER_PERMISSION.PROJECT_READ, USER_PERMISSION.PROJECT_UPDATE,
  USER_PERMISSION.REPORT_VIEW],

  [USER_ROLE.FINANCE]: [
  USER_PERMISSION.PROJECT_READ,
  USER_PERMISSION.DATA_EXPORT, USER_PERMISSION.REPORT_VIEW],

  [USER_ROLE.HR]: [
  USER_PERMISSION.USER_CREATE, USER_PERMISSION.USER_READ, USER_PERMISSION.USER_UPDATE,
  USER_PERMISSION.ROLE_READ,
  USER_PERMISSION.REPORT_VIEW],

  [USER_ROLE.OPERATIONS]: [
  USER_PERMISSION.PROJECT_READ, USER_PERMISSION.PROJECT_UPDATE,
  USER_PERMISSION.REPORT_VIEW, USER_PERMISSION.ANALYTICS]

};

// 工具函数
export const getUserStatusLabel = (status) => {
  return USER_STATUS_LABELS[status] || status;
};

export const getUserRoleLabel = (role) => {
  return USER_ROLE_LABELS[role] || role;
};

export const getUserDepartmentLabel = (department) => {
  return USER_DEPARTMENT_LABELS[department] || department;
};

export const getUserPermissionLabel = (permission) => {
  return USER_PERMISSION_LABELS[permission] || permission;
};

export const getUserGenderLabel = (gender) => {
  return USER_GENDER_LABELS[gender] || gender;
};

export const getEmploymentTypeLabel = (type) => {
  return EMPLOYMENT_TYPE_LABELS[type] || type;
};

export const getUserStatusColor = (status) => {
  return USER_STATUS_COLORS[status] || '#6B7280';
};

export const getRoleColor = (role) => {
  return ROLE_COLORS[role] || '#6B7280';
};

export const getDepartmentColor = (department) => {
  return DEPARTMENT_COLORS[department] || '#6B7280';
};

// 计算用户状态统计
export const getUserStatusStats = (users) => {
  const stats = {
    total: users.length,
    active: 0,
    inactive: 0,
    suspended: 0,
    pending: 0
  };

  users.forEach((user) => {
    switch (user.status) {
      case USER_STATUS.ACTIVE:
        stats.active++;
        break;
      case USER_STATUS.INACTIVE:
        stats.inactive++;
        break;
      case USER_STATUS.SUSPENDED:
        stats.suspended++;
        break;
      case USER_STATUS.PENDING:
        stats.pending++;
        break;
    }
  });

  return stats;
};

// 计算角色分布统计
export const getRoleDistributionStats = (users) => {
  const stats = {};

  Object.values(USER_ROLE).forEach((role) => {
    stats[role] = 0;
  });

  users.forEach((user) => {
    if (user.role) {
      stats[user.role] = (stats[user.role] || 0) + 1;
    }
  });

  return stats;
};

// 计算部门分布统计
export const getDepartmentDistributionStats = (users) => {
  const stats = {};

  Object.values(USER_DEPARTMENT).forEach((department) => {
    stats[department] = 0;
  });

  users.forEach((user) => {
    if (user.department) {
      stats[user.department] = (stats[user.department] || 0) + 1;
    }
  });

  return stats;
};

// 计算月度新用户统计
export const getMonthlyNewUsers = (users) => {
  const currentMonth = new Date().getMonth();
  const currentYear = new Date().getFullYear();

  return users.filter((user) => {
    const createdDate = new Date(user.created_at);
    return createdDate.getMonth() === currentMonth &&
    createdDate.getFullYear() === currentYear;
  }).length;
};

// 计算用户增长率
export const calculateUserGrowthRate = (currentUsers, previousUsers) => {
  if (previousUsers === 0) return currentUsers > 0 ? 100 : 0;
  return ((currentUsers - previousUsers) / previousUsers * 100).toFixed(1);
};

// 用户数据验证
export const validateUserData = (userData) => {
  const errors = [];

  if (!userData.username || userData.username.trim() === '') {
    errors.push('用户名不能为空');
  }

  if (!userData.email || userData.email.trim() === '') {
    errors.push('邮箱不能为空');
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userData.email)) {
    errors.push('邮箱格式不正确');
  }

  if (!userData.role) {
    errors.push('角色不能为空');
  }

  if (!userData.department) {
    errors.push('部门不能为空');
  }

  if (userData.phone && !/^[\d\s()+-]+$/.test(userData.phone)) {
    errors.push('电话格式不正确');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

// 检查用户权限
export const hasPermission = (userPermissions, requiredPermission) => {
  return userPermissions && userPermissions.includes(requiredPermission);
};

// 获取用户权限列表
export const getUserPermissions = (userRole) => {
  return DEFAULT_ROLE_PERMISSIONS[userRole] || [];
};

// 搜索和过滤配置
export const USER_STATUS_FILTER_OPTIONS = [
{ value: 'all', label: '全部状态' },
{ value: USER_STATUS.ACTIVE, label: '活跃' },
{ value: USER_STATUS.INACTIVE, label: '非活跃' },
{ value: USER_STATUS.SUSPENDED, label: '暂停' },
{ value: USER_STATUS.PENDING, label: '待激活' }];


export const ROLE_FILTER_OPTIONS = [
{ value: 'all', label: '全部角色' },
...Object.entries(USER_ROLE).map(([_key, value]) => ({
  value,
  label: USER_ROLE_LABELS[value]
}))];


export const DEPARTMENT_FILTER_OPTIONS = [
{ value: 'all', label: '全部部门' },
...Object.entries(USER_DEPARTMENT).map(([_key, value]) => ({
  value,
  label: USER_DEPARTMENT_LABELS[value]
}))];


// 默认配置
export const DEFAULT_USER_CONFIG = {
  status: USER_STATUS.ACTIVE,
  role: USER_ROLE.ENGINEER,
  department: USER_DEPARTMENT.ENGINEERING,
  gender: USER_GENDER.OTHER,
  employment_type: EMPLOYMENT_TYPE.FULL_TIME,
  permissions: []
};

export const DEFAULT_ROLE_CONFIG = {
  permissions: [],
  description: '',
  is_system_role: false
};
