/**
 * Delivery Management Constants
 * 交付管理系统常量配置
 */

export const DELIVERY_STATUS = {
  PENDING: { value: 'pending', label: '待发货', color: '#faad14' },
  PREPARING: { value: 'preparing', label: '准备中', color: '#1890ff' },
  SHIPPED: { value: 'shipped', label: '已发货', color: '#722ed1' },
  IN_TRANSIT: { value: 'in_transit', label: '在途', color: '#13c2c2' },
  DELIVERED: { value: 'delivered', label: '已送达', color: '#52c41a' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: '#ff4d4f' }
};

export const DELIVERY_PRIORITY = {
  URGENT: { value: 'urgent', label: '紧急', color: '#ff4d4f' },
  HIGH: { value: 'high', label: '高', color: '#fa8c16' },
  NORMAL: { value: 'normal', label: '普通', color: '#1890ff' },
  LOW: { value: 'low', label: '低', color: '#52c41a' }
};

export const SHIPPING_METHODS = {
  EXPRESS: { value: 'express', label: '快递', days: '1-3天' },
  STANDARD: { value: 'standard', label: '标准物流', days: '3-7天' },
  FREIGHT: { value: 'freight', label: '货运', days: '7-15天' },
  SELF_PICKUP: { value: 'self_pickup', label: '自提', days: '0天' }
};

export const PACKAGE_TYPES = {
  STANDARD: { value: 'standard', label: '标准包装' },
  FRAGILE: { value: 'fragile', label: '易碎品包装' },
  LIQUID: { value: 'liquid', label: '液体包装' },
  OVERSIZE: { value: 'oversize', label: '超大件包装' }
};