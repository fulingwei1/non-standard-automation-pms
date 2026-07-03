// 安装派工管理业务配置
export const DISPATCH_STATUS = {
  PENDING: 'PENDING',           // 待派工
  ASSIGNED: 'ASSIGNED',         // 已派工
  IN_PROGRESS: 'IN_PROGRESS',   // 进行中
  COMPLETED: 'COMPLETED',       // 已完成
  CANCELLED: 'CANCELLED',       // 已取消
  DELAYED: 'DELAYED'            // 延期
};

export const DISPATCH_PRIORITY = {
  LOW: 'LOW',          // 低优先级
  NORMAL: 'NORMAL',    // 普通优先级
  MEDIUM: 'MEDIUM',    // 兼容旧数据
  HIGH: 'HIGH',        // 高优先级
  URGENT: 'URGENT'     // 紧急
};

export const TECHNICIAN_STATUS = {
  AVAILABLE: 'available',       // 可用
  BUSY: 'busy',                // 忙碌
  ON_LEAVE: 'on_leave',        // 休假
  UNAVAILABLE: 'unavailable'   // 不可用
};

export const INSTALLATION_TYPE = {
  INSTALLATION: 'INSTALLATION', // 安装
  DEBUGGING: 'DEBUGGING',       // 调试
  TRAINING: 'TRAINING',         // 培训
  MAINTENANCE: 'MAINTENANCE',   // 维护
  REPAIR: 'REPAIR',             // 维修
  OTHER: 'OTHER'                // 其他
};

export const WORK_TIME_PREFERENCE = {
  MORNING: 'morning',     // 上午
  AFTERNOON: 'afternoon', // 下午
  EVENING: 'evening',     // 晚上
  FLEXIBLE: 'flexible'   // 灵活
};

export const DISPATCH_STATUS_LABELS = {
  [DISPATCH_STATUS.PENDING]: '待派工',
  [DISPATCH_STATUS.ASSIGNED]: '已派工',
  [DISPATCH_STATUS.IN_PROGRESS]: '进行中',
  [DISPATCH_STATUS.COMPLETED]: '已完成',
  [DISPATCH_STATUS.CANCELLED]: '已取消',
  [DISPATCH_STATUS.DELAYED]: '延期'
};

export const DISPATCH_PRIORITY_LABELS = {
  [DISPATCH_PRIORITY.LOW]: '低优先级',
  [DISPATCH_PRIORITY.NORMAL]: '普通优先级',
  [DISPATCH_PRIORITY.MEDIUM]: '中优先级',
  [DISPATCH_PRIORITY.HIGH]: '高优先级',
  [DISPATCH_PRIORITY.URGENT]: '紧急'
};

export const TECHNICIAN_STATUS_LABELS = {
  [TECHNICIAN_STATUS.AVAILABLE]: '可用',
  [TECHNICIAN_STATUS.BUSY]: '忙碌',
  [TECHNICIAN_STATUS.ON_LEAVE]: '休假',
  [TECHNICIAN_STATUS.UNAVAILABLE]: '不可用'
};

export const INSTALLATION_TYPE_LABELS = {
  [INSTALLATION_TYPE.INSTALLATION]: '安装',
  [INSTALLATION_TYPE.DEBUGGING]: '调试',
  [INSTALLATION_TYPE.TRAINING]: '培训',
  [INSTALLATION_TYPE.MAINTENANCE]: '维护',
  [INSTALLATION_TYPE.REPAIR]: '维修',
  [INSTALLATION_TYPE.OTHER]: '其他'
};

export const WORK_TIME_PREFERENCE_LABELS = {
  [WORK_TIME_PREFERENCE.MORNING]: '上午',
  [WORK_TIME_PREFERENCE.AFTERNOON]: '下午',
  [WORK_TIME_PREFERENCE.EVENING]: '晚上',
  [WORK_TIME_PREFERENCE.FLEXIBLE]: '灵活'
};

// 状态颜色配置
export const DISPATCH_STATUS_COLORS = {
  [DISPATCH_STATUS.PENDING]: '#8B5CF6',    // 紫色
  [DISPATCH_STATUS.ASSIGNED]: '#3B82F6',   // 蓝色
  [DISPATCH_STATUS.IN_PROGRESS]: '#F59E0B', // 橙色
  [DISPATCH_STATUS.COMPLETED]: '#10B981',   // 绿色
  [DISPATCH_STATUS.CANCELLED]: '#EF4444',   // 红色
  [DISPATCH_STATUS.DELAYED]: '#F97316'     // 深橙色
};

export const PRIORITY_COLORS = {
  [DISPATCH_PRIORITY.LOW]: '#10B981',    // 绿色
  [DISPATCH_PRIORITY.NORMAL]: '#6B7280', // 灰色
  [DISPATCH_PRIORITY.MEDIUM]: '#F59E0B', // 橙色
  [DISPATCH_PRIORITY.HIGH]: '#EF4444',   // 红色
  [DISPATCH_PRIORITY.URGENT]: '#DC2626'  // 深红
};

export const TECHNICIAN_STATUS_COLORS = {
  [TECHNICIAN_STATUS.AVAILABLE]: '#10B981',   // 绿色
  [TECHNICIAN_STATUS.BUSY]: '#F59E0B',        // 橙色
  [TECHNICIAN_STATUS.ON_LEAVE]: '#6B7280',    // 灰色
  [TECHNICIAN_STATUS.UNAVAILABLE]: '#EF4444'  // 红色
};

// 派工统计配置
export const DISPATCH_STATS_CONFIG = {
  TOTAL_DISPATCHES: 'total_dispatches',
  PENDING_DISPATCHES: 'pending_dispatches',
  IN_PROGRESS_DISPATCHES: 'in_progress_dispatches',
  COMPLETED_DISPATCHES: 'completed_dispatches',
  DELAYED_DISPATCHES: 'delayed_dispatches',
  AVAILABLE_TECHNICIANS: 'available_technicians'
};

// 技术人员技能配置
export const TECHNICIAN_SKILLS = {
  ELECTRICAL: 'electrical',     // 电工
  MECHANICAL: 'mechanical',     // 机械
  PLUMBING: 'plumbing',         // 管道
  HVAC: 'hvac',                // 暖通空调
  NETWORKING: 'networking',     // 网络
  SOFTWARE: 'software'          // 软件
};

export const TECHNICIAN_SKILL_LABELS = {
  [TECHNICIAN_SKILLS.ELECTRICAL]: '电工',
  [TECHNICIAN_SKILLS.MECHANICAL]: '机械',
  [TECHNICIAN_SKILLS.PLUMBING]: '管道',
  [TECHNICIAN_SKILLS.HVAC]: '暖通空调',
  [TECHNICIAN_SKILLS.NETWORKING]: '网络',
  [TECHNICIAN_SKILLS.SOFTWARE]: '软件'
};

// 工具函数
const upper = (value) => String(value || "").trim().toUpperCase();

export const normalizeDispatchStatus = (status) => {
  const value = upper(status);
  return (
    {
      PENDING: DISPATCH_STATUS.PENDING,
      ASSIGNED: DISPATCH_STATUS.ASSIGNED,
      APPROVED: DISPATCH_STATUS.ASSIGNED,
      IN_PROGRESS: DISPATCH_STATUS.IN_PROGRESS,
      COMPLETED: DISPATCH_STATUS.COMPLETED,
      CANCELLED: DISPATCH_STATUS.CANCELLED,
      CANCELED: DISPATCH_STATUS.CANCELLED,
      DELAYED: DISPATCH_STATUS.DELAYED,
    }[value] || value
  );
};

export const normalizeDispatchPriority = (priority) => {
  const value = upper(priority);
  return (
    {
      LOW: DISPATCH_PRIORITY.LOW,
      NORMAL: DISPATCH_PRIORITY.NORMAL,
      MEDIUM: DISPATCH_PRIORITY.MEDIUM,
      HIGH: DISPATCH_PRIORITY.HIGH,
      CRITICAL: DISPATCH_PRIORITY.URGENT,
      URGENT: DISPATCH_PRIORITY.URGENT,
    }[value] || value
  );
};

export const normalizeInstallationType = (type) => {
  const value = upper(type);
  return (
    {
      NEW: INSTALLATION_TYPE.INSTALLATION,
      INSTALL: INSTALLATION_TYPE.INSTALLATION,
      INSTALLATION: INSTALLATION_TYPE.INSTALLATION,
      DEBUG: INSTALLATION_TYPE.DEBUGGING,
      DEBUGGING: INSTALLATION_TYPE.DEBUGGING,
      TRAINING: INSTALLATION_TYPE.TRAINING,
      MAINTENANCE: INSTALLATION_TYPE.MAINTENANCE,
      REPAIR: INSTALLATION_TYPE.REPAIR,
      AUTO: INSTALLATION_TYPE.DEBUGGING,
      MANUAL: INSTALLATION_TYPE.INSTALLATION,
      NORMAL: INSTALLATION_TYPE.OTHER,
      OTHER: INSTALLATION_TYPE.OTHER,
    }[value] || value
  );
};

export const normalizeDispatchOrder = (order = {}) => {
  const project = order.project || {};
  const machine = order.machine || {};
  const assignedTo = order.assigned_to || {};

  return {
    ...order,
    order_no: order.order_no || order.order_number || "",
    project_name: order.project_name || project.project_name || project.name || "",
    machine_name:
      order.machine_name ||
      machine.machine_name ||
      machine.name ||
      order.machine_no ||
      "",
    assigned_to_name:
      order.assigned_to_name ||
      assignedTo.name ||
      assignedTo.real_name ||
      "",
    status: normalizeDispatchStatus(order.status),
    priority: normalizeDispatchPriority(order.priority),
    task_type: normalizeInstallationType(order.task_type),
    scheduled_date: order.scheduled_date || order.scheduledDate || "",
  };
};

export const getDispatchStatusLabel = (status) => {
  const normalized = normalizeDispatchStatus(status);
  return DISPATCH_STATUS_LABELS[normalized] || status;
};

export const getDispatchPriorityLabel = (priority) => {
  const normalized = normalizeDispatchPriority(priority);
  return DISPATCH_PRIORITY_LABELS[normalized] || priority;
};

export const getTechnicianStatusLabel = (status) => {
  return TECHNICIAN_STATUS_LABELS[status] || status;
};

export const getInstallationTypeLabel = (type) => {
  const normalized = normalizeInstallationType(type);
  return INSTALLATION_TYPE_LABELS[normalized] || type;
};

export const getWorkTimePreferenceLabel = (preference) => {
  return WORK_TIME_PREFERENCE_LABELS[preference] || preference;
};

export const getDispatchStatusColor = (status) => {
  return DISPATCH_STATUS_COLORS[normalizeDispatchStatus(status)] || '#6B7280';
};

export const getPriorityColor = (priority) => {
  return PRIORITY_COLORS[normalizeDispatchPriority(priority)] || '#6B7280';
};

export const getTechnicianStatusColor = (status) => {
  return TECHNICIAN_STATUS_COLORS[status] || '#6B7280';
};

// 计算派工完成率
export const calculateCompletionRate = (completed, total) => {
  if (total === 0) {return 0;}
  return ((completed / total) * 100).toFixed(1);
};

// 计算延期率
export const calculateDelayRate = (delayed, total) => {
  if (total === 0) {return 0;}
  return ((delayed / total) * 100).toFixed(1);
};

// 获取派工状态统计
export const getDispatchStatusStats = (dispatches) => {
  const stats = {
    total: dispatches.length,
    pending: 0,
    assigned: 0,
    inProgress: 0,
    completed: 0,
    cancelled: 0,
    delayed: 0
  };

  dispatches.forEach(dispatch => {
    switch (normalizeDispatchStatus(dispatch.status)) {
      case DISPATCH_STATUS.PENDING:
        stats.pending++;
        break;
      case DISPATCH_STATUS.ASSIGNED:
        stats.assigned++;
        break;
      case DISPATCH_STATUS.IN_PROGRESS:
        stats.inProgress++;
        break;
      case DISPATCH_STATUS.COMPLETED:
        stats.completed++;
        break;
      case DISPATCH_STATUS.CANCELLED:
        stats.cancelled++;
        break;
      case DISPATCH_STATUS.DELAYED:
        stats.delayed++;
        break;
    }
  });

  return stats;
};

// 获取技术人员状态统计
export const getTechnicianStatusStats = (technicians) => {
  const stats = {
    total: technicians.length,
    available: 0,
    busy: 0,
    onLeave: 0,
    unavailable: 0
  };

  technicians.forEach(technician => {
    switch (technician.status) {
      case TECHNICIAN_STATUS.AVAILABLE:
        stats.available++;
        break;
      case TECHNICIAN_STATUS.BUSY:
        stats.busy++;
        break;
      case TECHNICIAN_STATUS.ON_LEAVE:
        stats.onLeave++;
        break;
      case TECHNICIAN_STATUS.UNAVAILABLE:
        stats.unavailable++;
        break;
    }
  });

  return stats;
};

// 计算技术人员工作负载
export const calculateTechnicianWorkload = (assignedTasks, maxTasks = 5) => {
  if (!assignedTasks) {return 0;}
  const workload = (assignedTasks.length / maxTasks) * 100;
  return Math.min(workload, 100);
};

// 获取最佳匹配技术人员
export const getBestMatchTechnician = (technicians, requiredSkills, currentWorkload = {}) => {
  return technicians
    .filter(tech => tech.status === TECHNICIAN_STATUS.AVAILABLE)
    .map(tech => ({
      ...tech,
      skillMatch: calculateSkillMatch(tech.skills || [], requiredSkills),
      workload: currentWorkload[tech.id] || 0
    }))
    .sort((a, b) => {
      // 优先匹配技能，其次考虑工作负载
      if (b.skillMatch !== a.skillMatch) {
        return b.skillMatch - a.skillMatch;
      }
      return a.workload - b.workload;
    })[0];
};

// 计算技能匹配度
export const calculateSkillMatch = (technicianSkills, requiredSkills) => {
  if (!requiredSkills || requiredSkills.length === 0) {return 100;}
  
  const matchedSkills = technicianSkills.filter(skill => 
    requiredSkills.includes(skill)
  ).length;
  
  return (matchedSkills / requiredSkills.length) * 100;
};

// 派工验证
export const validateDispatchData = (dispatchData) => {
  const errors = [];
  
  if (!dispatchData.project_id) {
    errors.push('项目ID不能为空');
  }
  
  if (!dispatchData.customer_id) {
    errors.push('客户ID不能为空');
  }
  
  if (!dispatchData.task_type) {
    errors.push('安装类型不能为空');
  }

  if (!dispatchData.task_title) {
    errors.push('任务标题不能为空');
  }
  
  if (!dispatchData.scheduled_date) {
    errors.push('计划日期不能为空');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

// 搜索和过滤配置
export const DISPATCH_FILTER_OPTIONS = [
  { value: 'all', label: '全部' },
  { value: DISPATCH_STATUS.PENDING, label: '待派工' },
  { value: DISPATCH_STATUS.ASSIGNED, label: '已派工' },
  { value: DISPATCH_STATUS.IN_PROGRESS, label: '进行中' },
  { value: DISPATCH_STATUS.COMPLETED, label: '已完成' },
  { value: DISPATCH_STATUS.CANCELLED, label: '已取消' },
  { value: DISPATCH_STATUS.DELAYED, label: '延期' }
];

export const PRIORITY_FILTER_OPTIONS = [
  { value: 'all', label: '全部优先级' },
  { value: DISPATCH_PRIORITY.URGENT, label: '紧急' },
  { value: DISPATCH_PRIORITY.HIGH, label: '高优先级' },
  { value: DISPATCH_PRIORITY.NORMAL, label: '普通优先级' },
  { value: DISPATCH_PRIORITY.MEDIUM, label: '中优先级' },
  { value: DISPATCH_PRIORITY.LOW, label: '低优先级' }
];

export const TECHNICIAN_FILTER_OPTIONS = [
  { value: 'all', label: '全部状态' },
  { value: TECHNICIAN_STATUS.AVAILABLE, label: '可用' },
  { value: TECHNICIAN_STATUS.BUSY, label: '忙碌' },
  { value: TECHNICIAN_STATUS.ON_LEAVE, label: '休假' },
  { value: TECHNICIAN_STATUS.UNAVAILABLE, label: '不可用' }
];

// 默认配置
export const DEFAULT_DISPATCH_CONFIG = {
  status: DISPATCH_STATUS.PENDING,
  priority: DISPATCH_PRIORITY.NORMAL,
  estimatedDuration: 4, // 小时
  maxDelay: 30 // 分钟
};

export const DEFAULT_TECHNICIAN_CONFIG = {
  status: TECHNICIAN_STATUS.AVAILABLE,
  maxTasksPerDay: 5,
  skillLevel: 'intermediate'
};
