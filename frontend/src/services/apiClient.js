// API Client - 统一的 API 调用客户端
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// API 请求实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 自动添加 token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  (response) => {
    const { data, status } = response;

    if (status >= 200 && status < 300) {
      return response;
    }

    // 统一错误处理
    const errorMap = {
      401: '未授权，请重新登录',
      403: '权限不足',
      404: '资源不存在',
      422: '请求参数错误',
      500: '服务器内部错误',
    };

    const message = data?.message || errorMap[status] || '请求失败';
    console.error('API Error:', status, message);

    return Promise.reject({
      status,
      message,
      data: data?.data,
    });
  }
);

// 导出
export { apiClient };
export default apiClient;
