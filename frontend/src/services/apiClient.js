// API Client - 统一路由到具备完整 Token 无感刷新与请求重试的统一客户端 (api/client)
import api from "./api/client";

// 向后兼容现有导入: import apiClient from './apiClient' 或 import { apiClient } from './apiClient'
export const apiClient = api;
export default api;
