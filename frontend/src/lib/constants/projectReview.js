/**
 * 📋 项目评审管理系统 - 配置常量
 * 评审状态、类型、流程、角色等核心配置
 */

// ==================== 评审状态配置 ====================

export const REVIEW_STATUS = {
  DRAFT: {
    key: 'draft',
    label: '草稿',
    color: 'bg-slate-500',
    textColor: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/30',
    icon: 'Edit',
    description: '评审报告正在编辑中',
    allowedActions: ['edit', 'publish', 'delete'],
    transition: ['published']
  },
  PUBLISHED: {
    key: 'published',
    label: '已发布',
    color: 'bg-green-500',
    textColor: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
    icon: 'CheckCircle2',
    description: '评审报告已发布，可供查看',
    allowedActions: ['archive'],
    transition: ['archived']
  },
  ARCHIVED: {
    key: 'archived',
    label: '已归档',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    icon: 'Archive',
    description: '评审报告已归档',
    allowedActions: ['view'],
    transition: []
  },
  REVIEWING: {
    key: 'reviewing',
    label: '评审中',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    icon: 'Clock',
    description: '正在进行评审',
    allowedActions: ['review', 'comment'],
    transition: ['published', 'draft']
  }
};

export const REVIEW_STATUS_OPTIONS = Object.values(REVIEW_STATUS);

// ==================== 评审类型配置 ====================

export const REVIEW_TYPES = {
  POST_MORTEM: {
    key: 'post_mortem',
    label: '结项复盘',
    description: '项目完成后的全面复盘',
    icon: 'Archive',
    color: 'bg-purple-500',
    phases: ['initiation', 'execution', 'closure'],
    requiredSections: ['overview', 'lessons', 'practices'],
    reviewers: ['project_manager', 'team_lead', 'stakeholder'],
    duration: '2-4小时'
  },
  MID_TERM: {
    key: 'mid_term',
    label: '中期复盘',
    description: '项目进行中的阶段性回顾',
    icon: 'TrendingUp',
    color: 'bg-blue-500',
    phases: ['execution'],
    requiredSections: ['overview', 'lessons'],
    reviewers: ['project_manager', 'team_lead'],
    duration: '1-2小时'
  },
  QUARTERLY: {
    key: 'quarterly',
    label: '季度复盘',
    description: '按季度进行的定期回顾',
    icon: 'Calendar',
    color: 'bg-green-500',
    phases: ['execution'],
    requiredSections: ['overview', 'lessons'],
    reviewers: ['project_manager'],
    duration: '1小时'
  },
  MILESTONE: {
    key: 'milestone',
    label: '里程碑复盘',
    description: '重要里程碑达成后的回顾',
    icon: 'Target',
    color: 'bg-orange-500',
    phases: ['execution'],
    requiredSections: ['overview', 'lessons'],
    reviewers: ['project_manager', 'team_lead'],
    duration: '1-2小时'
  },
  INCIDENT: {
    key: 'incident',
    label: '事故复盘',
    description: '发生重大事故后的专项复盘',
    icon: 'AlertCircle',
    color: 'bg-red-500',
    phases: ['response', 'recovery', 'prevention'],
    requiredSections: ['overview', 'lessons', 'practices'],
    reviewers: ['project_manager', 'team_lead', 'quality_manager'],
    duration: '3-5小时'
  }
};

export const REVIEW_TYPE_OPTIONS = Object.values(REVIEW_TYPES);

// ==================== 经验教训类型配置 ====================

export const LESSON_TYPES = {
  SUCCESS: {
    key: 'success',
    label: '成功经验',
    icon: 'CheckCircle2',
    color: 'bg-green-500',
    textColor: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
    description: '项目中的成功做法和经验',
    impact: 'positive',
    category: 'best_practice'
  },
  FAILURE: {
    key: 'failure',
    label: '失败教训',
    icon: 'AlertCircle',
    color: 'bg-red-500',
    textColor: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    description: '项目中的失败经验和教训',
    impact: 'negative',
    category: 'lesson_learned'
  },
  CHALLENGE: {
    key: 'challenge',
    label: '挑战与解决',
    icon: 'Lightbulb',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    description: '遇到的挑战及解决方案',
    impact: 'neutral',
    category: 'challenge_solution'
  },
  IMPROVEMENT: {
    key: 'improvement',
    label: '改进建议',
    icon: 'TrendingUp',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    description: '未来改进的建议',
    impact: 'positive',
    category: 'improvement'
  }
};

export const LESSON_TYPE_OPTIONS = Object.values(LESSON_TYPES);

// ==================== 评审角色配置 ====================

export const REVIEW_ROLES = {
  PROJECT_MANAGER: {
    key: 'project_manager',
    label: '项目经理',
    icon: 'User',
    color: 'bg-blue-500',
    description: '项目负责人，负责整体协调',
    responsibilities: [
      '组织评审会议',
      '总结项目成果',
      '分析项目数据',
      '制定改进计划'
    ],
    required: true
  },
  TEAM_LEAD: {
    key: 'team_lead',
    label: '团队负责人',
    icon: 'Users',
    color: 'bg-green-500',
    description: '技术团队负责人',
    responsibilities: [
      '技术实现总结',
      '团队协作评估',
      '技术难点分析',
      '改进建议提供'
    ],
    required: true
  },
  STAKEHOLDER: {
    key: 'stakeholder',
    label: '利益相关者',
    icon: 'User',
    color: 'bg-purple-500',
    description: '项目利益相关方',
    responsibilities: [
      '需求满足度评估',
      '业务价值评价',
      '用户体验反馈',
      '未来需求建议'
    ],
    required: false
  },
  QUALITY_MANAGER: {
    key: 'quality_manager',
    label: '质量经理',
    icon: 'Shield',
    color: 'bg-red-500',
    description: '质量管理负责人',
    responsibilities: [
      '质量标准评估',
      '缺陷分析总结',
      '质量改进建议',
      '合规性检查'
    ],
    required: false
  },
  EXTERNAL_EXPERT: {
    key: 'external_expert',
    label: '外部专家',
    icon: 'Award',
    color: 'bg-amber-500',
    description: '行业专家或顾问',
    responsibilities: [
      '行业最佳实践分享',
      '专业建议提供',
      '标杆对比分析',
      '创新思路启发'
    ],
    required: false
  }
};

export const REVIEW_ROLE_OPTIONS = Object.values(REVIEW_ROLES);

// ==================== 评审阶段配置 ====================

export const REVIEW_PHASES = {
  PREPARATION: {
    key: 'preparation',
    label: '准备阶段',
    icon: 'FileText',
    color: 'bg-blue-500',
    description: '评审前的准备工作',
    duration: '1-3天',
    activities: [
      '收集项目数据',
      '准备评审材料',
      '确定评审人员',
      '安排评审时间'
    ],
    deliverables: ['评审议程', '数据报告', '会议材料']
  },
  EXECUTION: {
    key: 'execution',
    label: '执行阶段',
    icon: 'Users',
    color: 'bg-green-500',
    description: '正式评审会议',
    duration: '1-4小时',
    activities: [
      '项目成果展示',
      '经验教训分享',
      '问题讨论分析',
      '改进计划制定'
    ],
    deliverables: ['会议记录', '初步结论', '行动计划']
  },
  ANALYSIS: {
    key: 'analysis',
    label: '分析阶段',
    icon: 'BarChart3',
    color: 'bg-purple-500',
    description: '深度分析和总结',
    duration: '2-5天',
    activities: [
      '数据深度分析',
      '根因分析',
      '模式识别',
      '趋势预测'
    ],
    deliverables: ['分析报告', '根因分析', '趋势报告']
  },
  DOCUMENTATION: {
    key: 'documentation',
    label: '文档化阶段',
    icon: 'BookOpen',
    color: 'bg-orange-500',
    description: '撰写和整理评审文档',
    duration: '1-2天',
    activities: [
      '撰写评审报告',
      '整理经验教训',
      '制定最佳实践',
      '知识库更新'
    ],
    deliverables: ['评审报告', '经验教训库', '最佳实践库']
  },
  FOLLOW_UP: {
    key: 'follow_up',
    label: '跟进阶段',
    icon: 'Target',
    color: 'bg-red-500',
    description: '后续行动和改进跟踪',
    duration: '持续',
    activities: [
      '改进计划执行',
      '效果跟踪评估',
      '定期检查回顾',
      '持续优化改进'
    ],
    deliverables: ['执行报告', '效果评估', '优化建议']
  }
};

export const REVIEW_PHASE_OPTIONS = Object.values(REVIEW_PHASES);

// ==================== 评估指标配置 ====================

export const EVALUATION_METRICS = {
  PROJECT_SUCCESS: {
    key: 'project_success',
    label: '项目成功度',
    category: 'outcome',
    weight: 0.3,
    description: '项目整体目标达成情况',
    measurement: 'percentage',
    target: 80,
    criteria: [
      '目标完成度',
      '质量标准达成',
      '时间控制情况',
      '成本控制效果'
    ]
  },
  TEAM_PERFORMANCE: {
    key: 'team_performance',
    label: '团队表现',
    category: 'process',
    weight: 0.25,
    description: '团队协作和执行效果',
    measurement: 'score',
    target: 85,
    criteria: [
      '沟通协作效率',
      '技术能力表现',
      '问题解决能力',
      '学习能力提升'
    ]
  },
  PROCESS_EFFICIENCY: {
    key: 'process_efficiency',
    label: '流程效率',
    category: 'process',
    weight: 0.2,
    description: '项目流程的优化程度',
    measurement: 'percentage',
    target: 75,
    criteria: [
      '流程规范性',
      '工具使用效率',
      '文档完整性',
      '决策及时性'
    ]
  },
  INNOVATION_LEARNING: {
    key: 'innovation_learning',
    label: '创新学习',
    category: 'growth',
    weight: 0.15,
    description: '创新成果和团队学习',
    measurement: 'score',
    target: 70,
    criteria: [
      '技术创新成果',
      '流程改进创新',
      '知识沉淀分享',
      '技能提升效果'
    ]
  },
  STAKEHOLDER_SATISFACTION: {
    key: 'stakeholder_satisfaction',
    label: '相关方满意度',
    category: 'outcome',
    weight: 0.1,
    description: '客户和利益相关方满意度',
    measurement: 'score',
    target: 85,
    criteria: [
      '客户满意度',
      '用户反馈评价',
      '业务价值认可',
      '合作体验评价'
    ]
  }
};

export const EVALUATION_METRIC_OPTIONS = Object.values(EVALUATION_METRICS);

// ==================== 最佳实践类别配置 ====================

export const PRACTICE_CATEGORIES = {
  PROJECT_MANAGEMENT: {
    key: 'project_management',
    label: '项目管理',
    icon: 'Briefcase',
    color: 'bg-blue-500',
    description: '项目管理相关的最佳实践',
    examples: [
      '敏捷项目管理',
      '风险管理',
      '沟通管理',
      '范围管理'
    ]
  },
  TECHNICAL_EXCELLENCE: {
    key: 'technical_excellence',
    label: '技术卓越',
    icon: 'Code',
    color: 'bg-purple-500',
    description: '技术实现的最佳实践',
    examples: [
      '架构设计',
      '代码质量',
      '测试策略',
      '性能优化'
    ]
  },
  TEAM_COLLABORATION: {
    key: 'team_collaboration',
    label: '团队协作',
    icon: 'Users',
    color: 'bg-green-500',
    description: '团队协作的最佳实践',
    examples: [
      '沟通机制',
      '知识分享',
      '冲突解决',
      '团队建设'
    ]
  },
  PROCESS_IMPROVEMENT: {
    key: 'process_improvement',
    label: '流程改进',
    icon: 'Settings',
    color: 'bg-orange-500',
    description: '流程优化的最佳实践',
    examples: [
      '流程标准化',
      '自动化改进',
      '工具优化',
      '度量体系'
    ]
  },
  INNOVATION_CULTURE: {
    key: 'innovation_culture',
    label: '创新文化',
    icon: 'Lightbulb',
    color: 'bg-amber-500',
    description: '创新文化建设的最佳实践',
    examples: [
      '创新激励',
      '实验文化',
      '失败容忍',
      '学习分享'
    ]
  }
};

export const PRACTICE_CATEGORY_OPTIONS = Object.values(PRACTICE_CATEGORIES);

// ==================== 工具函数 ====================

/**
 * 获取评审状态配置
 */
export function getReviewStatus(status) {
  return REVIEW_STATUS[status?.toUpperCase()] || REVIEW_STATUS.DRAFT;
}

/**
 * 获取评审类型配置
 */
export function getReviewType(type) {
  return REVIEW_TYPES[type?.toUpperCase()] || REVIEW_TYPES.POST_MORTEM;
}

/**
 * 获取经验教训类型配置
 */
export function getLessonType(type) {
  return LESSON_TYPES[type?.toUpperCase()] || LESSON_TYPES.SUCCESS;
}

/**
 * 获取评审角色配置
 */
export function getReviewRole(role) {
  return REVIEW_ROLES[role?.toUpperCase()] || REVIEW_ROLES.PROJECT_MANAGER;
}

/**
 * 获取评审阶段配置
 */
export function getReviewPhase(phase) {
  return REVIEW_PHASES[phase?.toUpperCase()] || REVIEW_PHASES.PREPARATION;
}

/**
 * 获取评估指标配置
 */
export function getEvaluationMetric(metric) {
  return EVALUATION_METRICS[metric?.toUpperCase()] || EVALUATION_METRICS.PROJECT_SUCCESS;
}

/**
 * 获取最佳实践类别配置
 */
export function getPracticeCategory(category) {
  return PRACTICE_CATEGORIES[category?.toUpperCase()] || PRACTICE_CATEGORIES.PROJECT_MANAGEMENT;
}

/**
 * 计算评审完成度
 */
export function calculateReviewProgress(review) {
  if (!review) {return 0;}
  
  const sections = ['overview', 'lessons', 'practices'];
  const completedSections = sections.filter(section => {
    if (section === 'overview') {
      return review.project_summary && review.key_achievements;
    } else if (section === 'lessons') {
      return review.lessons && review.lessons.length > 0;
    } else if (section === 'practices') {
      return review.best_practices && review.best_practices.length > 0;
    }
    return false;
  });
  
  return Math.round((completedSections.length / sections.length) * 100);
}

/**
 * 计算评审评分
 */
export function calculateReviewScore(review) {
  if (!review || !review.evaluations) {return 0;}
  
  const totalScore = review.evaluations.reduce(
    (sum, evaluation) => {
      const metric = getEvaluationMetric(evaluation.metric);
      return sum + (evaluation.score * metric.weight);
    },
    0
  );
  
  return Math.round(totalScore * 100) / 100;
}

/**
 * 生成评审建议
 */
export function generateReviewRecommendations(review) {
  const recommendations = [];
  const score = calculateReviewScore(review);
  
  if (score < 60) {
    recommendations.push({
      type: 'critical',
      title: '需要全面改进',
      description: '项目评审得分较低，需要制定详细的改进计划',
      actions: [
        '深入分析问题根因',
        '制定具体改进措施',
        '加强团队能力建设',
        '优化项目管理流程'
      ]
    });
  } else if (score < 80) {
    recommendations.push({
      type: 'moderate',
      title: '有待提升',
      description: '项目表现中等，可以在多个方面进行改进',
      actions: [
        '总结成功经验',
        '分析不足之处',
        '制定提升计划',
        '加强知识分享'
      ],
    });
  } else {
    recommendations.push({
      type: 'good',
      title: '表现优秀',
      description: '项目表现优秀，建议总结最佳实践',
      actions: [
        '提炼最佳实践',
        '推广成功经验',
        '持续创新改进',
        '分享知识成果'
      ],
    });
  }
  
  return recommendations;
}

/**
 * 验证评审完整性
 */
export function validateReviewCompleteness(review, reviewType) {
  const typeConfig = getReviewType(reviewType);
  const errors = [];
  const warnings = [];
  
  // 检查必填部分
  typeConfig.requiredSections.forEach(section => {
    if (section === 'overview' && !review.project_summary) {
      errors.push('缺少项目概述');
    } else if (section === 'lessons' && (!review.lessons || review.lessons.length === 0)) {
      warnings.push('建议添加经验教训');
    } else if (section === 'practices' && (!review.best_practices || review.best_practices.length === 0)) {
      warnings.push('建议添加最佳实践');
    }
  });
  
  // 检查评审人员
  const requiredRoles = typeConfig.reviewers.filter(role => 
    getReviewRole(role).required
  );
  const actualRoles = review.reviewers?.map(r => r.role) || [];
  
  requiredRoles.forEach(role => {
    if (!actualRoles.includes(role)) {
      errors.push(`缺少必要的评审角色: ${getReviewRole(role).label}`);
    }
  });
  
  return { errors, warnings };
}

/**
 * 格式化评审报告
 */
export function formatReviewReport(review) {
  return {
    basicInfo: {
      reviewId: review.id,
      reviewNo: review.review_no,
      projectName: review.project_name,
      projectCode: review.project_code,
      reviewType: getReviewType(review.review_type).label,
      reviewDate: review.review_date,
      status: getReviewStatus(review.status).label,
      score: calculateReviewScore(review),
      progress: calculateReviewProgress(review)
    },
    summary: {
      projectOverview: review.project_summary,
      keyAchievements: review.key_achievements,
      challengesFaced: review.challenges_faced,
      lessonsLearned: review.lessons?.length || 0,
      bestPractices: review.best_practices?.length || 0
    },
    details: {
      lessons: review.lessons || [],
      practices: review.best_practices || [],
      evaluations: review.evaluations || [],
      actionItems: review.action_items || [],
      attachments: review.attachments || []
    },
    metadata: {
      createdAt: review.created_at,
      updatedAt: review.updated_at,
      createdBy: review.created_by,
      reviewedBy: review.reviewers || [],
      version: review.version || 1
    }
  };
}

// ==================== 默认导出 ====================

export default {
  // 配置集合
  REVIEW_STATUS,
  REVIEW_TYPES,
  LESSON_TYPES,
  REVIEW_ROLES,
  REVIEW_PHASES,
  EVALUATION_METRICS,
  PRACTICE_CATEGORIES,
  
  // 选项集合
  REVIEW_STATUS_OPTIONS,
  REVIEW_TYPE_OPTIONS,
  LESSON_TYPE_OPTIONS,
  REVIEW_ROLE_OPTIONS,
  REVIEW_PHASE_OPTIONS,
  EVALUATION_METRIC_OPTIONS,
  PRACTICE_CATEGORY_OPTIONS,
  
  // 工具函数
  getReviewStatus,
  getReviewType,
  getLessonType,
  getReviewRole,
  getReviewPhase,
  getEvaluationMetric,
  getPracticeCategory,
  calculateReviewProgress,
  calculateReviewScore,
  generateReviewRecommendations,
  validateReviewCompleteness,
  formatReviewReport
};
