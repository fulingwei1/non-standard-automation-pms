import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setupApiTest, teardownApiTest } from './_test-setup.js';

describe('presaleApi', () => {
  let mock;
  let presaleApi;
  let presalesIntegrationApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;

    const presalesModule = await import('../presales.js');
    presaleApi = presalesModule.presaleApi;
    presalesIntegrationApi = presalesModule.presalesIntegrationApi;

    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it('tickets.complete() - should send completion context as JSON body', async () => {
    mock.onPut('/api/v1/presale/tickets/42/complete').reply((config) => {
      expect(config.params).toBeUndefined();
      expect(JSON.parse(config.data)).toEqual({
        actual_hours: 8.5,
        completion_note: '方案可行，建议进入报价',
      });
      return [
        200,
        {
          id: 42,
          status: 'COMPLETED',
          actual_hours: 8.5,
          progress_note: '方案可行，建议进入报价',
        },
      ];
    });

    const response = await presaleApi.tickets.complete(42, {
      actualHours: 8.5,
      completion_note: '方案可行，建议进入报价',
    });

    expect(response.data.status).toBe('COMPLETED');
    expect(response.data.progress_note).toBe('方案可行，建议进入报价');
  });

  it('tickets.createDeliverable() - should post deliverable payload to ticket route', async () => {
    const payload = {
      deliverable_name: '初版技术方案',
      deliverable_type: 'SOLUTION',
      file_path: '/files/solution-v1.pdf',
      file_url: 'https://files.example.com/solution-v1.pdf',
      description: '方案初稿',
    };

    mock.onPost('/api/v1/presale/tickets/42/deliverables').reply((config) => {
      expect(JSON.parse(config.data)).toEqual(payload);
      return [201, { id: 7, ticket_id: 42, ...payload }];
    });

    const response = await presaleApi.tickets.createDeliverable(42, payload);

    expect(response.data.id).toBe(7);
    expect(response.data.ticket_id).toBe(42);
  });

  it('createProjectFromLead() - should post approved lead payload to compatibility route', async () => {
    const payload = {
      lead_id: 'XS260607001',
      lead_name: '自动化测试站',
      customer_name: '测试客户',
      salesperson_id: 1,
      salesperson_name: '销售员',
      decision: 'GO',
      evaluation_score: 82,
      dimension_scores: {
        requirement_maturity: 85,
        technical_feasibility: 80,
        business_feasibility: 78,
        delivery_risk: 82,
        customer_relationship: 86,
      },
    };

    mock.onPost('/api/v1/presales/from-lead').reply((config) => {
      expect(JSON.parse(config.data)).toEqual(payload);
      return [200, { success: true, data: { project_code: 'PJ260607001' } }];
    });

    const response = await presalesIntegrationApi.createProjectFromLead(payload);

    expect(response.data.data.project_code).toBe('PJ260607001');
  });
});
