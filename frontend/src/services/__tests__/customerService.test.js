/**
 * Customer Service 测试
 * 测试范围：
 * - Customer 360度信息获取
 * - 订单历史
 * - 报价历史
 * - 合同历史
 * - 付款记录
 * - 交付记录
 * - 满意度记录
 * - 分析数据
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import * as customerService from '../customerService';
import { apiClient } from '../apiClient';

describe('Customer Service', () => {
  let mock;

  beforeEach(() => {
    // 创建apiClient的mock
    mock = new MockAdapter(apiClient);
    vi.clearAllMocks();
  });

  afterEach(() => {
    mock.reset();
  });

  describe('getCustomer360()', () => {
    it('应该获取客户360度信息', async () => {
      const mockData = {
        id: 1,
        name: 'Test Company',
        contact: 'John Doe',
        email: 'john@test.com',
      };

      mock.onGet('/api/v1/customer/1').reply(200, mockData);

      const result = await customerService.getCustomer360(1);

      expect(result).toEqual(mockData);
      expect(mock.history.get).toHaveLength(1);
      expect(mock.history.get[0].url).toBe('/api/v1/customer/1');
    });

    it('应该处理客户不存在的情况', async () => {
      mock.onGet('/api/v1/customer/999').reply(404, {
        message: 'Customer not found',
      });

      await expect(customerService.getCustomer360(999)).rejects.toThrow();
    });
  });

  describe('getCustomerOrders()', () => {
    it('应该获取客户订单历史', async () => {
      const mockData = {
        items: [
          { id: 1, order_no: 'ORD001', amount: 10000 },
          { id: 2, order_no: 'ORD002', amount: 20000 },
        ],
        total: 2,
      };

      mock.onGet('/api/v1/customer/1/orders').reply(200, mockData);

      const result = await customerService.getCustomerOrders(1);

      expect(result).toEqual(mockData);
      expect(result.items).toHaveLength(2);
    });

    it('应该支持分页参数', async () => {
      mock.onGet('/api/v1/customer/1/orders').reply(200, { items: [], total: 0 });

      await customerService.getCustomerOrders(1, { page: 2, page_size: 10 });

      expect(mock.history.get[0].params).toEqual({ page: 2, page_size: 10 });
    });

    it('应该支持状态过滤', async () => {
      mock.onGet('/api/v1/customer/1/orders').reply(200, { items: [], total: 0 });

      await customerService.getCustomerOrders(1, { status: 'COMPLETED' });

      expect(mock.history.get[0].params).toEqual({ status: 'COMPLETED' });
    });
  });

  describe('getCustomerQuotes()', () => {
    it('应该获取客户报价历史', async () => {
      const mockData = {
        items: [{ id: 1, quote_no: 'Q001', amount: 50000 }],
        total: 1,
      };

      mock.onGet('/api/v1/customer/1/quotes').reply(200, mockData);

      const result = await customerService.getCustomerQuotes(1);

      expect(result).toEqual(mockData);
    });

    it('应该支持查询参数', async () => {
      mock.onGet('/api/v1/customer/1/quotes').reply(200, { items: [], total: 0 });

      await customerService.getCustomerQuotes(1, {
        status: 'PENDING',
        date_from: '2024-01-01',
      });

      expect(mock.history.get[0].params).toEqual({
        status: 'PENDING',
        date_from: '2024-01-01',
      });
    });
  });

  describe('getCustomerContracts()', () => {
    it('应该获取客户合同历史', async () => {
      const mockData = {
        items: [{ id: 1, contract_no: 'C001', value: 100000 }],
        total: 1,
      };

      mock.onGet('/api/v1/customer/1/contracts').reply(200, mockData);

      const result = await customerService.getCustomerContracts(1);

      expect(result).toEqual(mockData);
    });
  });

  describe('getCustomerPayments()', () => {
    it('应该获取客户付款记录', async () => {
      const mockData = {
        items: [
          { id: 1, amount: 10000, payment_date: '2024-01-15' },
          { id: 2, amount: 20000, payment_date: '2024-02-15' },
        ],
        total: 2,
      };

      mock.onGet('/api/v1/customer/1/payments').reply(200, mockData);

      const result = await customerService.getCustomerPayments(1);

      expect(result).toEqual(mockData);
      expect(result.items).toHaveLength(2);
    });

    it('应该支持日期范围过滤', async () => {
      mock.onGet('/api/v1/customer/1/payments').reply(200, { items: [], total: 0 });

      await customerService.getCustomerPayments(1, {
        start_date: '2024-01-01',
        end_date: '2024-12-31',
      });

      expect(mock.history.get[0].params).toEqual({
        start_date: '2024-01-01',
        end_date: '2024-12-31',
      });
    });
  });

  describe('getCustomerDeliveries()', () => {
    it('应该获取客户交付记录', async () => {
      const mockData = {
        items: [
          { id: 1, project_name: 'Project A', delivery_date: '2024-01-20' },
        ],
        total: 1,
      };

      mock.onGet('/api/v1/customer/1/deliveries').reply(200, mockData);

      const result = await customerService.getCustomerDeliveries(1);

      expect(result).toEqual(mockData);
    });
  });

  describe('getCustomerSatisfaction()', () => {
    it('应该获取客户满意度记录', async () => {
      const mockData = {
        items: [{ id: 1, score: 95, comment: 'Excellent service' }],
        total: 1,
        average_score: 95,
      };

      mock.onGet('/api/v1/customer/1/satisfaction').reply(200, mockData);

      const result = await customerService.getCustomerSatisfaction(1);

      expect(result).toEqual(mockData);
      expect(result.average_score).toBe(95);
    });
  });

  describe('getCustomerServices()', () => {
    it('应该获取客户服务记录', async () => {
      const mockData = {
        items: [{ id: 1, service_type: 'MAINTENANCE', date: '2024-01-10' }],
        total: 1,
      };

      mock.onGet('/api/v1/customer/1/services').reply(200, mockData);

      const result = await customerService.getCustomerServices(1);

      expect(result).toEqual(mockData);
    });

    it('应该支持服务类型过滤', async () => {
      mock.onGet('/api/v1/customer/1/services').reply(200, { items: [], total: 0 });

      await customerService.getCustomerServices(1, {
        service_type: 'MAINTENANCE',
      });

      expect(mock.history.get[0].params).toEqual({
        service_type: 'MAINTENANCE',
      });
    });
  });

  describe('getCustomerAnalytics()', () => {
    it('应该获取客户分析数据', async () => {
      const mockData = {
        total_revenue: 500000,
        total_orders: 10,
        average_order_value: 50000,
        customer_lifetime_value: 1000000,
        satisfaction_score: 92,
      };

      mock.onGet('/api/v1/customer/1/analytics').reply(200, mockData);

      const result = await customerService.getCustomerAnalytics(1);

      expect(result).toEqual(mockData);
      expect(result.total_revenue).toBe(500000);
      expect(result.satisfaction_score).toBe(92);
    });

    it('应该支持时间范围参数', async () => {
      mock.onGet('/api/v1/customer/1/analytics').reply(200, {});

      await customerService.getCustomerAnalytics(1, {
        period: '2024',
        granularity: 'monthly',
      });

      expect(mock.history.get[0].params).toEqual({
        period: '2024',
        granularity: 'monthly',
      });
    });
  });

  describe('错误处理', () => {
    it('应该处理网络错误', async () => {
      mock.onGet('/api/v1/customer/1').networkError();

      await expect(customerService.getCustomer360(1)).rejects.toThrow();
    });

    it('应该处理服务器错误', async () => {
      mock.onGet('/api/v1/customer/1').reply(500, {
        message: 'Internal Server Error',
      });

      await expect(customerService.getCustomer360(1)).rejects.toThrow();
    });

    it('应该处理超时错误', async () => {
      mock.onGet('/api/v1/customer/1/orders').timeout();

      await expect(customerService.getCustomerOrders(1)).rejects.toThrow();
    });

    it('应该处理参数错误', async () => {
      mock.onGet('/api/v1/customer/1/analytics').reply(400, {
        message: 'Invalid parameters',
      });

      await expect(customerService.getCustomerAnalytics(1)).rejects.toThrow();
    });
  });

  describe('默认导出', () => {
    it('应该导出所有方法', () => {
      expect(customerService.default).toEqual({
        getCustomer360: customerService.getCustomer360,
        getCustomerOrders: customerService.getCustomerOrders,
        getCustomerQuotes: customerService.getCustomerQuotes,
        getCustomerContracts: customerService.getCustomerContracts,
        getCustomerPayments: customerService.getCustomerPayments,
        getCustomerDeliveries: customerService.getCustomerDeliveries,
        getCustomerSatisfaction: customerService.getCustomerSatisfaction,
        getCustomerServices: customerService.getCustomerServices,
        getCustomerAnalytics: customerService.getCustomerAnalytics,
      });
    });
  });
});
