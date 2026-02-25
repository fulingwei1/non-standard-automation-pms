/**
 * API Client 核心功能测试
 * 测试范围：
 * - Request interceptor (token处理)
 * - Response interceptor (统一响应格式处理)
 * - 错误处理 (4xx, 5xx)
 * - 公开端点识别
 * - 401错误的特殊处理
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { setupApiTest, teardownApiTest } from './_test-setup.js';

describe('API Client', () => {
  let api;
  let mock;

  beforeEach(async () => {
    // 清除模块缓存
    vi.resetModules();
    
    // 重新导入client - 每次测试都获取新实例
    const clientModule = await import('../client.js');
    api = clientModule.default || clientModule.api;
    
    // 创建MockAdapter实例
    mock = new MockAdapter(api);
    
    // 清空localStorage
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    if (mock) {
      mock.restore();
    }
  });

  describe('Request Interceptor - Token处理', () => {
    it('应该为非公开API添加Authorization header', async () => {
      const token = 'test-token-12345';
      localStorage.setItem('token', token);

      mock.onGet('/api/v1/projects').reply(200, { success: true, data: [] });

      await api.get('/projects');

      expect(mock.history.get[0].headers.Authorization).toBe(`Bearer ${token}`);
    });

    it('应该跳过公开API的token验证', async () => {
      mock.onPost('/api/v1/auth/login').reply(200, { success: true, data: {} });

      await api.post('/auth/login', { username: 'test', password: 'test' });

      expect(mock.history.post[0].headers.Authorization).toBeUndefined();
    });

    it('应该正确识别所有公开端点', async () => {
      const publicEndpoints = [
        '/auth/login',
        '/auth/register',
        '/health',
        '/docs',
        '/openapi.json',
      ];

      for (const endpoint of publicEndpoints) {
        mock.onGet(`/api/v1${endpoint}`).reply(200, { success: true });
        await api.get(endpoint);
        const lastRequest = mock.history.get[mock.history.get.length - 1];
        expect(lastRequest.headers.Authorization).toBeUndefined();
      }
    });

    it('应该处理演示token (demo_token_*) 而不发送Authorization', async () => {
      const demoToken = 'demo_token_user123';
      localStorage.setItem('token', demoToken);

      mock.onGet('/api/v1/projects').reply(200, { success: true, data: [] });

      await api.get('/projects');

      expect(mock.history.get[0].headers.Authorization).toBeUndefined();
    });

    it('应该在无token且非公开API时发出警告', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      mock.onGet('/api/v1/projects').reply(200, { success: true, data: [] });

      await api.get('/projects');

      expect(consoleWarnSpy).toHaveBeenCalled();
      consoleWarnSpy.mockRestore();
    });
  });

  describe('Response Interceptor - 统一响应格式', () => {
    it('应该正确提取统一响应格式的data字段 (success字段)', async () => {
      const mockData = { id: 1, name: 'Test' };
      mock.onGet('/api/v1/test').reply(200, {
        success: true,
        data: mockData,
        message: 'Success',
      });

      const response = await api.get('/test');

      expect(response.formatted).toEqual(mockData);
      expect(response.data.success).toBe(true);
    });

    it('应该正确提取统一响应格式的data字段 (code字段)', async () => {
      const mockData = { id: 2, name: 'Test2' };
      mock.onGet('/api/v1/test').reply(200, {
        code: 200,
        data: mockData,
        message: 'Success',
      });

      const response = await api.get('/test');

      expect(response.formatted).toEqual(mockData);
    });

    it('应该处理无包装的直接响应', async () => {
      const mockData = { id: 3, name: 'Direct' };
      mock.onGet('/api/v1/test').reply(200, mockData);

      const response = await api.get('/test');

      expect(response.formatted).toEqual(mockData);
    });

    it('应该处理数组响应', async () => {
      const mockData = [{ id: 1 }, { id: 2 }];
      mock.onGet('/api/v1/test').reply(200, mockData);

      const response = await api.get('/test');

      expect(response.formatted).toEqual(mockData);
    });
  });

  describe('Error Handling - 错误处理', () => {
    it('应该处理4xx客户端错误', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mock.onGet('/api/v1/test').reply(400, {
        success: false,
        message: 'Bad Request',
      });

      await expect(api.get('/test')).rejects.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalled();
      
      consoleErrorSpy.mockRestore();
    });

    it('应该处理5xx服务器错误', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      mock.onGet('/api/v1/test').reply(500, {
        success: false,
        message: 'Internal Server Error',
      });

      await expect(api.get('/test')).rejects.toThrow();
      expect(consoleErrorSpy).toHaveBeenCalled();
      
      consoleErrorSpy.mockRestore();
    });

    it('应该处理网络错误', async () => {
      mock.onGet('/api/v1/test').networkError();

      await expect(api.get('/test')).rejects.toThrow();
    });

    it('应该处理超时错误', async () => {
      mock.onGet('/api/v1/test').timeout();

      await expect(api.get('/test')).rejects.toThrow();
    });
  });

  describe('401 Unauthorized 特殊处理', () => {
    beforeEach(() => {
      // Mock window.location
      delete window.location;
      window.location = { pathname: '/dashboard', href: '/' };
    });

    it('应该在认证API返回401时清除token并重定向', async () => {
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      localStorage.setItem('token', 'invalid-token');
      localStorage.setItem('user', JSON.stringify({ id: 1 }));

      mock.onGet('/api/v1/auth/me').reply(401);

      await expect(api.get('/auth/me')).rejects.toThrow();

      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      
      consoleLogSpy.mockRestore();
    });

    it('应该在非认证API返回401时保持token (使用mock数据)', async () => {
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const token = 'valid-token';
      localStorage.setItem('token', token);

      mock.onGet('/api/v1/projects').reply(401);

      await expect(api.get('/projects')).rejects.toThrow();

      // 非认证API的401不应清除token
      expect(localStorage.getItem('token')).toBe(token);
      
      consoleLogSpy.mockRestore();
    });

    it('应该静默处理演示账号的401错误', async () => {
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      const demoToken = 'demo_token_user123';
      localStorage.setItem('token', demoToken);

      mock.onGet('/api/v1/projects').reply(401);

      await expect(api.get('/projects')).rejects.toThrow();

      // 演示token不应被删除
      expect(localStorage.getItem('token')).toBe(demoToken);
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('演示账号')
      );
      
      consoleLogSpy.mockRestore();
    });
  });

  describe('API配置', () => {
    it('应该使用正确的baseURL', () => {
      expect(api.defaults.baseURL).toBe('/api/v1');
    });

    it('应该设置正确的Content-Type', () => {
      expect(api.defaults.headers['Content-Type']).toBe('application/json');
    });

    it('应该设置5秒超时', () => {
      expect(api.defaults.timeout).toBe(5000);
    });
  });

  describe('调试日志', () => {
    it('应该记录所有API请求', async () => {
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      mock.onGet('/api/v1/test').reply(200, { success: true });

      await api.get('/test');

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('[API请求]'),
        expect.anything()
      );
      
      consoleLogSpy.mockRestore();
    });
  });
});
