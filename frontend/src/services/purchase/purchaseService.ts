/**
 * 智能采购管理系统 - API 客户端服务
 * @module services/purchase/purchaseService
 * @description 封装所有采购相关的API调用
 */

import axios, { AxiosInstance } from 'axios';
import type {
  PurchaseSuggestion,
  ApproveSuggestionRequest,
  CreateOrderFromSuggestionRequest,
  CreateOrderResponse,
  SupplierPerformance,
  EvaluateSupplierRequest,
  SupplierRankingResponse,
  SupplierQuotation,
  CreateQuotationRequest,
  QuotationCompareResponse,
  OrderTrackingEvent,
  ReceiveOrderRequest,
  ReceiveOrderResponse,
  SuggestionFilters,
  PerformanceFilters,
  RankingFilters,
  QuotationCompareFilters,
  ApiResponse
} from '../../types/purchase';

/**
 * 采购管理 API 客户端
 */
class PurchaseService {
  private client: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1/purchase';
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器 - 添加认证 Token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器 - 统一错误处理
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token 过期，跳转登录
          localStorage.removeItem('access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // ============================================
  // 1. 采购建议管理 API
  // ============================================

  /**
   * 获取采购建议列表
   * @param filters 筛选条件
   * @returns 采购建议列表
   */
  async getSuggestions(filters?: SuggestionFilters): Promise<PurchaseSuggestion[]> {
    const { data } = await this.client.get<PurchaseSuggestion[]>('/suggestions', {
      params: filters,
    });
    return data;
  }

  /**
   * 获取采购建议详情
   * @param id 建议ID
   * @returns 采购建议详情
   */
  async getSuggestionById(id: number): Promise<PurchaseSuggestion> {
    const { data } = await this.client.get<PurchaseSuggestion>(`/suggestions/${id}`);
    return data;
  }

  /**
   * 批准/拒绝采购建议
   * @param id 建议ID
   * @param request 批准请求
   * @returns 操作结果
   */
  async approveSuggestion(
    id: number,
    request: ApproveSuggestionRequest
  ): Promise<ApiResponse<{ suggestion_id: number }>> {
    const { data } = await this.client.post(`/suggestions/${id}/approve`, request);
    return data;
  }

  /**
   * 建议转订单
   * @param id 建议ID
   * @param request 订单信息
   * @returns 创建的订单信息
   */
  async createOrderFromSuggestion(
    id: number,
    request: CreateOrderFromSuggestionRequest
  ): Promise<CreateOrderResponse> {
    const { data } = await this.client.post(`/suggestions/${id}/create-order`, request);
    return data;
  }

  // ============================================
  // 2. 供应商绩效管理 API
  // ============================================

  /**
   * 获取供应商绩效
   * @param supplierId 供应商ID
   * @param filters 筛选条件
   * @returns 供应商绩效列表
   */
  async getSupplierPerformance(
    supplierId: number,
    filters?: PerformanceFilters
  ): Promise<SupplierPerformance[]> {
    const { data } = await this.client.get<SupplierPerformance[]>(
      `/suppliers/${supplierId}/performance`,
      { params: filters }
    );
    return data;
  }

  /**
   * 触发供应商评估
   * @param supplierId 供应商ID
   * @param request 评估请求
   * @returns 评估结果
   */
  async evaluateSupplier(
    supplierId: number,
    request: EvaluateSupplierRequest
  ): Promise<SupplierPerformance> {
    const { data } = await this.client.post<SupplierPerformance>(
      `/suppliers/${supplierId}/evaluate`,
      request
    );
    return data;
  }

  /**
   * 获取供应商排名
   * @param filters 筛选条件
   * @returns 供应商排名列表
   */
  async getSupplierRanking(filters: RankingFilters): Promise<SupplierRankingResponse> {
    const { data } = await this.client.get<SupplierRankingResponse>('/suppliers/ranking', {
      params: filters,
    });
    return data;
  }

  // ============================================
  // 3. 供应商报价管理 API
  // ============================================

  /**
   * 创建供应商报价
   * @param request 报价信息
   * @returns 创建的报价
   */
  async createQuotation(request: CreateQuotationRequest): Promise<SupplierQuotation> {
    const { data } = await this.client.post<SupplierQuotation>('/quotations', request);
    return data;
  }

  /**
   * 获取报价比价
   * @param filters 比价筛选条件
   * @returns 比价结果
   */
  async compareQuotations(filters: QuotationCompareFilters): Promise<QuotationCompareResponse> {
    const { data } = await this.client.get<QuotationCompareResponse>('/quotations/compare', {
      params: filters,
    });
    return data;
  }

  // ============================================
  // 4. 采购订单管理 API
  // ============================================

  /**
   * 获取订单跟踪记录
   * @param orderId 订单ID
   * @returns 跟踪事件列表
   */
  async getOrderTracking(orderId: number): Promise<OrderTrackingEvent[]> {
    const { data } = await this.client.get<OrderTrackingEvent[]>(`/orders/${orderId}/tracking`);
    return data;
  }

  /**
   * 收货确认
   * @param orderId 订单ID
   * @param request 收货信息
   * @returns 收货确认结果
   */
  async receiveOrder(orderId: number, request: ReceiveOrderRequest): Promise<ReceiveOrderResponse> {
    const { data } = await this.client.post<ReceiveOrderResponse>(
      `/orders/${orderId}/receive`,
      request
    );
    return data;
  }

  // ============================================
  // 5. 辅助方法
  // ============================================

  /**
   * 批量评估供应商
   * @param supplierIds 供应商ID列表
   * @param evaluationPeriod 评估期间
   * @returns 评估结果列表
   */
  async batchEvaluateSuppliers(
    supplierIds: number[],
    evaluationPeriod: string
  ): Promise<SupplierPerformance[]> {
    const results = await Promise.allSettled(
      supplierIds.map((id) =>
        this.evaluateSupplier(id, {
          supplier_id: id,
          evaluation_period: evaluationPeriod,
        })
      )
    );

    return results
      .filter((r): r is PromiseFulfilledResult<SupplierPerformance> => r.status === 'fulfilled')
      .map((r) => r.value);
  }

  /**
   * 获取所有待审批建议
   * @returns 待审批建议列表
   */
  async getPendingSuggestions(): Promise<PurchaseSuggestion[]> {
    return this.getSuggestions({ status: 'PENDING' });
  }

  /**
   * 批量批准建议
   * @param suggestionIds 建议ID列表
   * @param note 批注
   * @returns 批准结果
   */
  async batchApproveSuggestions(
    suggestionIds: number[],
    note?: string
  ): Promise<ApiResponse<{ suggestion_id: number }>[]> {
    const results = await Promise.allSettled(
      suggestionIds.map((id) =>
        this.approveSuggestion(id, {
          approved: true,
          review_note: note,
        })
      )
    );

    return results
      .filter(
        (r): r is PromiseFulfilledResult<ApiResponse<{ suggestion_id: number }>> =>
          r.status === 'fulfilled'
      )
      .map((r) => r.value);
  }
}

// 导出单例
export const purchaseService = new PurchaseService();
export default purchaseService;
