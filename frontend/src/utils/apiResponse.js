/**
 * API响应处理辅助函数
 * 
 * 提供便捷的API响应处理方法，自动处理统一响应格式
 */

import { extractData, extractItems, extractPaginatedData, extractListData } from './responseFormatter.js';

/**
 * 处理单个对象响应
 * 
 * @param {Object} response - axios响应对象
 * @returns {*} 提取的数据对象
 */
export function getResponseData(response) {
  const responseData = response?.data || response;
  return extractData(responseData);
}

/**
 * 处理分页列表响应
 * 
 * @param {Object} response - axios响应对象
 * @returns {Object} 包含items、total、page等字段的对象
 */
export function getPaginatedResponse(response) {
  const responseData = response?.data || response;
  return extractPaginatedData(responseData);
}

/**
 * 处理列表响应（无分页）
 * 
 * @param {Object} response - axios响应对象
 * @returns {Object} 包含items和total的对象
 */
export function getListResponse(response) {
  const responseData = response?.data || response;
  return extractListData(responseData);
}

/**
 * 处理列表响应（自动判断分页）
 * 
 * @param {Object} response - axios响应对象
 * @returns {Object|Array} 提取的列表数据
 */
export function getItems(response) {
  const responseData = response?.data || response;
  return extractItems(responseData);
}

/**
 * 兼容旧代码的响应处理
 * 
 * 自动处理新旧格式，返回与旧代码兼容的数据结构
 * 
 * @param {Object} response - axios响应对象
 * @param {Object} options - 选项
 * @param {string} options.type - 响应类型：'single' | 'paginated' | 'list' | 'items'
 * @returns {*} 处理后的数据
 */
export function handleResponse(response, options = {}) {
  const { type = 'auto' } = options;
  const responseData = response?.data || response;

  switch (type) {
    case 'single':
      return getResponseData(response);
    case 'paginated':
      return getPaginatedResponse(response);
    case 'list':
      return getListResponse(response);
    case 'items':
      return getItems(response);
    case 'auto':
    default:
      // 自动判断
      if (responseData && typeof responseData === 'object' && 'items' in responseData) {
        // 如果有page字段，认为是分页列表
        if ('page' in responseData) {
          return getPaginatedResponse(response);
        }
        // 否则认为是无分页列表
        return getListResponse(response);
      }
      // 单个对象
      return getResponseData(response);
  }
}

/**
 * 兼容旧代码的便捷方法
 * 
 * 保持与旧代码的兼容性：response.data?.items || response.data || []
 */
export function getItemsCompat(response) {
  const responseData = response?.data || response;
  
  // 尝试提取items
  const items = extractItems(responseData);
  if (items.length > 0) {
    return items;
  }
  
  // 如果是数组，直接返回
  if (Array.isArray(responseData)) {
    return responseData;
  }
  
  // 如果是对象但没有items，尝试提取data
  if (responseData && typeof responseData === 'object' && 'data' in responseData) {
    const data = responseData.data;
    if (Array.isArray(data)) {
      return data;
    }
  }
  
  // 默认返回空数组
  return [];
}
