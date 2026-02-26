/**
 * Procurement API 测试
 * 测试范围：
 * - purchaseApi: 采购订单管理
 * - outsourcingApi: 外协管理
 * - procurementAnalysisApi: 采购分析
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { setupApiTest, teardownApiTest } from './_test-setup.js';

describe('Procurement API', () => {
  let api, mock;
  let purchaseApi, outsourcingApi, procurementAnalysisApi;

  beforeEach(async () => {
    vi.resetModules();
    
    const clientModule = await import('../client.js');
    api = clientModule.default || clientModule.api;
    
    const procurementModule = await import('../procurement.js');
    purchaseApi = procurementModule.purchaseApi;
    outsourcingApi = procurementModule.outsourcingApi;
    procurementAnalysisApi = procurementModule.procurementAnalysisApi;
    
    mock = new MockAdapter(api);
    vi.clearAllMocks();
  });

  afterEach(() => {
    if (mock) {
      mock.restore();
    }
  });

  describe('purchaseApi - 采购订单API', () => {
    it('list() - 应该获取采购订单列表', async () => {
      mock.onGet('/api/v1/purchase-orders/').reply(200, {
        success: true,
        data: [{ id: 1, order_no: 'PO001' }],
      });

      const response = await purchaseApi.list({ page: 1 });

      expect(response.status).toBe(200);
      expect(mock.history.get).toHaveLength(1);
    });

    it('get() - 应该获取采购订单详情', async () => {
      mock.onGet('/api/v1/purchase-orders/1').reply(200, {
        success: true,
        data: { id: 1, order_no: 'PO001', status: 'APPROVED' },
      });

      const response = await purchaseApi.get(1);

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建采购订单', async () => {
      const order = {
        supplier_id: 1,
        project_id: 1,
        items: [{ material: 'Steel', quantity: 100 }],
      };
      mock.onPost('/api/v1/purchase-orders').reply(201, {
        success: true,
        data: { id: 1, ...order },
      });

      const response = await purchaseApi.create(order);

      expect(response.status).toBe(201);
      expect(JSON.parse(mock.history.post[0].data)).toEqual(order);
    });

    it('update() - 应该更新采购订单', async () => {
      const updates = { status: 'IN_TRANSIT' };
      mock.onPut('/api/v1/purchase-orders/1').reply(200, {
        success: true,
        data: { id: 1, ...updates },
      });

      const response = await purchaseApi.update(1, updates);

      expect(response.status).toBe(200);
    });

    it('submit() - 应该提交采购订单审批', async () => {
      mock.onPut('/api/v1/purchase-orders/1/submit').reply(200, {
        success: true,
        data: { status: 'PENDING_APPROVAL' },
      });

      const response = await purchaseApi.orders.submit(1);

      expect(response.status).toBe(200);
    });

    it('approve() - 应该审批采购订单', async () => {
      const approvalData = { approved: true, comment: 'Approved' };
      mock.onPut('/api/v1/purchase-orders/1/approve').reply(200, {
        success: true,
        data: { status: 'APPROVED' },
      });

      const response = await purchaseApi.orders.approve(1, approvalData);

      expect(response.status).toBe(200);
    });

    it('getItems() - 应该获取订单条目', async () => {
      mock.onGet('/api/v1/purchase-orders/1/items').reply(200, {
        success: true,
        data: [{ id: 1, material: 'Steel', quantity: 100 }],
      });

      const response = await purchaseApi.orders.getItems(1);

      expect(response.status).toBe(200);
    });

    it('createFromBOM() - 应该从BOM创建采购订单', async () => {
      mock.onPost('/api/v1/purchase-orders/from-bom').reply(201, {
        success: true,
        data: { id: 1, created_from_bom: true },
      });

      const response = await purchaseApi.orders.createFromBOM({
        project_id: 1,
        machine_id: 1,
      });

      expect(response.status).toBe(201);
    });
  });

  describe('purchaseApi.requests - 采购申请API', () => {
    it('list() - 应该获取采购申请列表', async () => {
      mock.onGet('/api/v1/purchase-orders/requests').reply(200, {
        success: true,
        data: [{ id: 1, title: 'Request 1' }],
      });

      const response = await purchaseApi.requests.list({ status: 'PENDING' });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建采购申请', async () => {
      const request = { title: 'New Request', items: [] };
      mock.onPost('/api/v1/purchase-orders/requests').reply(201, {
        success: true,
        data: { id: 1, ...request },
      });

      const response = await purchaseApi.requests.create(request);

      expect(response.status).toBe(201);
    });

    it('generateOrders() - 应该从申请生成采购订单', async () => {
      mock.onPost('/api/v1/purchase-orders/requests/1/generate-orders').reply(200, {
        success: true,
        data: { orders: [{ id: 1 }] },
      });

      const response = await purchaseApi.requests.generateOrders(1, {
        split_by_supplier: true,
      });

      expect(response.status).toBe(200);
    });

    it('delete() - 应该删除采购申请', async () => {
      mock.onDelete('/api/v1/purchase-orders/requests/1').reply(204);

      const response = await purchaseApi.requests.delete(1);

      expect(response.status).toBe(204);
    });
  });

  describe('purchaseApi.receipts - 收货API', () => {
    it('list() - 应该获取收货记录列表', async () => {
      mock.onGet('/api/v1/purchase-orders/goods-receipts/').reply(200, {
        success: true,
        data: [{ id: 1, receipt_no: 'GR001' }],
      });

      const response = await purchaseApi.receipts.list({ page: 1 });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建收货记录', async () => {
      const receipt = { order_id: 1, items: [] };
      mock.onPost('/api/v1/purchase-orders/goods-receipts/').reply(201, {
        success: true,
        data: { id: 1, ...receipt },
      });

      const response = await purchaseApi.receipts.create(receipt);

      expect(response.status).toBe(201);
    });

    it('receive() - 应该确认收货', async () => {
      mock.onPut('/api/v1/purchase-orders/goods-receipts/1/receive').reply(200, {
        success: true,
        data: { status: 'RECEIVED' },
      });

      const response = await purchaseApi.receipts.receive(1, {
        status: 'RECEIVED',
      });

      expect(response.status).toBe(200);
    });

    it('inspectItem() - 应该质检条目', async () => {
      const inspectionData = { passed: true, comment: 'Good quality' };
      mock
        .onPut('/api/v1/purchase-orders/goods-receipts/1/items/1/inspect')
        .reply(200, {
          success: true,
          data: { inspection_status: 'PASSED' },
        });

      const response = await purchaseApi.receipts.inspectItem(
        1,
        1,
        inspectionData
      );

      expect(response.status).toBe(200);
    });
  });

  describe('outsourcingApi - 外协API', () => {
    it('vendors.list() - 应该获取供应商列表', async () => {
      mock.onGet('/api/v1/outsourcing-vendors').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Vendor 1' }],
      });

      const response = await outsourcingApi.vendors.list({ type: 'PROCESSING' });

      expect(response.status).toBe(200);
    });

    it('vendors.create() - 应该创建供应商', async () => {
      const vendor = { name: 'New Vendor', type: 'PROCESSING' };
      mock.onPost('/api/v1/outsourcing-vendors').reply(201, {
        success: true,
        data: { id: 1, ...vendor },
      });

      const response = await outsourcingApi.vendors.create(vendor);

      expect(response.status).toBe(201);
    });

    it('vendors.evaluate() - 应该评价供应商', async () => {
      const evaluation = { score: 85, comment: 'Good service' };
      mock.onPost('/api/v1/outsourcing-vendors/1/evaluations').reply(201, {
        success: true,
        data: { id: 1, ...evaluation },
      });

      const response = await outsourcingApi.vendors.evaluate(1, evaluation);

      expect(response.status).toBe(201);
    });

    it('orders.list() - 应该获取外协订单列表', async () => {
      mock.onGet('/api/v1/outsourcing-orders').reply(200, {
        success: true,
        data: [{ id: 1, order_no: 'OS001' }],
      });

      const response = await outsourcingApi.orders.list({ status: 'IN_PROGRESS' });

      expect(response.status).toBe(200);
    });

    it('orders.create() - 应该创建外协订单', async () => {
      const order = { vendor_id: 1, project_id: 1, items: [] };
      mock.onPost('/api/v1/outsourcing-orders').reply(201, {
        success: true,
        data: { id: 1, ...order },
      });

      const response = await outsourcingApi.orders.create(order);

      expect(response.status).toBe(201);
    });

    it('orders.updateItem() - 应该更新订单条目', async () => {
      const itemUpdate = { status: 'COMPLETED' };
      mock.onPut('/api/v1/outsourcing-order-items/1').reply(200, {
        success: true,
        data: { id: 1, ...itemUpdate },
      });

      const response = await outsourcingApi.orders.updateItem(1, itemUpdate);

      expect(response.status).toBe(200);
    });

    it('deliveries.create() - 应该创建交付记录', async () => {
      const delivery = { order_id: 1, items: [] };
      mock.onPost('/api/v1/outsourcing-orders/1/deliveries').reply(201, {
        success: true,
        data: { id: 1, ...delivery },
      });

      const response = await outsourcingApi.deliveries.create(1, delivery);

      expect(response.status).toBe(201);
    });

    it('inspections.create() - 应该创建质检记录', async () => {
      const inspection = { order_id: 1, result: 'PASSED' };
      mock.onPost('/api/v1/outsourcing-orders/1/inspections').reply(201, {
        success: true,
        data: { id: 1, ...inspection },
      });

      const response = await outsourcingApi.inspections.create(1, inspection);

      expect(response.status).toBe(201);
    });
  });

  describe('procurementAnalysisApi - 采购分析API', () => {
    it('getCostTrend() - 应该获取成本趋势', async () => {
      mock.onGet('/api/v1/procurement-analysis/cost-trend').reply(200, {
        success: true,
        data: { trend: [] },
      });

      const response = await procurementAnalysisApi.getCostTrend({
        start_date: '2024-01-01',
        end_date: '2024-12-31',
      });

      expect(response.status).toBe(200);
      expect(mock.history.get[0].params).toEqual({
        start_date: '2024-01-01',
        end_date: '2024-12-31',
      });
    });

    it('getPriceFluctuation() - 应该获取价格波动', async () => {
      mock.onGet('/api/v1/procurement-analysis/price-fluctuation').reply(200, {
        success: true,
        data: { materials: [] },
      });

      const response = await procurementAnalysisApi.getPriceFluctuation({
        material: 'Steel',
      });

      expect(response.status).toBe(200);
    });

    it('getDeliveryPerformance() - 应该获取交期表现', async () => {
      mock.onGet('/api/v1/procurement-analysis/delivery-performance').reply(200, {
        success: true,
        data: { on_time_rate: 0.85 },
      });

      const response = await procurementAnalysisApi.getDeliveryPerformance({
        supplier_id: 1,
      });

      expect(response.status).toBe(200);
    });

    it('getRequestEfficiency() - 应该获取申请处理效率', async () => {
      mock.onGet('/api/v1/procurement-analysis/request-efficiency').reply(200, {
        success: true,
        data: { avg_processing_days: 3 },
      });

      const response = await procurementAnalysisApi.getRequestEfficiency({
        month: '2024-01',
      });

      expect(response.status).toBe(200);
    });

    it('getQualityRate() - 应该获取质量合格率', async () => {
      mock.onGet('/api/v1/procurement-analysis/quality-rate').reply(200, {
        success: true,
        data: { pass_rate: 0.95 },
      });

      const response = await procurementAnalysisApi.getQualityRate({
        supplier_id: 1,
      });

      expect(response.status).toBe(200);
    });

    it('getOverview() - 应该获取采购概览', async () => {
      mock.onGet('/api/v1/procurement-analysis/overview').reply(200, {
        success: true,
        data: {
          total_orders: 100,
          total_amount: 1000000,
        },
      });

      const response = await procurementAnalysisApi.getOverview();

      expect(response.status).toBe(200);
    });
  });

  describe('purchaseApi.kitRate - 齐套率API', () => {
    it('getProject() - 应该获取项目齐套率', async () => {
      mock.onGet('/api/v1/projects/1/kit-rate').reply(200, {
        success: true,
        data: { kit_rate: 0.85 },
      });

      const response = await purchaseApi.kitRate.getProject(1, {});

      expect(response.status).toBe(200);
    });

    it('getMachine() - 应该获取机器齐套率', async () => {
      mock.onGet('/api/v1/machines/1/kit-rate').reply(200, {
        success: true,
        data: { kit_rate: 0.90 },
      });

      const response = await purchaseApi.kitRate.getMachine(1, {});

      expect(response.status).toBe(200);
    });

    it('unified() - 应该获取统一齐套率', async () => {
      mock.onGet('/api/v1/kit-rates/unified/1').reply(200, {
        success: true,
        data: { kit_rate: 0.88 },
      });

      const response = await purchaseApi.kitRate.unified(1, {});

      expect(response.status).toBe(200);
    });
  });

  describe('错误处理', () => {
    it('应该处理404错误 - 订单不存在', async () => {
      mock.onGet('/api/v1/purchase-orders/999').reply(404, {
        success: false,
        message: 'Purchase order not found',
      });

      await expect(purchaseApi.get(999)).rejects.toThrow();
    });

    it('应该处理422验证错误', async () => {
      mock.onPost('/api/v1/purchase-orders').reply(422, {
        success: false,
        message: 'Validation failed',
        errors: {
          supplier_id: ['Supplier is required'],
        },
      });

      await expect(purchaseApi.create({})).rejects.toThrow();
    });

    it('应该处理权限错误', async () => {
      mock.onPut('/api/v1/purchase-orders/1/approve').reply(403, {
        success: false,
        message: 'Not authorized to approve',
      });

      await expect(
        purchaseApi.orders.approve(1, { approved: true })
      ).rejects.toThrow();
    });

    it('应该处理网络错误', async () => {
      mock.onGet('/api/v1/purchase-orders/').networkError();

      await expect(purchaseApi.list()).rejects.toThrow();
    });

    it('应该处理超时错误', async () => {
      mock.onGet('/api/v1/purchase-orders/').timeout();

      await expect(purchaseApi.list()).rejects.toThrow();
    });
  });
});
