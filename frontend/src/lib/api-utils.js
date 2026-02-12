/**
 * API请求优化工具
 * 包含请求缓存、防抖、节流等功能
 */

import axios from 'axios';

// ============================================
// 请求缓存管理器
// ============================================

class RequestCache {
  constructor() {
    this.cache = new Map();
    this.defaultTTL = 5 * 60 * 1000; // 默认5分钟
  }

  /**
   * 生成缓存键
   */
  generateKey(url, params = {}) {
    return `${url}?${JSON.stringify(params)}`;
  }

  /**
   * 获取缓存
   */
  get(url, params = {}) {
    const key = this.generateKey(url, params);
    const cached = this.cache.get(key);

    if (!cached) {
      return null;
    }

    // 检查是否过期
    if (Date.now() > cached.expireTime) {
      this.cache.delete(key);
      return null;
    }

    return cached.data;
  }

  /**
   * 设置缓存
   */
  set(url, params = {}, data, ttl = this.defaultTTL) {
    const key = this.generateKey(url, params);
    this.cache.set(key, {
      data,
      expireTime: Date.now() + ttl,
    });
  }

  /**
   * 删除缓存
   */
  delete(url, params = {}) {
    const key = this.generateKey(url, params);
    this.cache.delete(key);
  }

  /**
   * 删除匹配模式的缓存
   */
  deletePattern(pattern) {
    for (const key of this.cache.keys()) {
      if (key.startsWith(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * 清空所有缓存
   */
  clear() {
    this.cache.clear();
  }

  /**
   * 获取缓存大小
   */
  size() {
    return this.cache.size;
  }
}

// 全局缓存实例
const requestCache = new RequestCache();

// ============================================
// 防抖函数
// ============================================

export function debounce(func, wait = 300) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// ============================================
// 节流函数
// ============================================

export function throttle(func, limit = 300) {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// ============================================
// 请求重试装饰器
// ============================================

export function withRetry(requestFn, maxRetries = 3, delay = 1000) {
  return async (...args) => {
    let lastError;

    for (let i = 0; i < maxRetries; i++) {
      try {
        return await requestFn(...args);
      } catch (error) {
        lastError = error;

        // 如果是客户端错误（4xx），不重试
        if (error.response && error.response.status >= 400 && error.response.status < 500) {
          throw error;
        }

        // 最后一次重试不等待
        if (i < maxRetries - 1) {
          await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
        }
      }
    }

    throw lastError;
  };
}

// ============================================
// 缓存的API请求
// ============================================

export async function cachedRequest(
  url,
  options = {},
  cacheOptions = { enabled: true, ttl: null }
) {
  const { enabled = true, ttl = null } = cacheOptions;
  const params = options.params || {};

  // 如果启用缓存，尝试从缓存获取
  if (enabled) {
    const cachedData = requestCache.get(url, params);
    if (cachedData) {
      return { data: cachedData, fromCache: true };
    }
  }

  // 发起请求
  const response = await axios(url, options);

  // 如果启用缓存，将结果存入缓存
  if (enabled) {
    requestCache.set(url, params, response.data, ttl);
  }

  return { data: response.data, fromCache: false };
}

/**
 * ============================================
 * 并发请求控制器（限制同时请求数）
 * ============================================
 */

class RequestQueue {
  constructor(maxConcurrent = 5) {
    this.maxConcurrent = maxConcurrent;
    this.queue = [];
    this.activeCount = 0;
  }

  /**
   * 添加请求到队列
   */
  async add(requestFn) {
    return new Promise((resolve, reject) => {
      this.queue.push({ requestFn, resolve, reject });
      this.process();
    });
  }

  /**
   * 处理队列
   */
  async process() {
    if (this.activeCount >= this.maxConcurrent || this.queue.length === 0) {
      return;
    }

    this.activeCount++;
    const { requestFn, resolve, reject } = this.queue.shift();

    try {
      const result = await requestFn();
      resolve(result);
    } catch (error) {
      reject(error);
    } finally {
      this.activeCount--;
      this.process();
    }
  }

  /**
   * 清空队列
   */
  clear() {
    this.queue.forEach(({ reject }) => {
      reject(new Error('Request cancelled'));
    });
    this.queue = [];
  }
}

// 全局请求队列实例
const requestQueue = new RequestQueue(5);

/**
 * ============================================
 * 批量请求工具
 * ============================================
 */

export async function batchRequest(requests, concurrency = 5) {
  const batchQueue = new RequestQueue(concurrency);

  const promises = requests.map(requestFn =>
    batchQueue.add(requestFn)
  );

  const batchResults = await Promise.all(promises);
  return batchResults;
}

/**
 * ============================================
 * 取消令牌管理器
 * ============================================
 */

class CancelTokenManager {
  constructor() {
    this.tokens = new Map();
  }

  /**
   * 创建取消令牌
   */
  create(key) {
    // 如果已存在，先取消
    if (this.tokens.has(key)) {
      this.cancel(key);
    }

    const source = axios.CancelToken.source();
    this.tokens.set(key, source);
    return source;
  }

  /**
   * 取消请求
   */
  cancel(key) {
    const source = this.tokens.get(key);
    if (source) {
      source.cancel('Request cancelled');
      this.tokens.delete(key);
    }
  }

  /**
   * 取消所有请求
   */
  cancelAll() {
    this.tokens.forEach((source) => {
      source.cancel('Request cancelled');
    });
    this.tokens.clear();
  }
}

// 全局取消令牌管理器实例
const cancelTokenManager = new CancelTokenManager();

/**
 * ============================================
 * 带缓存的Axios实例
 * ============================================
 */

export const cachedAxios = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
});

// 请求拦截器
cachedAxios.interceptors.request.use(
  (config) => {
    // 添加时间戳防止缓存
    if (!config.params) {
      config.params = {};
    }
    config.params._t = Date.now();

    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
cachedAxios.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    // 请求取消
    if (axios.isCancel(error)) {
      return Promise.reject(error);
    }

    // 401未授权，跳转登录
    if (error.response && error.response.status === 401) {
      // TODO: 跳转到登录页
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

/**
 * ============================================
 * 导出工具
 * ============================================
 */

export {
  requestCache,
  requestQueue,
  cancelTokenManager,
  RequestCache,
  RequestQueue,
  CancelTokenManager,
};

// 默认导出
export default {
  debounce,
  throttle,
  withRetry,
  cachedRequest,
  batchRequest,
  cachedAxios,
  requestCache,
  requestQueue,
  cancelTokenManager,
};
