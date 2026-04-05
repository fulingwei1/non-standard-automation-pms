import { describe, it, expect, beforeEach, vi } from 'vitest';
import MockAdapter from 'axios-mock-adapter';

describe('Debug client.js axios mock', () => {
  it('should test client.js axios with mock', async () => {
    // 直接导入 client.js
    const { default: api } = await import('../client.js');
    console.log('Client api:', api);
    console.log('Client api defaults:', api.defaults);
    
    const mock = new MockAdapter(api);
    
    mock.onGet('/test').reply(200, { success: true, data: [{ id: 1 }] });

    const response = await api.get('/test');
    console.log('Response keys:', Object.keys(response));
    console.log('Response status:', response.status);
    console.log('Response:', response);
    
    expect(response.status).toBe(200);
  });
});
