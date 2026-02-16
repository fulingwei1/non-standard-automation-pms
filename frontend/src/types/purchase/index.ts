/**
 * 智能采购管理系统 - TypeScript 类型定义
 * @module types/purchase
 * @description 包含所有采购相关的数据类型定义
 */

// ============================================
// 1. 采购建议相关类型
// ============================================

/**
 * 采购建议状态
 */
export type SuggestionStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'ORDERED';

/**
 * 采购建议来源
 */
export type SourceType = 'SHORTAGE' | 'SAFETY_STOCK' | 'FORECAST' | 'MANUAL';

/**
 * 紧急程度
 */
export type UrgencyLevel = 'LOW' | 'NORMAL' | 'HIGH' | 'URGENT';

/**
 * AI推荐理由
 */
export interface RecommendationReason {
  total_score: number;
  performance_score: number;
  price_score: number;
  delivery_score: number;
  history_score: number;
}

/**
 * 采购建议
 */
export interface PurchaseSuggestion {
  id: number;
  suggestion_no: string;
  material_id: number;
  material_code: string;
  material_name: string;
  specification: string;
  unit: string;
  suggested_qty: number;
  current_stock: number;
  safety_stock: number;
  source_type: SourceType;
  urgency_level: UrgencyLevel;
  suggested_supplier_id: number;
  suggested_supplier_name: string;
  ai_confidence: number;
  recommendation_reason: RecommendationReason;
  estimated_unit_price: number;
  estimated_total_amount: number;
  status: SuggestionStatus;
  created_at: string;
  updated_at: string;
}

/**
 * 批准采购建议请求
 */
export interface ApproveSuggestionRequest {
  approved: boolean;
  review_note?: string;
  suggested_supplier_id?: number;
}

/**
 * 建议转订单请求
 */
export interface CreateOrderFromSuggestionRequest {
  supplier_id?: number;
  required_date?: string;
  payment_terms?: string;
  delivery_address?: string;
  remark?: string;
}

/**
 * 建议转订单响应
 */
export interface CreateOrderResponse {
  message: string;
  data: {
    order_id: number;
    order_no: string;
  };
}

// ============================================
// 2. 供应商绩效相关类型
// ============================================

/**
 * 供应商评级
 */
export type SupplierRating = 'A+' | 'A' | 'B' | 'C' | 'D';

/**
 * 绩效评估状态
 */
export type PerformanceStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';

/**
 * 权重配置
 */
export interface WeightConfig {
  on_time_delivery: number;
  quality: number;
  price: number;
  response: number;
}

/**
 * 供应商绩效
 */
export interface SupplierPerformance {
  id: number;
  supplier_id: number;
  supplier_code: string;
  supplier_name: string;
  evaluation_period: string;
  period_start: string;
  period_end: string;
  total_orders: number;
  total_amount: number;
  on_time_delivery_rate: number;
  on_time_orders: number;
  late_orders: number;
  avg_delay_days: number;
  quality_pass_rate: number;
  total_received_qty: number;
  qualified_qty: number;
  rejected_qty: number;
  price_competitiveness: number;
  avg_price_vs_market: number;
  response_speed_score: number;
  avg_response_hours: number;
  overall_score: number;
  rating: SupplierRating;
  weight_config: WeightConfig;
  status: PerformanceStatus;
  created_at: string;
  updated_at: string;
}

/**
 * 触发评估请求
 */
export interface EvaluateSupplierRequest {
  supplier_id: number;
  evaluation_period: string;
  weight_config?: WeightConfig;
}

/**
 * 供应商排名
 */
export interface SupplierRanking {
  supplier_id: number;
  supplier_code: string;
  supplier_name: string;
  overall_score: number;
  rating: SupplierRating;
  on_time_delivery_rate: number;
  quality_pass_rate: number;
  price_competitiveness: number;
  response_speed_score: number;
  total_orders: number;
  total_amount: number;
  evaluation_period: string;
  rank: number;
}

/**
 * 供应商排名响应
 */
export interface SupplierRankingResponse {
  evaluation_period: string;
  total_suppliers: number;
  rankings: SupplierRanking[];
}

// ============================================
// 3. 供应商报价相关类型
// ============================================

/**
 * 报价状态
 */
export type QuotationStatus = 'ACTIVE' | 'EXPIRED' | 'INACTIVE';

/**
 * 供应商报价
 */
export interface SupplierQuotation {
  id: number;
  quotation_no: string;
  supplier_id: number;
  supplier_code: string;
  supplier_name: string;
  material_id: number;
  material_code: string;
  material_name: string;
  unit_price: number;
  currency: string;
  min_order_qty: number;
  lead_time_days: number;
  valid_from: string;
  valid_to: string;
  payment_terms: string;
  warranty_period: string;
  tax_rate: number;
  remark?: string;
  status: QuotationStatus;
  created_at: string;
  updated_at: string;
}

/**
 * 创建报价请求
 */
export interface CreateQuotationRequest {
  supplier_id: number;
  material_id: number;
  unit_price: number;
  currency?: string;
  min_order_qty?: number;
  lead_time_days?: number;
  valid_from: string;
  valid_to: string;
  payment_terms?: string;
  warranty_period?: string;
  tax_rate?: number;
  remark?: string;
}

/**
 * 报价比价项
 */
export interface QuotationCompareItem extends SupplierQuotation {
  is_selected: boolean;
  performance_score?: number;
  performance_rating?: SupplierRating;
}

/**
 * 报价比价响应
 */
export interface QuotationCompareResponse {
  material_id: number;
  material_code: string;
  material_name: string;
  quotations: QuotationCompareItem[];
  best_price_supplier_id: number;
  recommended_supplier_id: number;
  recommendation_reason: string;
}

// ============================================
// 4. 采购订单相关类型
// ============================================

/**
 * 订单状态
 */
export type OrderStatus = 'PENDING' | 'CONFIRMED' | 'SHIPPED' | 'RECEIVED' | 'CANCELLED';

/**
 * 跟踪事件类型
 */
export type TrackingEventType = 'CREATED' | 'CONFIRMED' | 'SHIPPED' | 'RECEIVED' | 'CANCELLED';

/**
 * 订单跟踪事件
 */
export interface OrderTrackingEvent {
  id: number;
  order_id: number;
  order_no: string;
  event_type: TrackingEventType;
  event_time: string;
  event_description: string;
  old_status?: OrderStatus;
  new_status: OrderStatus;
  tracking_no?: string;
  logistics_company?: string;
  estimated_arrival?: string;
  operator_id?: number;
  operator_name: string;
  created_at: string;
}

/**
 * 收货明细
 */
export interface ReceiveItemDetail {
  order_item_id: number;
  delivery_qty: number;
  received_qty: number;
  remark?: string;
}

/**
 * 收货确认请求
 */
export interface ReceiveOrderRequest {
  receipt_date: string;
  delivery_note_no?: string;
  logistics_company?: string;
  tracking_no?: string;
  items: ReceiveItemDetail[];
  remark?: string;
}

/**
 * 收货确认响应
 */
export interface ReceiveOrderResponse {
  message: string;
  data: {
    receipt_id: number;
    receipt_no: string;
  };
}

// ============================================
// 5. 通用类型
// ============================================

/**
 * API响应包装
 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error_code?: string;
}

/**
 * 分页参数
 */
export interface PaginationParams {
  skip?: number;
  limit?: number;
}

/**
 * 采购建议筛选参数
 */
export interface SuggestionFilters extends PaginationParams {
  status?: SuggestionStatus;
  source_type?: SourceType;
  material_id?: number;
  project_id?: number;
  urgency_level?: UrgencyLevel;
}

/**
 * 供应商绩效筛选参数
 */
export interface PerformanceFilters {
  evaluation_period?: string;
  limit?: number;
}

/**
 * 供应商排名筛选参数
 */
export interface RankingFilters {
  evaluation_period: string;
  limit?: number;
}

/**
 * 报价比价筛选参数
 */
export interface QuotationCompareFilters {
  material_id: number;
  supplier_ids?: string;
}

// ============================================
// 6. UI组件专用类型
// ============================================

/**
 * 紧急程度配置
 */
export interface UrgencyConfig {
  color: string;
  label: string;
  icon?: string;
}

/**
 * 供应商评级配置
 */
export interface RatingConfig {
  color: string;
  label: string;
  minScore: number;
  maxScore: number;
}

/**
 * 表格列定义
 */
export interface TableColumn {
  key: string;
  title: string;
  sortable?: boolean;
  filterable?: boolean;
  width?: string;
}

/**
 * 雷达图数据点
 */
export interface RadarDataPoint {
  subject: string;
  value: number;
  fullMark: number;
}
