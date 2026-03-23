import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { setupApiTest, teardownApiTest } from './_test-setup.js';

describe('marginPredictionApi', () => {
  let mock;
  let marginPredictionApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;

    const marginPredictionModule = await import('../marginPrediction.js');
    marginPredictionApi = marginPredictionModule.marginPredictionApi;

    localStorage.setItem('token', 'test-token');
    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it('historical() should request the historical margin summary', async () => {
    mock.onGet('/api/v1/margin-prediction/historical').reply(200, { success: true, data: {} });

    const response = await marginPredictionApi.historical();

    expect(response.status).toBe(200);
    expect(mock.history.get[0].url).toBe('/margin-prediction/historical');
  });

  it('predict() should send query params to the prediction endpoint', async () => {
    mock.onGet('/api/v1/margin-prediction/predict').reply(200, { success: true, data: {} });

    const response = await marginPredictionApi.predict({ contract_amount: 1000000, project_complexity: 'MEDIUM' });

    expect(response.status).toBe(200);
    expect(mock.history.get[0].params).toEqual({
      contract_amount: 1000000,
      project_complexity: 'MEDIUM',
    });
  });

  it('variance() should request the variance analysis payload', async () => {
    mock.onGet('/api/v1/margin-prediction/variance').reply(200, { success: true, data: {} });

    const response = await marginPredictionApi.variance();

    expect(response.status).toBe(200);
    expect(mock.history.get[0].url).toBe('/margin-prediction/variance');
  });

  // getBomCosts 方法已从 marginPredictionApi 中移除，跳过该测试
  it.skip('getBomCosts() should request a project BOM cost summary', async () => {});
});
