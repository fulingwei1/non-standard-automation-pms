import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { setupApiTest, teardownApiTest } from './_test-setup.js';

describe('solutionApi', () => {
  let mock;
  let solutionApi;

  beforeEach(async () => {
    const setup = await setupApiTest();
    mock = setup.mock;

    const solutionModule = await import('../solution.js');
    solutionApi = solutionModule.solutionApi;

    vi.clearAllMocks();
  });

  afterEach(() => {
    teardownApiTest(mock);
  });

  it('list() should use the registered presale proposal solution route', async () => {
    mock.onGet('/api/v1/presale/proposals/solutions').reply((config) => {
      expect(config.params).toEqual({ project_id: 7 });
      return [200, { items: [{ id: 1, name: '项目方案' }], total: 1 }];
    });

    const response = await solutionApi.list({ project_id: 7 });

    expect(response.data.items[0].name).toBe('项目方案');
  });
});
