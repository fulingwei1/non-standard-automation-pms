/**
 * 测试辅助工具
 * 用于设置API测试的通用配置
 */

import { vi } from 'vitest';

// 取消setupTests中对client的mock
vi.unmock('../client.js');

/**
 * 设置API测试环境
 * @returns {Promise<{api, mock}>}
 */
export async function setupApiTest() {
  vi.resetModules();
  
  // 动态导入client模块
  const clientModule = await import('../client.js');
  const api = clientModule.api;
  
  // 动态导入MockAdapter
  const { default: MockAdapter } = await import('axios-mock-adapter');
  const mock = new MockAdapter(api);
  
  vi.clearAllMocks();
  
  return { api, mock };
}

/**
 * 清理API测试环境
 * @param {MockAdapter} mock 
 */
export function teardownApiTest(mock) {
  if (mock) {
    mock.restore();
  }
}
