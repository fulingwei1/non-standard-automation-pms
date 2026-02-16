/**
 * 库存管理 API 客户端
 * Team 2 - 物料库存管理前端开发
 * @version 1.0.0
 */

import axios, { AxiosInstance } from 'axios';
import {
  Stock,
  Transaction,
  Reservation,
  CountTask,
  CountDetail,
  TurnoverAnalysis,
  AgingAnalysisResponse,
  StockSummary,
  StockQueryParams,
  TransactionQueryParams,
  ReserveRequest,
  IssueRequest,
  ReturnRequest,
  TransferRequest,
  CreateCountTaskRequest,
  UpdateCountDetailRequest,
  ApproveCountTaskRequest,
  PaginatedResponse,
  ApiResponse,
} from '../types/inventory';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

/**
 * 创建 Axios 实例
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // 请求拦截器 - 自动添加 token
  client.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // 响应拦截器 - 统一错误处理
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response) {
        const { status, data } = error.response;
        const errorMap: Record<number, string> = {
          401: '未授权，请重新登录',
          403: '权限不足',
          404: '资源不存在',
          422: '请求参数错误',
          500: '服务器内部错误',
        };
        const message = data?.detail || errorMap[status] || '请求失败';
        throw new Error(message);
      }
      throw error;
    }
  );

  return client;
};

const apiClient = createApiClient();

/**
 * 库存管理 API 服务
 */
export class InventoryAPI {
  // ==================== 库存查询 ====================

  /**
   * 查询库存列表
   * GET /api/v1/inventory/stocks
   */
  static async getStocks(params?: StockQueryParams): Promise<PaginatedResponse<Stock>> {
    const response = await apiClient.get<PaginatedResponse<Stock>>('/inventory/stocks', {
      params,
    });
    return response.data;
  }

  /**
   * 获取单个库存详情
   * GET /api/v1/inventory/stocks/{id}
   */
  static async getStockById(id: number): Promise<Stock> {
    const response = await apiClient.get<Stock>(`/inventory/stocks/${id}`);
    return response.data;
  }

  /**
   * 获取库存交易记录
   * GET /api/v1/inventory/stocks/{id}/transactions
   */
  static async getStockTransactions(
    stockId: number,
    params?: TransactionQueryParams
  ): Promise<Transaction[]> {
    const response = await apiClient.get<Transaction[]>(
      `/inventory/stocks/${stockId}/transactions`,
      { params }
    );
    return response.data;
  }

  /**
   * 获取库存统计数据（仪表板）
   * GET /api/v1/inventory/dashboard/summary
   */
  static async getDashboardSummary(): Promise<StockSummary> {
    const response = await apiClient.get<StockSummary>('/inventory/dashboard/summary');
    return response.data;
  }

  // ==================== 物料操作 ====================

  /**
   * 预留物料
   * POST /api/v1/inventory/reserve
   */
  static async reserveMaterial(data: ReserveRequest): Promise<Reservation> {
    const response = await apiClient.post<Reservation>('/inventory/reserve', data);
    return response.data;
  }

  /**
   * 取消预留
   * POST /api/v1/inventory/reservation/{id}/cancel
   */
  static async cancelReservation(
    id: number,
    cancel_reason?: string
  ): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>(
      `/inventory/reservation/${id}/cancel`,
      { cancel_reason }
    );
    return response.data;
  }

  /**
   * 领料
   * POST /api/v1/inventory/issue
   */
  static async issueMaterial(data: IssueRequest): Promise<Transaction> {
    const response = await apiClient.post<Transaction>('/inventory/issue', data);
    return response.data;
  }

  /**
   * 退料
   * POST /api/v1/inventory/return
   */
  static async returnMaterial(data: ReturnRequest): Promise<Transaction> {
    const response = await apiClient.post<Transaction>('/inventory/return', data);
    return response.data;
  }

  /**
   * 库存转移
   * POST /api/v1/inventory/transfer
   */
  static async transferStock(data: TransferRequest): Promise<Transaction> {
    const response = await apiClient.post<Transaction>('/inventory/transfer', data);
    return response.data;
  }

  // ==================== 库存盘点 ====================

  /**
   * 获取盘点任务列表
   * GET /api/v1/inventory/count/tasks
   */
  static async getCountTasks(params?: {
    status?: string;
    location?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<CountTask>> {
    const response = await apiClient.get<PaginatedResponse<CountTask>>(
      '/inventory/count/tasks',
      { params }
    );
    return response.data;
  }

  /**
   * 获取盘点任务详情
   * GET /api/v1/inventory/count/tasks/{id}
   */
  static async getCountTaskById(id: number): Promise<CountTask> {
    const response = await apiClient.get<CountTask>(`/inventory/count/tasks/${id}`);
    return response.data;
  }

  /**
   * 创建盘点任务
   * POST /api/v1/inventory/count/tasks
   */
  static async createCountTask(data: CreateCountTaskRequest): Promise<CountTask> {
    const response = await apiClient.post<CountTask>('/inventory/count/tasks', data);
    return response.data;
  }

  /**
   * 获取盘点明细列表
   * GET /api/v1/inventory/count/tasks/{taskId}/details
   */
  static async getCountDetails(taskId: number): Promise<CountDetail[]> {
    const response = await apiClient.get<CountDetail[]>(
      `/inventory/count/tasks/${taskId}/details`
    );
    return response.data;
  }

  /**
   * 更新盘点明细（录入实盘数量）
   * PUT /api/v1/inventory/count/details/{id}
   */
  static async updateCountDetail(
    id: number,
    data: UpdateCountDetailRequest
  ): Promise<CountDetail> {
    const response = await apiClient.put<CountDetail>(
      `/inventory/count/details/${id}`,
      data
    );
    return response.data;
  }

  /**
   * 批准盘点调整
   * POST /api/v1/inventory/count/tasks/{id}/approve
   */
  static async approveCountTask(
    id: number,
    data?: ApproveCountTaskRequest
  ): Promise<ApiResponse> {
    const response = await apiClient.post<ApiResponse>(
      `/inventory/count/tasks/${id}/approve`,
      data
    );
    return response.data;
  }

  // ==================== 库存分析 ====================

  /**
   * 获取库存周转率分析
   * GET /api/v1/inventory/analysis/turnover
   */
  static async getTurnoverAnalysis(params: {
    material_id?: number;
    start_date: string;
    end_date: string;
  }): Promise<TurnoverAnalysis> {
    const response = await apiClient.get<TurnoverAnalysis>(
      '/inventory/analysis/turnover',
      { params }
    );
    return response.data;
  }

  /**
   * 获取库龄分析
   * GET /api/v1/inventory/analysis/aging
   */
  static async getAgingAnalysis(params?: {
    location?: string;
    material_id?: number;
  }): Promise<AgingAnalysisResponse> {
    const response = await apiClient.get<AgingAnalysisResponse>(
      '/inventory/analysis/aging',
      { params }
    );
    return response.data;
  }

  // ==================== 辅助方法 ====================

  /**
   * 导出库存数据
   * GET /api/v1/inventory/stocks/export
   */
  static async exportStocks(params?: StockQueryParams): Promise<Blob> {
    const response = await apiClient.get('/inventory/stocks/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * 批次追溯
   * GET /api/v1/inventory/batch/{batchNumber}/trace
   */
  static async traceBatch(batchNumber: string): Promise<Transaction[]> {
    const response = await apiClient.get<Transaction[]>(
      `/inventory/batch/${batchNumber}/trace`
    );
    return response.data;
  }
}

export default InventoryAPI;
