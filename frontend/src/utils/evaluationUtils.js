/**
 * 评价相关的工具函数和常量
 */

// 评分建议
export const scoringGuidelines = [
  {
    range: "95-100",
    level: "A+",
    description: "远超预期，表现卓越",
    color: "text-emerald-400",
  },
  {
    range: "90-94",
    level: "A",
    description: "超出预期，表现优秀",
    color: "text-emerald-400",
  },
  {
    range: "85-89",
    level: "B+",
    description: "符合预期，表现良好",
    color: "text-blue-400",
  },
  {
    range: "80-84",
    level: "B",
    description: "基本符合预期",
    color: "text-blue-400",
  },
  {
    range: "75-79",
    level: "C+",
    description: "略低于预期，需改进",
    color: "text-amber-400",
  },
  {
    range: "70-74",
    level: "C",
    description: "低于预期，需重点改进",
    color: "text-amber-400",
  },
  {
    range: "60-69",
    level: "D",
    description: "明显低于预期，需密切关注",
    color: "text-red-400",
  },
];

// 评价建议模板
export const commentTemplates = [
  {
    category: "优秀表现",
    templates: [
      "工作态度积极主动，能够独立完成复杂任务，技术能力突出",
      "按时保质完成工作任务，在项目中发挥了关键作用",
      "技术攻关能力强，成功解决了多个技术难题",
      "代码质量高，注重代码规范和可维护性",
    ],
  },
  {
    category: "良好表现",
    templates: [
      "工作完成度良好，基本达到预期目标",
      "技术能力扎实，能够按时完成分配的任务",
      "团队协作能力较好，能够与他人有效配合",
      "学习能力强，能够快速掌握新技术",
    ],
  },
  {
    category: "需改进",
    templates: [
      "工作效率有待提升，部分任务完成进度滞后",
      "建议加强技术深度学习，提升解决复杂问题的能力",
      "需要加强与团队的沟通协作",
      "建议提高代码质量，注重细节",
    ],
  },
];

/**
 * 验证评分
 */
export const validateScore = (score) => {
  if (!score) return { valid: false, message: "请输入评分" };
  const numScore = Number(score);
  if (numScore < 60 || numScore > 100) {
    return { valid: false, message: "评分必须在60-100之间" };
  }
  return { valid: true };
};

/**
 * 验证评价意见
 */
export const validateComment = (comment) => {
  if (!comment || !comment.trim()) {
    return { valid: false, message: "请填写评价意见" };
  }
  return { valid: true };
};
