import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setupApiTest, teardownApiTest } from './_test-setup.js';

describe('presaleApi', () => {
  let mock;
  let presaleApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;

    const presalesModule = await import('../presales.js');
    presaleApi = presalesModule.presaleApi;

    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it('tickets.complete() - should send actual_hours as query params', async () => {
    mock.onPut('/api/v1/presale/tickets/42/complete').reply((config) => {
      expect(config.params).toEqual({ actual_hours: 8.5 });
      expect(config.data).toBeUndefined();
      return [200, { id: 42, status: 'COMPLETED', actual_hours: 8.5 }];
    });

    const response = await presaleApi.tickets.complete(42, { actualHours: 8.5 });

    expect(response.data.status).toBe('COMPLETED');
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
});
