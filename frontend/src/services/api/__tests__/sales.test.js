/**
 * Sales API 测试
 * 测试范围：
 * - leadApi: 线索管理
 * - opportunityApi: 商机管理
 * - quoteApi: 报价管理
 * - contractApi: 合同管理
 * - invoiceApi: 发票管理
 * - salesStatisticsApi: 销售统计
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { setupApiTest, teardownApiTest } from './_test-setup.js';

describe('Sales API', () => {
  let _api, mock;
  let leadApi, opportunityApi, quoteApi, contractApi, invoiceApi, paymentApi;
  let salesStatisticsApi, salesTemplateApi, salesTeamApi, salesTargetApi;
  let healthApi, priorityApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    _api = setup.api;
    mock = setup.mock;
    
    const salesModule = await import('../sales.js');
    leadApi = salesModule.leadApi;
    opportunityApi = salesModule.opportunityApi;
    quoteApi = salesModule.quoteApi;
    contractApi = salesModule.contractApi;
    invoiceApi = salesModule.invoiceApi;
    paymentApi = salesModule.paymentApi;
    salesStatisticsApi = salesModule.salesStatisticsApi;
    salesTemplateApi = salesModule.salesTemplateApi;
    salesTeamApi = salesModule.salesTeamApi;
    salesTargetApi = salesModule.salesTargetApi;
    healthApi = salesModule.healthApi;
    priorityApi = salesModule.priorityApi;
    
    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  describe('leadApi - 线索API', () => {
    it('list() - 应该获取线索列表', async () => {
      mock.onGet('/api/v1/sales/leads').reply(200, {
        success: true,
        data: [{ id: 1, company: 'Test Company' }],
      });

      const response = await leadApi.list({ page: 1 });

      expect(response.status).toBe(200);
      expect(mock.history.get).toHaveLength(1);
    });

    it('create() - 应该创建线索', async () => {
      const lead = { company: 'New Company', contact: 'John Doe' };
      mock.onPost('/api/v1/sales/leads').reply(201, {
        success: true,
        data: { id: 1, ...lead },
      });

      const response = await leadApi.create(lead);

      expect(response.status).toBe(201);
      expect(JSON.parse(mock.history.post[0].data)).toEqual(lead);
    });

    it('getFollowUps() - 应该获取跟进记录', async () => {
      mock.onGet('/api/v1/sales/leads/1/follow-ups').reply(200, {
        success: true,
        data: [{ id: 1, content: 'Follow up 1' }],
      });

      const response = await leadApi.getFollowUps(1);

      expect(response.status).toBe(200);
    });

    it('createFollowUp() - 应该创建跟进记录', async () => {
      const followUp = { content: 'Called customer', type: 'PHONE' };
      mock.onPost('/api/v1/sales/leads/1/follow-ups').reply(201, {
        success: true,
        data: { id: 1, ...followUp },
      });

      const response = await leadApi.createFollowUp(1, followUp);

      expect(response.status).toBe(201);
    });

    it('convert() - 应该转换线索为商机', async () => {
      const requirementData = { title: 'New Requirement' };
      mock.onPost('/api/v1/sales/leads/1/convert').reply(200, {
        success: true,
        data: { opportunity_id: 1 },
      });

      const response = await leadApi.convert(1, 1, requirementData, false);

      expect(response.status).toBe(200);
      expect(mock.history.post[0].params).toEqual({
        customer_id: 1,
        skip_validation: false,
      });
    });
  });

  describe('opportunityApi - 商机API', () => {
    it('list() - 应该获取商机列表', async () => {
      mock.onGet('/api/v1/sales/opportunities').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Opportunity 1' }],
      });

      const response = await opportunityApi.list({ stage: 'QUALIFICATION' });

      expect(response.status).toBe(200);
      expect(mock.history.get[0].params).toEqual({ stage: 'QUALIFICATION' });
    });

    it('create() - 应该创建商机', async () => {
      const opportunity = { name: 'New Opp', customer_id: 1, value: 100000 };
      mock.onPost('/api/v1/sales/opportunities').reply(201, {
        success: true,
        data: { id: 1, ...opportunity },
      });

      const response = await opportunityApi.create(opportunity);

      expect(response.status).toBe(201);
    });

    it('update() - 应该更新商机', async () => {
      const updates = { value: 120000 };
      mock.onPut('/api/v1/sales/opportunities/1').reply(200, {
        success: true,
        data: { id: 1, ...updates },
      });

      const response = await opportunityApi.update(1, updates);

      expect(response.status).toBe(200);
    });

    it('getWinProbability() - 应该获取赢单概率', async () => {
      mock.onGet('/api/v1/sales/opportunities/1/win-probability').reply(200, {
        success: true,
        data: { probability: 0.75, factors: [] },
      });

      const response = await opportunityApi.getWinProbability(1);

      expect(response.status).toBe(200);
    });

    it('submitGate() - 应该提交阶段门审批', async () => {
      const gateData = { checklist: [] };
      mock.onPost('/api/v1/sales/opportunities/1/gate').reply(200, {
        success: true,
        data: { approved: true },
      });

      const response = await opportunityApi.submitGate(1, gateData, 'G2');

      expect(response.status).toBe(200);
      expect(mock.history.post[0].params).toEqual({ gate_type: 'G2' });
    });
  });

  describe('quoteApi - 报价API', () => {
    it('list() - 应该获取报价列表', async () => {
      mock.onGet('/api/v1/sales/quotes').reply(200, {
        success: true,
        data: [{ id: 1, quote_no: 'Q001' }],
      });

      const response = await quoteApi.list({ status: 'DRAFT' });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建报价', async () => {
      const quote = { opportunity_id: 1, title: 'Quote 1' };
      mock.onPost('/api/v1/sales/quotes').reply(201, {
        success: true,
        data: { id: 1, ...quote },
      });

      const response = await quoteApi.create(quote);

      expect(response.status).toBe(201);
    });

    it('createVersion() - 应该创建报价版本', async () => {
      const version = { version_no: '2.0', changes: 'Updated pricing' };
      mock.onPost('/api/v1/sales/quotes/1/versions').reply(201, {
        success: true,
        data: { id: 2, ...version },
      });

      const response = await quoteApi.createVersion(1, version);

      expect(response.status).toBe(201);
    });

    it('getItems() - 应该获取报价条目', async () => {
      mock.onGet('/api/v1/sales/quotes/1/items').reply(200, {
        success: true,
        data: [{ id: 1, product: 'Product A' }],
      });

      const response = await quoteApi.getItems(1, 1);

      expect(response.status).toBe(200);
      expect(mock.history.get[0].params).toEqual({ version_id: 1 });
    });

    it('batchUpdateItems() - 应该批量更新条目', async () => {
      const items = [
        { id: 1, quantity: 10 },
        { id: 2, quantity: 5 },
      ];
      mock.onPut('/api/v1/sales/quotes/1/items/batch').reply(200, {
        success: true,
        data: items,
      });

      const response = await quoteApi.batchUpdateItems(1, items, 1);

      expect(response.status).toBe(200);
    });

    it('getCostBreakdown() - 应该获取成本明细', async () => {
      mock.onGet('/api/v1/sales/quotes/1/cost-breakdown').reply(200, {
        success: true,
        data: { material: 10000, labor: 5000 },
      });

      const response = await quoteApi.getCostBreakdown(1);

      expect(response.status).toBe(200);
    });

    it('startApproval() - 应该启动审批流程', async () => {
      mock.onPost('/api/v1/sales/quotes/1/approval/start').reply(200, {
        success: true,
        data: { approval_id: 1 },
      });

      const response = await quoteApi.startApproval(1);

      expect(response.status).toBe(200);
    });
  });

  describe('contractApi - 合同API', () => {
    it('list() - 应该获取合同列表', async () => {
      mock.onGet('/api/v1/sales/contracts').reply(200, {
        success: true,
        data: [{ id: 1, contract_no: 'C001' }],
      });

      const response = await contractApi.list({ status: 'SIGNED' });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建合同', async () => {
      const contract = { quote_id: 1, title: 'Contract 1' };
      mock.onPost('/api/v1/sales/contracts').reply(201, {
        success: true,
        data: { id: 1, ...contract },
      });

      const response = await contractApi.create(contract);

      expect(response.status).toBe(201);
    });

    it('sign() - 应该签署合同', async () => {
      const signData = { signed_date: '2024-01-01', signer: 'John Doe' };
      mock.onPost('/api/v1/sales/contracts/1/sign').reply(200, {
        success: true,
        data: { status: 'SIGNED' },
      });

      const response = await contractApi.sign(1, signData);

      expect(response.status).toBe(200);
    });

    it('createProject() - 应该从合同创建项目', async () => {
      const projectData = { name: 'New Project' };
      mock.onPost('/api/v1/sales/contracts/1/project').reply(201, {
        success: true,
        data: { project_id: 1 },
      });

      const response = await contractApi.createProject(1, projectData);

      expect(response.status).toBe(201);
    });
  });

  describe('invoiceApi - 发票API', () => {
    it('list() - 应该获取发票列表', async () => {
      mock.onGet('/api/v1/sales/invoices').reply(200, {
        success: true,
        data: [{ id: 1, invoice_no: 'INV001' }],
      });

      const response = await invoiceApi.list({ status: 'PENDING' });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建发票', async () => {
      const invoice = { contract_id: 1, amount: 10000 };
      mock.onPost('/api/v1/sales/invoices').reply(201, {
        success: true,
        data: { id: 1, ...invoice },
      });

      const response = await invoiceApi.create(invoice);

      expect(response.status).toBe(201);
    });

    it('issue() - 应该开具发票', async () => {
      const issueData = { issue_date: '2024-01-01' };
      mock.onPost('/api/v1/sales/invoices/1/issue').reply(200, {
        success: true,
        data: { status: 'ISSUED' },
      });

      const response = await invoiceApi.issue(1, issueData);

      expect(response.status).toBe(200);
    });

    it('receivePayment() - 应该记录收款', async () => {
      const paymentData = { amount: 10000, payment_date: '2024-01-01' };
      mock.onPost('/api/v1/sales/invoices/1/receive-payment').reply(200, {
        success: true,
        data: { received_amount: 10000 },
      });

      const response = await invoiceApi.receivePayment(1, paymentData);

      expect(response.status).toBe(200);
    });
  });

  describe('paymentApi - 付款API', () => {
    it('list() - 应该获取付款列表', async () => {
      mock.onGet('/api/v1/sales/payments').reply(200, {
        success: true,
        data: [{ id: 1, amount: 5000 }],
      });

      const response = await paymentApi.list({ status: 'PENDING' });

      expect(response.status).toBe(200);
    });

    it('getReminders() - 应该获取付款提醒', async () => {
      mock.onGet('/api/v1/sales/payments/reminders').reply(200, {
        success: true,
        data: [{ id: 1, due_date: '2024-01-15' }],
      });

      const response = await paymentApi.getReminders({ overdue: true });

      expect(response.status).toBe(200);
    });

    it('getStatistics() - 应该获取付款统计', async () => {
      mock.onGet('/api/v1/sales/payments/statistics').reply(200, {
        success: true,
        data: { total_paid: 50000, total_pending: 30000 },
      });

      const response = await paymentApi.getStatistics({ month: '2024-01' });

      expect(response.status).toBe(200);
    });
  });

  describe('salesStatisticsApi - 销售统计API', () => {
    it('funnel() - 应该获取销售漏斗数据', async () => {
      mock.onGet('/api/v1/sales/statistics/funnel').reply(200, {
        success: true,
        data: { stages: [] },
      });

      const response = await salesStatisticsApi.funnel({ year: 2024 });

      expect(response.status).toBe(200);
    });

    it('summary() - 应该获取销售汇总', async () => {
      mock.onGet('/api/v1/sales/statistics/summary').reply(200, {
        success: true,
        data: { total_revenue: 1000000 },
      });

      const response = await salesStatisticsApi.summary({ month: '2024-01' });

      expect(response.status).toBe(200);
    });

    it('prediction() - 应该获取销售预测', async () => {
      mock.onGet('/api/v1/sales/statistics/prediction').reply(200, {
        success: true,
        data: { predicted_revenue: 1200000 },
      });

      const response = await salesStatisticsApi.prediction({ months: 3 });

      expect(response.status).toBe(200);
    });

    it('predictionAccuracy() - 应该获取预测准确度', async () => {
      mock.onGet('/api/v1/sales/statistics/prediction/accuracy').reply(200, {
        success: true,
        data: { accuracy: 0.85 },
      });

      const response = await salesStatisticsApi.predictionAccuracy({
        period: '2024-Q1',
      });

      expect(response.status).toBe(200);
    });
  });

  describe('salesTemplateApi - 销售模板API', () => {
    it('listQuoteTemplates() - 应该获取报价模板列表', async () => {
      mock.onGet('/api/v1/sales/quote-templates').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Template 1' }],
      });

      const response = await salesTemplateApi.listQuoteTemplates({ type: 'STANDARD' });

      expect(response.status).toBe(200);
    });

    it('createCostTemplate() - 应该创建成本模板', async () => {
      const template = { name: 'Cost Template 1', items: [] };
      mock.onPost('/api/v1/sales/cost-templates').reply(201, {
        success: true,
        data: { id: 1, ...template },
      });

      const response = await salesTemplateApi.createCostTemplate(template);

      expect(response.status).toBe(201);
    });
  });

  describe('salesTeamApi - 销售团队API', () => {
    it('getTeam() - 应该获取团队列表', async () => {
      mock.onGet('/api/v1/sales/team').reply(200, {
        success: true,
        data: [{ id: 1, name: 'Sales Person 1' }],
      });

      const response = await salesTeamApi.getTeam({ department: 'SALES' });

      expect(response.status).toBe(200);
    });

    it('getRanking() - 应该获取销售排名', async () => {
      mock.onGet('/api/v1/sales/team/ranking').reply(200, {
        success: true,
        data: [{ user_id: 1, rank: 1, score: 95 }],
      });

      const response = await salesTeamApi.getRanking({ month: '2024-01' });

      expect(response.status).toBe(200);
    });

    it('updateRankingConfig() - 应该更新排名配置', async () => {
      const config = { weights: { revenue: 0.5, deals: 0.3 } };
      mock.onPut('/api/v1/sales/team/ranking/config').reply(200, {
        success: true,
        data: config,
      });

      const response = await salesTeamApi.updateRankingConfig(config);

      expect(response.status).toBe(200);
    });
  });

  describe('salesTargetApi - 销售目标API', () => {
    it('list() - 应该获取销售目标列表', async () => {
      mock.onGet('/api/v1/sales/targets').reply(200, {
        success: true,
        data: [{ id: 1, target_amount: 1000000 }],
      });

      const response = await salesTargetApi.list({ year: 2024 });

      expect(response.status).toBe(200);
    });

    it('create() - 应该创建销售目标', async () => {
      const target = { user_id: 1, target_amount: 500000, year: 2024 };
      mock.onPost('/api/v1/sales/targets').reply(201, {
        success: true,
        data: { id: 1, ...target },
      });

      const response = await salesTargetApi.create(target);

      expect(response.status).toBe(201);
    });

    it('delete() - 应该删除销售目标', async () => {
      mock.onDelete('/api/v1/sales/targets/1').reply(204);

      const response = await salesTargetApi.delete(1);

      expect(response.status).toBe(204);
    });
  });

  describe('healthApi - 健康度API', () => {
    it('getLeadHealth() - 应该获取线索健康度', async () => {
      mock.onGet('/api/v1/sales/health/lead/1').reply(200, {
        success: true,
        data: { health_score: 85, issues: [] },
      });

      const response = await healthApi.getLeadHealth(1);

      expect(response.status).toBe(200);
    });

    it('getPipelineHealth() - 应该获取销售管道健康度', async () => {
      mock.onGet('/api/v1/sales/health/pipeline').reply(200, {
        success: true,
        data: { overall_health: 'GOOD' },
      });

      const response = await healthApi.getPipelineHealth({ stage: 'ALL' });

      expect(response.status).toBe(200);
    });
  });

  describe('priorityApi - 优先级API', () => {
    it('calculateLeadPriority() - 应该计算线索优先级', async () => {
      mock.onPost('/api/v1/sales/leads/1/calculate-priority').reply(200, {
        success: true,
        data: { priority_score: 85 },
      });

      const response = await priorityApi.calculateLeadPriority(1);

      expect(response.status).toBe(200);
    });

    it('getKeyOpportunities() - 应该获取关键商机', async () => {
      mock.onGet('/api/v1/sales/opportunities/key-opportunities').reply(200, {
        success: true,
        data: [{ id: 1, priority: 'HIGH' }],
      });

      const response = await priorityApi.getKeyOpportunities();

      expect(response.status).toBe(200);
    });
  });

  describe('错误处理', () => {
    it('应该处理404错误', async () => {
      mock.onGet('/api/v1/sales/leads/999').reply(404, {
        success: false,
        message: 'Lead not found',
      });

      await expect(leadApi.get(999)).rejects.toThrow();
    });

    it('应该处理验证错误', async () => {
      mock.onPost('/api/v1/sales/leads').reply(422, {
        success: false,
        message: 'Validation failed',
        errors: { company: ['Company is required'] },
      });

      await expect(leadApi.create({})).rejects.toThrow();
    });

    it('应该处理权限错误', async () => {
      mock.onDelete('/api/v1/sales/leads/1').reply(403, {
        success: false,
        message: 'Permission denied',
      });

      await expect(leadApi.update(1, {})).rejects.toThrow();
    });
  });
});
