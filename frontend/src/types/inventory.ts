/**
 * 库存管理系统 - TypeScript 类型定义
 * Team 2 - 物料库存管理前端开发
 * @version 1.0.0
 */

// ==================== 枚举类型 ====================

/** 交易类型 */
export enum TransactionType {
  PURCHASE_IN = 'PURCHASE_IN',       // 采购入库
  RETURN_IN = 'RETURN_IN',           // 退料入库
  TRANSFER_IN = 'TRANSFER_IN',       // 调拨入库
  ISSUE = 'ISSUE',                   // 领料出库
  SCRAP = 'SCRAP',                   // 报废出库
  TRANSFER_OUT = 'TRANSFER_OUT',     // 调拨出库
  ADJUSTMENT = 'ADJUSTMENT',         // 库存调整
}

/** 库存状态 */
export enum StockStatus {
  NORMAL = 'NORMAL',       // 正常
  LOW = 'LOW',             // 低库存
  EXPIRED = 'EXPIRED',     // 已过期
  RESERVED = 'RESERVED',   // 已预留
}

/** 成本核算方法 */
export enum CostMethod {
  FIFO = 'FIFO',                     // 先进先出
  LIFO = 'LIFO',                     // 后进先出
  WEIGHTED_AVG = 'WEIGHTED_AVG',     // 加权平均
}

/** 盘点任务类型 */
export enum CountTaskType {
  FULL = 'FULL',           // 全盘
  SPOT = 'SPOT',           // 抽盘
  CYCLE = 'CYCLE',         // 循环盘
}

/** 盘点任务状态 */
export enum CountTaskStatus {
  DRAFT = 'DRAFT',               // 草稿
  IN_PROGRESS = 'IN_PROGRESS',   // 进行中
  COMPLETED = 'COMPLETED',       // 已完成
  APPROVED = 'APPROVED',         // 已批准
  CANCELLED = 'CANCELLED',       // 已取消
}

/** 预留状态 */
export enum ReservationStatus {
  ACTIVE = 'ACTIVE',       // 有效
  USED = 'USED',           // 已使用
  CANCELLED = 'CANCELLED', // 已取消
  EXPIRED = 'EXPIRED',     // 已过期
}

// ==================== 基础接口 ====================

/** 物料信息 */
export interface Material {
  id: number;
  code: string;
  name: string;
  specification?: string;
  category?: string;
  unit: string;
  min_stock_level?: number;
  max_stock_level?: number;
  has_batch?: boolean;
  has_expiry?: boolean;
  created_at: string;
  updated_at: string;
}

/** 库存记录 */
export interface Stock {
  id: number;
  material_id: number;
  material_code: string;
  material_name: string;
  specification?: string;
  location: string;
  batch_number?: string;
  quantity: number;
  available_quantity: number;
  reserved_quantity: number;
  unit: string;
  unit_price: number;
  total_value: number;
  production_date?: string;
  expire_date?: string;
  status: StockStatus;
  last_update: string;
}

/** 交易记录 */
export interface Transaction {
  id: number;
  material_id: number;
  material_code: string;
  material_name: string;
  transaction_type: TransactionType;
  quantity: number;
  unit_price: number;
  total_amount: number;
  source_location?: string;
  target_location?: string;
  batch_number?: string;
  purchase_order_id?: number;
  purchase_order_no?: string;
  work_order_id?: number;
  work_order_no?: string;
  project_id?: number;
  project_name?: string;
  operator: string;
  transaction_date: string;
  remark?: string;
}

/** 物料预留 */
export interface Reservation {
  id: number;
  material_id: number;
  material_code: string;
  material_name: string;
  quantity: number;
  used_quantity: number;
  remaining_quantity: number;
  project_id?: number;
  project_name?: string;
  work_order_id?: number;
  work_order_no?: string;
  expected_use_date?: string;
  status: ReservationStatus;
  created_by: string;
  created_at: string;
  remark?: string;
}

/** 盘点任务 */
export interface CountTask {
  id: number;
  task_no: string;
  task_type: CountTaskType;
  task_name: string;
  location?: string;
  scheduled_date: string;
  status: CountTaskStatus;
  created_by: string;
  created_at: string;
  completed_at?: string;
  approved_at?: string;
  approved_by?: string;
  remark?: string;
  item_count?: number;
  difference_count?: number;
}

/** 盘点明细 */
export interface CountDetail {
  id: number;
  task_id: number;
  material_id: number;
  material_code: string;
  material_name: string;
  location: string;
  batch_number?: string;
  book_quantity: number;
  actual_quantity?: number;
  difference?: number;
  difference_value?: number;
  unit_price: number;
  operator?: string;
  counted_at?: string;
  remark?: string;
}

/** 周转率分析 */
export interface TurnoverAnalysis {
  period: {
    start_date: string;
    end_date: string;
  };
  material_id?: number;
  material_code?: string;
  material_name?: string;
  total_issue_value: number;
  avg_stock_value: number;
  turnover_rate: number;
  turnover_days: number;
  period_days: number;
}

/** 库龄分析 */
export interface AgingAnalysis {
  aging_range: string;
  count: number;
  total_quantity: number;
  total_value: number;
  percentage: number;
}

export interface AgingAnalysisResponse {
  location?: string;
  analysis_date: string;
  aging_summary: {
    '0-30天': AgingAnalysis;
    '31-90天': AgingAnalysis;
    '91-180天': AgingAnalysis;
    '181-365天': AgingAnalysis;
    '365天以上': AgingAnalysis;
  };
  details: Array<{
    material_id: number;
    material_code: string;
    material_name: string;
    batch_number?: string;
    quantity: number;
    unit_price: number;
    total_value: number;
    in_stock_days: number;
    aging_range: string;
  }>;
}

// ==================== 仪表板数据 ====================

/** 库存统计卡片 */
export interface StockSummary {
  total_stock_quantity: number;
  total_stock_value: number;
  low_stock_count: number;
  counting_tasks: number;
  expired_materials: number;
  turnover_rate: number;
}

/** 最近交易记录 */
export interface RecentTransaction {
  id: number;
  transaction_date: string;
  material_name: string;
  transaction_type: TransactionType;
  quantity: number;
  operator: string;
}

/** 库存预警 */
export interface StockAlert {
  id: number;
  material_code: string;
  material_name: string;
  current_quantity: number;
  min_stock_level: number;
  alert_type: 'LOW_STOCK' | 'EXPIRED' | 'EXPIRING_SOON';
  alert_message: string;
  location: string;
}

// ==================== API 请求/响应类型 ====================

/** 库存查询参数 */
export interface StockQueryParams {
  material_id?: number;
  location?: string;
  status?: StockStatus;
  batch_number?: string;
  page?: number;
  page_size?: number;
}

/** 交易记录查询参数 */
export interface TransactionQueryParams {
  transaction_type?: TransactionType;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

/** 预留物料请求 */
export interface ReserveRequest {
  material_id: number;
  quantity: number;
  project_id?: number;
  work_order_id?: number;
  expected_use_date?: string;
  remark?: string;
}

/** 领料请求 */
export interface IssueRequest {
  material_id: number;
  quantity: number;
  location: string;
  work_order_id?: number;
  work_order_no?: string;
  project_id?: number;
  cost_method?: CostMethod;
  reservation_id?: number;
  remark?: string;
}

/** 退料请求 */
export interface ReturnRequest {
  material_id: number;
  quantity: number;
  location: string;
  batch_number?: string;
  work_order_id?: number;
  remark?: string;
}

/** 库存转移请求 */
export interface TransferRequest {
  material_id: number;
  quantity: number;
  from_location: string;
  to_location: string;
  batch_number?: string;
  remark?: string;
}

/** 创建盘点任务请求 */
export interface CreateCountTaskRequest {
  task_name: string;
  task_type: CountTaskType;
  location?: string;
  scheduled_date: string;
  material_ids?: number[];
  remark?: string;
}

/** 更新盘点明细请求 */
export interface UpdateCountDetailRequest {
  actual_quantity: number;
  remark?: string;
}

/** 批准盘点调整请求 */
export interface ApproveCountTaskRequest {
  approve_comment?: string;
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/** API 响应 */
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

/** API 错误响应 */
export interface ApiError {
  code: number;
  message: string;
  detail?: string;
  errors?: Record<string, string[]>;
}
