/**
 * HR Configuration Constants
 * 人力资源配置常量
 */

// 员工状态配置
export const employeeStatusConfigs = {
  ACTIVE: { label: "在职", color: "bg-green-500", textColor: "text-green-50", icon: "✅" },
  INACTIVE: { label: "离职", color: "bg-red-500", textColor: "text-red-50", icon: "❌" },
  SUSPENDED: { label: "停职", color: "bg-orange-500", textColor: "text-orange-50", icon: "⏸️" },
  ON_LEAVE: { label: "休假", color: "bg-blue-500", textColor: "text-blue-50", icon: "🏖️" },
  PENDING: { label: "待入职", color: "bg-yellow-500", textColor: "text-yellow-50", icon: "⏳" },
  TERMINATED: { label: "终止", color: "bg-gray-500", textColor: "text-gray-50", icon: "🛑" },
};

// 员工类型配置
export const employeeTypeConfigs = {
  FULL_TIME: { label: "全职", color: "bg-blue-500", textColor: "text-blue-50" },
  PART_TIME: { label: "兼职", color: "bg-purple-500", textColor: "text-purple-50" },
  INTERN: { label: "实习", color: "bg-green-500", textColor: "text-green-50" },
  CONTRACTOR: { label: "外包", color: "bg-orange-500", textColor: "text-orange-50" },
  TEMPORARY: { label: "临时", color: "bg-gray-500", textColor: "text-gray-50" },
};

// 部门配置
export const departmentConfigs = {
  MANAGEMENT: { label: "管理层", color: "bg-purple-500", textColor: "text-purple-50", icon: "👔" },
  HR: { label: "人事部", color: "bg-blue-500", textColor: "text-blue-50", icon: "👥" },
  ENGINEERING: { label: "工程部", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "⚙️" },
  PRODUCTION: { label: "生产部", color: "bg-green-500", textColor: "text-green-50", icon: "🏭" },
  QUALITY: { label: "质量部", color: "bg-red-500", textColor: "text-red-50", icon: "🔍" },
  SALES: { label: "销售部", color: "bg-orange-500", textColor: "text-orange-50", icon: "💼" },
  MARKETING: { label: "市场部", color: "bg-pink-500", textColor: "text-pink-50", icon: "📢" },
  FINANCE: { label: "财务部", color: "bg-yellow-500", textColor: "text-yellow-50", icon: "💰" },
  IT: { label: "IT部", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "💻" },
  ADMIN: { label: "行政部", color: "bg-gray-500", textColor: "text-gray-50", icon: "📋" },
  PURCHASING: { label: "采购部", color: "bg-teal-500", textColor: "text-teal-50", icon: "🛒" },
  LOGISTICS: { label: "物流部", color: "bg-lime-500", textColor: "text-lime-50", icon: "🚚" },
};

// 职位级别配置
export const positionLevelConfigs = {
  CEO: { label: "CEO", level: 1, color: "bg-purple-600", textColor: "text-purple-50" },
  VICE_PRESIDENT: { label: "副总裁", level: 2, color: "bg-purple-500", textColor: "text-purple-50" },
  DIRECTOR: { label: "总监", level: 3, color: "bg-purple-400", textColor: "text-purple-50" },
  MANAGER: { label: "经理", level: 4, color: "bg-blue-500", textColor: "text-blue-50" },
  SUPERVISOR: { label: "主管", level: 5, color: "bg-blue-400", textColor: "text-blue-50" },
  SENIOR: { label: "高级", level: 6, color: "bg-green-500", textColor: "text-green-50" },
  INTERMEDIATE: { label: "中级", level: 7, color: "bg-yellow-500", textColor: "text-yellow-50" },
  JUNIOR: { label: "初级", level: 8, color: "bg-orange-500", textColor: "text-orange-50" },
  TRAINEE: { label: "培训生", level: 9, color: "bg-gray-500", textColor: "text-gray-50" },
};

// 考勤状态配置
export const attendanceStatusConfigs = {
  PRESENT: { label: "出勤", color: "bg-green-500", textColor: "text-green-50", icon: "✓" },
  ABSENT: { label: "缺勤", color: "bg-red-500", textColor: "text-red-50", icon: "✗" },
  LATE: { label: "迟到", color: "bg-orange-500", textColor: "text-orange-50", icon: "⏰" },
  EARLY_LEAVE: { label: "早退", color: "bg-yellow-500", textColor: "text-yellow-50", icon: "🏃" },
  SICK_LEAVE: { label: "病假", color: "bg-blue-500", textColor: "text-blue-50", icon: "🏥" },
  ANNUAL_LEAVE: { label: "年假", color: "bg-purple-500", textColor: "text-purple-50", icon: "🏖️" },
  PERSONAL_LEAVE: { label: "事假", color: "bg-gray-500", textColor: "text-gray-50", icon: "📝" },
  BUSINESS_TRIP: { label: "出差", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "✈️" },
};

// 绩效等级配置
export const performanceGradeConfigs = {
  EXCELLENT: { 
    label: "优秀", 
    color: "bg-green-500", 
    textColor: "text-green-50", 
    score: "90-100",
    description: "表现卓越，超出预期"
  },
  GOOD: { 
    label: "良好", 
    color: "bg-blue-500", 
    textColor: "text-blue-50", 
    score: "80-89",
    description: "表现良好，达到预期"
  },
  AVERAGE: { 
    label: "合格", 
    color: "bg-yellow-500", 
    textColor: "text-yellow-50", 
    score: "70-79",
    description: "基本达到要求"
  },
  NEEDS_IMPROVEMENT: { 
    label: "需改进", 
    color: "bg-orange-500", 
    textColor: "text-orange-50", 
    score: "60-69",
    description: "需要改进和提高"
  },
  POOR: { 
    label: "不合格", 
    color: "bg-red-500", 
    textColor: "text-red-50", 
    score: "0-59",
    description: "未达到基本要求"
  },
};

// 薪资类型配置
export const salaryTypeConfigs = {
  BASE: { label: "基本工资", color: "bg-blue-500", textColor: "text-blue-50" },
  PERFORMANCE: { label: "绩效奖金", color: "bg-green-500", textColor: "text-green-50" },
  OVERTIME: { label: "加班费", color: "bg-orange-500", textColor: "text-orange-50" },
  BONUS: { label: "奖金", color: "bg-purple-500", textColor: "text-purple-50" },
  ALLOWANCE: { label: "津贴", color: "bg-yellow-500", textColor: "text-yellow-50" },
  DEDUCTION: { label: "扣除", color: "bg-red-500", textColor: "text-red-50" },
};

// 合同类型配置
export const contractTypeConfigs = {
  PERMANENT: { label: "永久合同", color: "bg-green-500", textColor: "text-green-50", duration: "长期" },
  FIXED_TERM: { label: "固定期限", color: "bg-blue-500", textColor: "text-blue-50", duration: "1-3年" },
  PROJECT_BASED: { label: "项目合同", color: "bg-purple-500", textColor: "text-purple-50", duration: "项目期间" },
  PART_TIME: { label: "兼职合同", color: "bg-orange-500", textColor: "text-orange-50", duration: "灵活" },
  INTERNSHIP: { label: "实习协议", color: "bg-gray-500", textColor: "text-gray-50", duration: "3-12个月" },
  CONSULTANT: { label: "咨询合同", color: "bg-indigo-500", textColor: "text-indigo-50", duration: "项目期间" },
};

// 培训类型配置
export const trainingTypeConfigs = {
  ONBOARDING: { label: "入职培训", color: "bg-blue-500", textColor: "text-blue-50", icon: "🎓" },
  SKILLS: { label: "技能培训", color: "bg-green-500", textColor: "text-green-50", icon: "🔧" },
  COMPLIANCE: { label: "合规培训", color: "bg-red-500", textColor: "text-red-50", icon: "⚖️" },
  LEADERSHIP: { label: "管理培训", color: "bg-purple-500", textColor: "text-purple-50", icon: "👑" },
  SAFETY: { label: "安全培训", color: "bg-orange-500", textColor: "text-orange-50", icon: "🛡️" },
  PRODUCT: { label: "产品培训", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "📦" },
  SOFT_SKILLS: { label: "软技能", color: "bg-pink-500", textColor: "text-pink-50", icon: "💬" },
  TECHNICAL: { label: "技术培训", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "💻" },
};

// 招聘状态配置
export const recruitmentStatusConfigs = {
  DRAFT: { label: "草稿", color: "bg-gray-500", textColor: "text-gray-50" },
  POSTED: { label: "已发布", color: "bg-blue-500", textColor: "text-blue-50" },
  SCREENING: { label: "筛选中", color: "bg-yellow-500", textColor: "text-yellow-50" },
  INTERVIEWING: { label: "面试中", color: "bg-orange-500", textColor: "text-orange-50" },
  OFFERED: { label: "已发offer", color: "bg-purple-500", textColor: "text-purple-50" },
  ACCEPTED: { label: "已接受", color: "bg-green-500", textColor: "text-green-50" },
  REJECTED: { label: "已拒绝", color: "bg-red-500", textColor: "text-red-50" },
  CLOSED: { label: "已关闭", color: "bg-gray-600", textColor: "text-gray-50" },
};

// HR Tab 配置
export const hrTabConfigs = [
  { value: "overview", label: "概览", icon: "📊" },
  { value: "transactions", label: "人事事务", icon: "📝" },
  { value: "contracts", label: "合同管理", icon: "📄" },
  { value: "recruitment", label: "招聘管理", icon: "👥" },
  { value: "performance", label: "绩效管理", icon: "🎯" },
  { value: "attendance", label: "考勤管理", icon: "⏰" },
  { value: "employees", label: "员工管理", icon: "👤" },
  { value: "relations", label: "员工关系", icon: "💝" },
  { value: "statistics", label: "统计分析", icon: "📈" },
];

// 工具函数
export const getEmployeeStatusConfig = (status) => {
  return employeeStatusConfigs[status] || employeeStatusConfigs.ACTIVE;
};

export const getDepartmentConfig = (department) => {
  return departmentConfigs[department] || departmentConfigs.ADMIN;
};

export const getPositionLevelConfig = (level) => {
  return positionLevelConfigs[level] || positionLevelConfigs.TRAINEE;
};

export const getAttendanceStatusConfig = (status) => {
  return attendanceStatusConfigs[status] || attendanceStatusConfigs.PRESENT;
};

export const getPerformanceGradeConfig = (grade) => {
  return performanceGradeConfigs[grade] || performanceGradeConfigs.AVERAGE;
};

export const getContractTypeConfig = (type) => {
  return contractTypeConfigs[type] || contractTypeConfigs.FIXED_TERM;
};

export const getRecruitmentStatusConfig = (status) => {
  return recruitmentStatusConfigs[status] || recruitmentStatusConfigs.DRAFT;
};

// 格式化函数
export const formatEmployeeStatus = (status) => {
  return getEmployeeStatusConfig(status).label;
};

export const formatDepartment = (department) => {
  return getDepartmentConfig(department).label;
};

export const formatPositionLevel = (level) => {
  return getPositionLevelConfig(level).label;
};

export const formatAttendanceStatus = (status) => {
  return getAttendanceStatusConfig(status).label;
};

export const formatPerformanceGrade = (grade) => {
  return getPerformanceGradeConfig(grade).label;
};

// 排序函数
export const sortByPositionLevel = (a, b) => {
  const levelA = getPositionLevelConfig(a.position_level)?.level || 999;
  const levelB = getPositionLevelConfig(b.position_level)?.level || 999;
  return levelA - levelB;
};

export const sortByPerformanceScore = (a, b) => {
  return (b.performance_score || 0) - (a.performance_score || 0);
};

// 验证函数
export const isValidEmployeeStatus = (status) => {
  return Object.keys(employeeStatusConfigs).includes(status);
};

export const isValidDepartment = (department) => {
  return Object.keys(departmentConfigs).includes(department);
};

export const isValidPerformanceGrade = (grade) => {
  return Object.keys(performanceGradeConfigs).includes(grade);
};

// 过滤函数
export const filterByEmployeeStatus = (employees, status) => {
  return employees.filter(employee => employee.status === status);
};

export const filterByDepartment = (employees, department) => {
  return employees.filter(employee => employee.department === department);
};

export const filterByPositionLevel = (employees, level) => {
  return employees.filter(employee => employee.position_level === level);
};

export default {
  employeeStatusConfigs,
  employeeTypeConfigs,
  departmentConfigs,
  positionLevelConfigs,
  attendanceStatusConfigs,
  performanceGradeConfigs,
  salaryTypeConfigs,
  contractTypeConfigs,
  trainingTypeConfigs,
  recruitmentStatusConfigs,
  hrTabConfigs,
  getEmployeeStatusConfig,
  getDepartmentConfig,
  getPositionLevelConfig,
  getAttendanceStatusConfig,
  getPerformanceGradeConfig,
  getContractTypeConfig,
  getRecruitmentStatusConfig,
  formatEmployeeStatus,
  formatDepartment,
  formatPositionLevel,
  formatAttendanceStatus,
  formatPerformanceGrade,
  sortByPositionLevel,
  sortByPerformanceScore,
  isValidEmployeeStatus,
  isValidDepartment,
  isValidPerformanceGrade,
  filterByEmployeeStatus,
  filterByDepartment,
  filterByPositionLevel,
};