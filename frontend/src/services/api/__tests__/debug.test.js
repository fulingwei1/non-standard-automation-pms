import { describe, it, expect, beforeEach, vi } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

describe('Debug raw axios mock', () => {
  it('should test raw axios mock', async () => {
    const testApi = axios.create({
      baseURL: '/api/v1',
    });

    const mock = new MockAdapter(testApi);
    
    mock.onGet('/test').reply(200, { success: true, data: [{ id: 1 }] });

    const response = await testApi.get('/test');
    console.log('Response keys:', Object.keys(response));
    console.log('Response:', response);
    
    expect(response.status).toBe(200);
  });
});
