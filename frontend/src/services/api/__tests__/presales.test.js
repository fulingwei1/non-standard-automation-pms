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
});
