// 物料齐套管理业务配置
export const MATERIAL_STATUS = {
  AVAILABLE: 'available',       // 可用
  OUT_OF_STOCK: 'out_of_stock', // 缺货
  ON_ORDER: 'on_order',         // 已订购
  IN_TRANSIT: 'in_transit',     // 运输中
  DAMAGED: 'damaged',           // 损坏
  EXPIRED: 'expired',           // 过期
  RESERVED: 'reserved',         // 已预留
  QUALITY_HOLD: 'quality_hold'  // 质检扣留
};

export const READINESS_STATUS = {
  READY: 'ready',           // 齐套
  PARTIAL: 'partial',       // 部分齐套
  NOT_READY: 'not_ready',   // 未齐套
  BLOCKED: 'blocked'        // 阻塞
};

export const MATERIAL_TYPE = {
  RAW_MATERIAL: 'raw_material',    // 原材料
  COMPONENT: 'component',          // 零部件
  EQUIPMENT: 'equipment',          // 设备
  TOOL: 'tool',                    // 工具
  CONSUMABLE: 'consumable',        // 耗材
  SOFTWARE: 'software',            // 软件
  DOCUMENTATION: 'documentation'  // 文档
};

export const PRIORITY_LEVEL = {
  LOW: 'low',         // 低优先级
  MEDIUM: 'medium',   // 中优先级
  HIGH: 'high',       // 高优先级
  URGENT: 'urgent'    // 紧急
};

export const SUPPLIER_STATUS = {
  ACTIVE: 'active',         // 活跃
  INACTIVE: 'inactive',     // 非活跃
  SUSPENDED: 'suspended',   // 暂停
  UNDER_REVIEW: 'under_review' // 审核中
};

export const QUALITY_STATUS = {
  PENDING: 'pending',       // 待检
  PASSED: 'passed',         // 合格
  FAILED: 'failed',         // 不合格
  REJECTED: 'rejected'       // 拒收
};

// 标签配置
export const MATERIAL_STATUS_LABELS = {
  [MATERIAL_STATUS.AVAILABLE]: '可用',
  [MATERIAL_STATUS.OUT_OF_STOCK]: '缺货',
  [MATERIAL_STATUS.ON_ORDER]: '已订购',
  [MATERIAL_STATUS.IN_TRANSIT]: '运输中',
  [MATERIAL_STATUS.DAMAGED]: '损坏',
  [MATERIAL_STATUS.EXPIRED]: '过期',
  [MATERIAL_STATUS.RESERVED]: '已预留',
  [MATERIAL_STATUS.QUALITY_HOLD]: '质检扣留'
};

export const READINESS_STATUS_LABELS = {
  [READINESS_STATUS.READY]: '齐套',
  [READINESS_STATUS.PARTIAL]: '部分齐套',
  [READINESS_STATUS.NOT_READY]: '未齐套',
  [READINESS_STATUS.BLOCKED]: '阻塞'
};

export const MATERIAL_TYPE_LABELS = {
  [MATERIAL_TYPE.RAW_MATERIAL]: '原材料',
  [MATERIAL_TYPE.COMPONENT]: '零部件',
  [MATERIAL_TYPE.EQUIPMENT]: '设备',
  [MATERIAL_TYPE.TOOL]: '工具',
  [MATERIAL_TYPE.CONSUMABLE]: '耗材',
  [MATERIAL_TYPE.SOFTWARE]: '软件',
  [MATERIAL_TYPE.DOCUMENTATION]: '文档'
};

export const PRIORITY_LEVEL_LABELS = {
  [PRIORITY_LEVEL.LOW]: '低优先级',
  [PRIORITY_LEVEL.MEDIUM]: '中优先级',
  [PRIORITY_LEVEL.HIGH]: '高优先级',
  [PRIORITY_LEVEL.URGENT]: '紧急'
};

export const SUPPLIER_STATUS_LABELS = {
  [SUPPLIER_STATUS.ACTIVE]: '活跃',
  [SUPPLIER_STATUS.INACTIVE]: '非活跃',
  [SUPPLIER_STATUS.SUSPENDED]: '暂停',
  [SUPPLIER_STATUS.UNDER_REVIEW]: '审核中'
};

export const QUALITY_STATUS_LABELS = {
  [QUALITY_STATUS.PENDING]: '待检',
  [QUALITY_STATUS.PASSED]: '合格',
  [QUALITY_STATUS.FAILED]: '不合格',
  [QUALITY_STATUS.REJECTED]: '拒收'
};

// 状态颜色配置
export const MATERIAL_STATUS_COLORS = {
  [MATERIAL_STATUS.AVAILABLE]: '#10B981',     // 绿色
  [MATERIAL_STATUS.OUT_OF_STOCK]: '#EF4444',   // 红色
  [MATERIAL_STATUS.ON_ORDER]: '#F59E0B',     // 橙色
  [MATERIAL_STATUS.IN_TRANSIT]: '#3B82F6',   // 蓝色
  [MATERIAL_STATUS.DAMAGED]: '#DC2626',       // 深红色
  [MATERIAL_STATUS.EXPIRED]: '#7C2D12',       // 棕色
  [MATERIAL_STATUS.RESERVED]: '#8B5CF6',     // 紫色
  [MATERIAL_STATUS.QUALITY_HOLD]: '#F97316'   // 深橙色
};

export const READINESS_STATUS_COLORS = {
  [READINESS_STATUS.READY]: '#10B981',     // 绿色
  [READINESS_STATUS.PARTIAL]: '#F59E0B',   // 橙色
  [READINESS_STATUS.NOT_READY]: '#EF4444', // 红色
  [READINESS_STATUS.BLOCKED]: '#DC2626'    // 深红色
};

export const PRIORITY_COLORS = {
  [PRIORITY_LEVEL.LOW]: '#10B981',       // 绿色
  [PRIORITY_LEVEL.MEDIUM]: '#F59E0B',     // 橙色
  [PRIORITY_LEVEL.HIGH]: '#EF4444',       // 红色
  [PRIORITY_LEVEL.URGENT]: '#DC2626'      // 深红色
};

// 统计配置
export const MATERIAL_STATS_CONFIG = {
  TOTAL_MATERIALS: 'total_materials',
  AVAILABLE_MATERIALS: 'available_materials',
  OUT_OF_STOCK_MATERIALS: 'out_of_stock_materials',
  ON_ORDER_MATERIALS: 'on_order_materials',
  READINESS_RATE: 'readiness_rate',
  CRITICAL_SHORTAGES: 'critical_shortages'
};

// 工具函数
export const getMaterialStatusLabel = (status) => {
  return MATERIAL_STATUS_LABELS[status] || status;
};

export const getReadinessStatusLabel = (status) => {
  return READINESS_STATUS_LABELS[status] || status;
};

export const getMaterialTypeLabel = (type) => {
  return MATERIAL_TYPE_LABELS[type] || type;
};

export const getPriorityLevelLabel = (priority) => {
  return PRIORITY_LEVEL_LABELS[priority] || priority;
};

export const getSupplierStatusLabel = (status) => {
  return SUPPLIER_STATUS_LABELS[status] || status;
};

export const getQualityStatusLabel = (status) => {
  return QUALITY_STATUS_LABELS[status] || status;
};

export const getMaterialStatusColor = (status) => {
  return MATERIAL_STATUS_COLORS[status] || '#6B7280';
};

export const getReadinessStatusColor = (status) => {
  return READINESS_STATUS_COLORS[status] || '#6B7280';
};

export const getPriorityColor = (priority) => {
  return PRIORITY_COLORS[priority] || '#6B7280';
};

// 计算齐套率
export const calculateReadinessRate = (materials) => {
  if (!materials || materials.length === 0) {return 0;}
  
  const availableMaterials = materials.filter(material => 
    material.status === MATERIAL_STATUS.AVAILABLE
  ).length;
  
  return Math.round((availableMaterials / materials.length) * 100);
};

// 计算物料状态统计
export const getMaterialStatusStats = (materials) => {
  const stats = {
    total: materials.length,
    available: 0,
    outOfStock: 0,
    onOrder: 0,
    inTransit: 0,
    damaged: 0,
    expired: 0,
    reserved: 0,
    qualityHold: 0
  };

  materials.forEach(material => {
    switch (material.status) {
      case MATERIAL_STATUS.AVAILABLE:
        stats.available++;
        break;
      case MATERIAL_STATUS.OUT_OF_STOCK:
        stats.outOfStock++;
        break;
      case MATERIAL_STATUS.ON_ORDER:
        stats.onOrder++;
        break;
      case MATERIAL_STATUS.IN_TRANSIT:
        stats.inTransit++;
        break;
      case MATERIAL_STATUS.DAMAGED:
        stats.damaged++;
        break;
      case MATERIAL_STATUS.EXPIRED:
        stats.expired++;
        break;
      case MATERIAL_STATUS.RESERVED:
        stats.reserved++;
        break;
      case MATERIAL_STATUS.QUALITY_HOLD:
        stats.qualityHold++;
        break;
    }
  });

  return stats;
};

// 计算关键缺料
export const getCriticalShortages = (materials) => {
  return materials.filter(material => 
    material.status === MATERIAL_STATUS.OUT_OF_STOCK && 
    material.priority === PRIORITY_LEVEL.URGENT
  );
};

// 计算齐套状态
export const calculateReadinessStatus = (materials) => {
  const readinessRate = calculateReadinessRate(materials);
  const criticalShortages = getCriticalShortages(materials);
  
  if (criticalShortages.length > 0) {
    return READINESS_STATUS.BLOCKED;
  }
  
  if (readinessRate === 100) {
    return READINESS_STATUS.READY;
  } else if (readinessRate >= 70) {
    return READINESS_STATUS.PARTIAL;
  } else {
    return READINESS_STATUS.NOT_READY;
  }
};

// 物料数据验证
export const validateMaterialData = (materialData) => {
  const errors = [];
  
  if (!materialData.name || materialData.name.trim() === '') {
    errors.push('物料名称不能为空');
  }
  
  if (!materialData.type) {
    errors.push('物料类型不能为空');
  }
  
  if (!materialData.quantity || materialData.quantity <= 0) {
    errors.push('物料数量必须大于0');
  }
  
  if (!materialData.unit) {
    errors.push('计量单位不能为空');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

// 搜索和过滤配置
export const MATERIAL_STATUS_FILTER_OPTIONS = [
  { value: 'all', label: '全部状态' },
  { value: MATERIAL_STATUS.AVAILABLE, label: '可用' },
  { value: MATERIAL_STATUS.OUT_OF_STOCK, label: '缺货' },
  { value: MATERIAL_STATUS.ON_ORDER, label: '已订购' },
  { value: MATERIAL_STATUS.IN_TRANSIT, label: '运输中' },
  { value: MATERIAL_STATUS.DAMAGED, label: '损坏' },
  { value: MATERIAL_STATUS.EXPIRED, label: '过期' },
  { value: MATERIAL_STATUS.RESERVED, label: '已预留' },
  { value: MATERIAL_STATUS.QUALITY_HOLD, label: '质检扣留' }
];

export const TYPE_FILTER_OPTIONS = [
  { value: 'all', label: '全部类型' },
  { value: MATERIAL_TYPE.RAW_MATERIAL, label: '原材料' },
  { value: MATERIAL_TYPE.COMPONENT, label: '零部件' },
  { value: MATERIAL_TYPE.EQUIPMENT, label: '设备' },
  { value: MATERIAL_TYPE.TOOL, label: '工具' },
  { value: MATERIAL_TYPE.CONSUMABLE, label: '耗材' },
  { value: MATERIAL_TYPE.SOFTWARE, label: '软件' },
  { value: MATERIAL_TYPE.DOCUMENTATION, label: '文档' }
];

export const PRIORITY_FILTER_OPTIONS = [
  { value: 'all', label: '全部优先级' },
  { value: PRIORITY_LEVEL.LOW, label: '低优先级' },
  { value: PRIORITY_LEVEL.MEDIUM, label: '中优先级' },
  { value: PRIORITY_LEVEL.HIGH, label: '高优先级' },
  { value: PRIORITY_LEVEL.URGENT, label: '紧急' }
];

// 默认配置
export const DEFAULT_MATERIAL_CONFIG = {
  status: MATERIAL_STATUS.AVAILABLE,
  priority: PRIORITY_LEVEL.MEDIUM,
  qualityStatus: QUALITY_STATUS.PENDING,
  minStockLevel: 0,
  maxStockLevel: 100
};