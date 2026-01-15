// 客户沟通管理业务配置
export const COMMUNICATION_TYPE = {
  PHONE: 'phone',           // 电话
  EMAIL: 'email',          // 邮件
  ON_SITE: 'on_site',      // 现场
  WECHAT: 'wechat',        // 微信
  MEETING: 'meeting',      // 会议
  VIDEO_CALL: 'video_call' // 视频通话
};

export const COMMUNICATION_PRIORITY = {
  HIGH: 'high',        // 高优先级
  MEDIUM: 'medium',    // 中优先级
  LOW: 'low'          // 低优先级
};

export const COMMUNICATION_STATUS = {
  PENDING: 'pending',         // 待处理
  IN_PROGRESS: 'in_progress', // 进行中
  COMPLETED: 'completed',     // 已完成
  FOLLOW_UP: 'follow_up'     // 需要跟进
};

export const COMMUNICATION_TOPIC = {
  SALES: 'sales',           // 销售
  SUPPORT: 'support',       // 技术支持
  COMPLAINT: 'complaint',    // 投诉
  CONSULTATION: 'consultation', // 咨询
  FEEDBACK: 'feedback',     // 反馈
  TRAINING: 'training',     // 培训
  MAINTENANCE: 'maintenance', // 维护
  OTHER: 'other'           // 其他
};

export const CUSTOMER_SATISFACTION = {
  VERY_SATISFIED: 5,    // 非常满意
  SATISFIED: 4,         // 满意
  NEUTRAL: 3,          // 一般
  DISSATISFIED: 2,     // 不满意
  VERY_DISSATISFIED: 1 // 非常不满意
};

export const FOLLOW_UP_PRIORITY = {
  URGENT: 'urgent',      // 紧急
  HIGH: 'high',         // 高
  MEDIUM: 'medium',     // 中
  LOW: 'low'           // 低
};

export const COMMUNICATION_TYPE_LABELS = {
  [COMMUNICATION_TYPE.PHONE]: '电话',
  [COMMUNICATION_TYPE.EMAIL]: '邮件',
  [COMMUNICATION_TYPE.ON_SITE]: '现场',
  [COMMUNICATION_TYPE.WECHAT]: '微信',
  [COMMUNICATION_TYPE.MEETING]: '会议',
  [COMMUNICATION_TYPE.VIDEO_CALL]: '视频通话'
};

export const COMMUNICATION_PRIORITY_LABELS = {
  [COMMUNICATION_PRIORITY.HIGH]: '高优先级',
  [COMMUNICATION_PRIORITY.MEDIUM]: '中优先级',
  [COMMUNICATION_PRIORITY.LOW]: '低优先级'
};

export const COMMUNICATION_STATUS_LABELS = {
  [COMMUNICATION_STATUS.PENDING]: '待处理',
  [COMMUNICATION_STATUS.IN_PROGRESS]: '进行中',
  [COMMUNICATION_STATUS.COMPLETED]: '已完成',
  [COMMUNICATION_STATUS.FOLLOW_UP]: '需要跟进'
};

export const COMMUNICATION_TOPIC_LABELS = {
  [COMMUNICATION_TOPIC.SALES]: '销售',
  [COMMUNICATION_TOPIC.SUPPORT]: '技术支持',
  [COMMUNICATION_TOPIC.COMPLAINT]: '投诉',
  [COMMUNICATION_TOPIC.CONSULTATION]: '咨询',
  [COMMUNICATION_TOPIC.FEEDBACK]: '反馈',
  [COMMUNICATION_TOPIC.TRAINING]: '培训',
  [COMMUNICATION_TOPIC.MAINTENANCE]: '维护',
  [COMMUNICATION_TOPIC.OTHER]: '其他'
};

export const CUSTOMER_SATISFACTION_LABELS = {
  [CUSTOMER_SATISFACTION.VERY_SATISFIED]: '非常满意',
  [CUSTOMER_SATISFACTION.SATISFIED]: '满意',
  [CUSTOMER_SATISFACTION.NEUTRAL]: '一般',
  [CUSTOMER_SATISFACTION.DISSATISFIED]: '不满意',
  [CUSTOMER_SATISFACTION.VERY_DISSATISFIED]: '非常不满意'
};

export const FOLLOW_UP_PRIORITY_LABELS = {
  [FOLLOW_UP_PRIORITY.URGENT]: '紧急',
  [FOLLOW_UP_PRIORITY.HIGH]: '高',
  [FOLLOW_UP_PRIORITY.MEDIUM]: '中',
  [FOLLOW_UP_PRIORITY.LOW]: '低'
};

// 沟通类型图标配置
export const COMMUNICATION_TYPE_ICONS = {
  [COMMUNICATION_TYPE.PHONE]: '📞',
  [COMMUNICATION_TYPE.EMAIL]: '📧',
  [COMMUNICATION_TYPE.ON_SITE]: '🏢',
  [COMMUNICATION_TYPE.WECHAT]: '💬',
  [COMMUNICATION_TYPE.MEETING]: '👥',
  [COMMUNICATION_TYPE.VIDEO_CALL]: '📹'
};

// 状态颜色配置
export const COMMUNICATION_STATUS_COLORS = {
  [COMMUNICATION_STATUS.PENDING]: '#8B5CF6',    // 紫色
  [COMMUNICATION_STATUS.IN_PROGRESS]: '#F59E0B', // 橙色
  [COMMUNICATION_STATUS.COMPLETED]: '#10B981',   // 绿色
  [COMMUNICATION_STATUS.FOLLOW_UP]: '#3B82F6'   // 蓝色
};

export const PRIORITY_COLORS = {
  [COMMUNICATION_PRIORITY.HIGH]: '#EF4444',   // 红色
  [COMMUNICATION_PRIORITY.MEDIUM]: '#F59E0B', // 橙色
  [COMMUNICATION_PRIORITY.LOW]: '#10B981'     // 绿色
};

export const TOPIC_COLORS = {
  [COMMUNICATION_TOPIC.SALES]: '#3B82F6',        // 蓝色
  [COMMUNICATION_TOPIC.SUPPORT]: '#10B981',      // 绿色
  [COMMUNICATION_TOPIC.COMPLAINT]: '#EF4444',     // 红色
  [COMMUNICATION_TOPIC.CONSULTATION]: '#8B5CF6',  // 紫色
  [COMMUNICATION_TOPIC.FEEDBACK]: '#F59E0B',      // 橙色
  [COMMUNICATION_TOPIC.TRAINING]: '#06B6D4',       // 青色
  [COMMUNICATION_TOPIC.MAINTENANCE]: '#6B7280',    // 灰色
  [COMMUNICATION_TOPIC.OTHER]: '#EC4899'          // 粉色
};

export const SATISFACTION_COLORS = {
  [CUSTOMER_SATISFACTION.VERY_SATISFIED]: '#10B981', // 绿色
  [CUSTOMER_SATISFACTION.SATISFIED]: '#22C55E',     // 浅绿色
  [CUSTOMER_SATISFACTION.NEUTRAL]: '#F59E0B',       // 橙色
  [CUSTOMER_SATISFACTION.DISSATISFIED]: '#F97316',  // 深橙色
  [CUSTOMER_SATISFACTION.VERY_DISSATISFIED]: '#EF4444' // 红色
};

// 统计配置
export const COMMUNICATION_STATS_CONFIG = {
  TOTAL_COMMUNICATIONS: 'total_communications',
  PENDING_COMMUNICATIONS: 'pending_communications',
  IN_PROGRESS_COMMUNICATIONS: 'in_progress_communications',
  COMPLETED_COMMUNICATIONS: 'completed_communications',
  FOLLOW_UP_COMMUNICATIONS: 'follow_up_communications',
  AVERAGE_SATISFACTION: 'average_satisfaction',
  RESPONSE_RATE: 'response_rate'
};

// 工具函数
export const getCommunicationTypeLabel = (type) => {
  return COMMUNICATION_TYPE_LABELS[type] || type;
};

export const getCommunicationPriorityLabel = (priority) => {
  return COMMUNICATION_PRIORITY_LABELS[priority] || priority;
};

export const getCommunicationStatusLabel = (status) => {
  return COMMUNICATION_STATUS_LABELS[status] || status;
};

export const getCommunicationTopicLabel = (topic) => {
  return COMMUNICATION_TOPIC_LABELS[topic] || topic;
};

export const getCustomerSatisfactionLabel = (rating) => {
  return CUSTOMER_SATISFACTION_LABELS[rating] || rating;
};

export const getFollowUpPriorityLabel = (priority) => {
  return FOLLOW_UP_PRIORITY_LABELS[priority] || priority;
};

export const getCommunicationStatusColor = (status) => {
  return COMMUNICATION_STATUS_COLORS[status] || '#6B7280';
};

export const getPriorityColor = (priority) => {
  return PRIORITY_COLORS[priority] || '#6B7280';
};

export const getTopicColor = (topic) => {
  return TOPIC_COLORS[topic] || '#6B7280';
};

export const getSatisfactionColor = (rating) => {
  return SATISFACTION_COLORS[rating] || '#6B7280';
};

// 获取沟通类型图标
export const getCommunicationTypeIcon = (type) => {
  return COMMUNICATION_TYPE_ICONS[type] || '📋';
};

// 计算平均满意度
export const calculateAverageSatisfaction = (communications) => {
  if (!communications || communications.length === 0) return 0;
  
  const validRatings = communications
    .filter(comm => comm.satisfaction_rating)
    .map(comm => comm.satisfaction_rating);
  
  if (validRatings.length === 0) return 0;
  
  const sum = validRatings.reduce((total, rating) => total + rating, 0);
  return (sum / validRatings.length).toFixed(1);
};

// 计算响应率
export const calculateResponseRate = (communications) => {
  if (!communications || communications.length === 0) return 0;
  
  const respondedCommunications = communications.filter(comm => 
    comm.status === COMMUNICATION_STATUS.COMPLETED || 
    comm.status === COMMUNICATION_STATUS.FOLLOW_UP
  );
  
  return ((respondedCommunications.length / communications.length) * 100).toFixed(1);
};

// 获取沟通状态统计
export const getCommunicationStatusStats = (communications) => {
  const stats = {
    total: communications.length,
    pending: 0,
    inProgress: 0,
    completed: 0,
    followUp: 0
  };

  communications.forEach(comm => {
    switch (comm.status) {
      case COMMUNICATION_STATUS.PENDING:
        stats.pending++;
        break;
      case COMMUNICATION_STATUS.IN_PROGRESS:
        stats.inProgress++;
        break;
      case COMMUNICATION_STATUS.COMPLETED:
        stats.completed++;
        break;
      case COMMUNICATION_STATUS.FOLLOW_UP:
        stats.followUp++;
        break;
    }
  });

  return stats;
};

// 获取沟通类型统计
export const getCommunicationTypeStats = (communications) => {
  const stats = {};
  
  Object.values(COMMUNICATION_TYPE).forEach(type => {
    stats[type] = 0;
  });

  communications.forEach(comm => {
    if (comm.communication_type) {
      stats[comm.communication_type] = (stats[comm.communication_type] || 0) + 1;
    }
  });

  return stats;
};

// 获取主题分布统计
export const getTopicDistributionStats = (communications) => {
  const stats = {};
  
  Object.values(COMMUNICATION_TOPIC).forEach(topic => {
    stats[topic] = 0;
  });

  communications.forEach(comm => {
    if (comm.topic) {
      stats[comm.topic] = (stats[comm.topic] || 0) + 1;
    }
  });

  return stats;
};

// 沟通记录验证
export const validateCommunicationData = (communicationData) => {
  const errors = [];
  
  if (!communicationData.customer_id) {
    errors.push('客户ID不能为空');
  }
  
  if (!communicationData.communication_type) {
    errors.push('沟通方式不能为空');
  }
  
  if (!communicationData.topic) {
    errors.push('沟通主题不能为空');
  }
  
  if (!communicationData.subject) {
    errors.push('沟通标题不能为空');
  }
  
  if (!communicationData.communication_date) {
    errors.push('沟通日期不能为空');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

// 搜索和过滤配置
export const COMMUNICATION_FILTER_OPTIONS = [
  { value: 'all', label: '全部状态' },
  { value: COMMUNICATION_STATUS.PENDING, label: '待处理' },
  { value: COMMUNICATION_STATUS.IN_PROGRESS, label: '进行中' },
  { value: COMMUNICATION_STATUS.COMPLETED, label: '已完成' },
  { value: COMMUNICATION_STATUS.FOLLOW_UP, label: '需要跟进' }
];

export const PRIORITY_FILTER_OPTIONS = [
  { value: 'all', label: '全部优先级' },
  { value: COMMUNICATION_PRIORITY.HIGH, label: '高优先级' },
  { value: COMMUNICATION_PRIORITY.MEDIUM, label: '中优先级' },
  { value: COMMUNICATION_PRIORITY.LOW, label: '低优先级' }
];

export const TYPE_FILTER_OPTIONS = [
  { value: 'all', label: '全部方式' },
  { value: COMMUNICATION_TYPE.PHONE, label: '电话' },
  { value: COMMUNICATION_TYPE.EMAIL, label: '邮件' },
  { value: COMMUNICATION_TYPE.ON_SITE, label: '现场' },
  { value: COMMUNICATION_TYPE.WECHAT, label: '微信' },
  { value: COMMUNICATION_TYPE.MEETING, label: '会议' },
  { value: COMMUNICATION_TYPE.VIDEO_CALL, label: '视频通话' }
];

export const TOPIC_FILTER_OPTIONS = [
  { value: 'all', label: '全部主题' },
  { value: COMMUNICATION_TOPIC.SALES, label: '销售' },
  { value: COMMUNICATION_TOPIC.SUPPORT, label: '技术支持' },
  { value: COMMUNICATION_TOPIC.COMPLAINT, label: '投诉' },
  { value: COMMUNICATION_TOPIC.CONSULTATION, label: '咨询' },
  { value: COMMUNICATION_TOPIC.FEEDBACK, label: '反馈' },
  { value: COMMUNICATION_TOPIC.TRAINING, label: '培训' },
  { value: COMMUNICATION_TOPIC.MAINTENANCE, label: '维护' },
  { value: COMMUNICATION_TOPIC.OTHER, label: '其他' }
];

// 默认配置
export const DEFAULT_COMMUNICATION_CONFIG = {
  status: COMMUNICATION_STATUS.PENDING,
  priority: COMMUNICATION_PRIORITY.MEDIUM,
  communication_type: COMMUNICATION_TYPE.PHONE,
  topic: COMMUNICATION_TOPIC.SUPPORT,
  satisfaction_rating: null,
  follow_up_priority: FOLLOW_UP_PRIORITY.MEDIUM
};

export const DEFAULT_FOLLOW_UP_CONFIG = {
  priority: FOLLOW_UP_PRIORITY.MEDIUM,
  due_date: null,
  assigned_to: null,
  notes: ''
};