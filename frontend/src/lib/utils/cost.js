/**
 * 成本相关工具函数
 */

/**
 * 格式化货币数字（带千分位分隔符）
 * @param {number} value - 金额
 * @param {boolean} showUnit - 是否显示单位
 * @returns {string} 格式化后的金额
 */
export function formatCurrency(value, showUnit = true) {
  if (value === null || value === undefined) return '--';
  
  const num = parseFloat(value);
  if (isNaN(num)) return '--';
  
  // 格式化为千分位
  const formatted = num.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  
  return showUnit ? `¥${formatted}` : formatted;
}

/**
 * 格式化为万元单位
 * @param {number} value - 金额
 * @returns {string} 格式化后的金额（万元）
 */
export function formatCurrencyWan(value) {
  if (value === null || value === undefined) return '--';
  
  const num = parseFloat(value);
  if (isNaN(num)) return '--';
  
  const wan = num / 10000;
  return `${wan.toFixed(1)}万`;
}

/**
 * 格式化百分比
 * @param {number} value - 百分比值
 * @param {number} decimals - 小数位数
 * @returns {string} 格式化后的百分比
 */
export function formatPercent(value, decimals = 2) {
  if (value === null || value === undefined) return '--';
  
  const num = parseFloat(value);
  if (isNaN(num)) return '--';
  
  return `${num.toFixed(decimals)}%`;
}

/**
 * 获取成本状态
 * @param {object} costSummary - 成本摘要对象
 * @returns {object} { status, color, label }
 */
export function getCostStatus(costSummary) {
  if (!costSummary) {
    return { status: 'unknown', color: 'gray', label: '无数据' };
  }

  const { overrun, budget_used_pct } = costSummary;

  if (overrun) {
    return { status: 'danger', color: 'red', label: '超支' };
  }

  if (budget_used_pct >= 90) {
    return { status: 'warning', color: 'yellow', label: '预警' };
  }

  if (budget_used_pct >= 80) {
    return { status: 'caution', color: 'amber', label: '注意' };
  }

  return { status: 'safe', color: 'green', label: '正常' };
}

/**
 * 获取成本使用率的进度条颜色类名
 * @param {number} usedPct - 预算使用率
 * @param {boolean} overrun - 是否超支
 * @returns {string} Tailwind CSS 颜色类名
 */
export function getCostProgressColor(usedPct, overrun) {
  if (overrun || usedPct > 100) return 'bg-red-500';
  if (usedPct >= 90) return 'bg-yellow-500';
  if (usedPct >= 80) return 'bg-amber-500';
  return 'bg-emerald-500';
}

/**
 * 获取成本徽章样式
 * @param {object} costSummary - 成本摘要对象
 * @returns {string} 徽章变体
 */
export function getCostBadgeVariant(costSummary) {
  const { status } = getCostStatus(costSummary);
  
  switch (status) {
    case 'danger':
      return 'destructive';
    case 'warning':
      return 'warning';
    case 'caution':
      return 'secondary';
    default:
      return 'success';
  }
}

/**
 * 生成成本明细数据（用于饼图）
 * @param {object} costBreakdown - 成本明细对象
 * @returns {array} 饼图数据
 */
export function generateCostChartData(costBreakdown) {
  if (!costBreakdown) return [];

  const data = [
    { name: '人工成本', value: costBreakdown.labor || 0, color: '#3b82f6' },
    { name: '材料成本', value: costBreakdown.material || 0, color: '#10b981' },
    { name: '设备成本', value: costBreakdown.equipment || 0, color: '#f59e0b' },
    { name: '差旅成本', value: costBreakdown.travel || 0, color: '#8b5cf6' },
    { name: '其他成本', value: costBreakdown.other || 0, color: '#6b7280' },
  ];

  // 过滤掉值为0的项
  return data.filter(item => item.value > 0);
}

/**
 * 计算成本健康度（0-100）
 * @param {object} costSummary - 成本摘要对象
 * @returns {number} 健康度分数
 */
export function calculateCostHealth(costSummary) {
  if (!costSummary) return 0;

  const { budget_used_pct, overrun } = costSummary;

  if (overrun) {
    // 超支，健康度根据超支程度递减
    const overrunPct = budget_used_pct - 100;
    return Math.max(0, 50 - overrunPct);
  }

  if (budget_used_pct >= 90) return 60;
  if (budget_used_pct >= 80) return 75;
  if (budget_used_pct >= 60) return 90;
  
  return 100;
}
