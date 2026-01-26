/**
 * 统一响应格式处理工具
 * 
 * 用于处理后端统一响应格式，支持新旧格式兼容
 */

/**
 * 从统一响应格式中提取数据
 * 
 * 支持两种格式：
 * 1. 新格式：{"success": true, "code": 200, "message": "...", "data": {...}}
 * 2. 旧格式：直接返回数据对象
 * 
 * @param {Object} responseData - API响应数据
 * @returns {*} 提取的数据对象
 */
export function extractData(responseData) {
  // 如果是新格式（有success字段）
  if (responseData && typeof responseData === 'object' && 'success' in responseData && 'data' in responseData) {
    return responseData.data;
  }
  // 如果是旧格式，直接返回
  return responseData;
}

/**
 * 从列表响应中提取items
 * 
 * 支持多种格式：
 * 1. 新格式（分页）：{"items": [...], "total": ..., "page": ...}
 * 2. 新格式（无分页）：{"items": [...], "total": ...}
 * 3. 新格式（SuccessResponse包装）：{"success": true, "data": {"items": [...], "total": ...}}
 * 4. 旧格式：直接返回列表或 {"items": [...]}
 * 
 * @param {Object|Array} responseData - API响应数据
 * @returns {Array} 提取的items数组
 */
export function extractItems(responseData) {
  // 如果直接是数组（旧格式）
  if (Array.isArray(responseData)) {
    return responseData;
  }

  // 如果是对象
  if (responseData && typeof responseData === 'object') {
    // 新格式：有items字段
    if ('items' in responseData) {
      return Array.isArray(responseData.items) ? responseData.items : [];
    }

    // 如果响应是SuccessResponse包装的ListResponse
    if ('success' in responseData && 'data' in responseData) {
      const data = responseData.data;
      if (Array.isArray(data)) {
        return data;
      }
      if (data && typeof data === 'object' && 'items' in data) {
        return Array.isArray(data.items) ? data.items : [];
      }
    }
  }

  return [];
}

/**
 * 从分页响应中提取分页信息
 * 
 * @param {Object} responseData - API响应数据
 * @returns {Object} 包含items、total、page、page_size的对象
 */
export function extractPaginatedData(responseData) {
  // 如果是SuccessResponse包装的PaginatedResponse
  if (responseData && typeof responseData === 'object' && 'success' in responseData && 'data' in responseData) {
    const data = responseData.data;
    if (data && typeof data === 'object' && 'items' in data) {
      return {
        items: Array.isArray(data.items) ? data.items : [],
        total: data.total || 0,
        page: data.page || 1,
        page_size: data.page_size || 20,
        pages: data.pages || Math.ceil((data.total || 0) / (data.page_size || 20)),
      };
    }
  }

  // 直接是PaginatedResponse格式
  if (responseData && typeof responseData === 'object' && 'items' in responseData) {
    return {
      items: Array.isArray(responseData.items) ? responseData.items : [],
      total: responseData.total || 0,
      page: responseData.page || 1,
      page_size: responseData.page_size || 20,
      pages: responseData.pages || Math.ceil((responseData.total || 0) / (responseData.page_size || 20)),
    };
  }

  // 旧格式：直接是数组
  if (Array.isArray(responseData)) {
    return {
      items: responseData,
      total: responseData.length,
      page: 1,
      page_size: responseData.length,
      pages: 1,
    };
  }

  // 默认返回空结果
  return {
    items: [],
    total: 0,
    page: 1,
    page_size: 20,
    pages: 0,
  };
}

/**
 * 从列表响应中提取列表数据（无分页）
 * 
 * @param {Object|Array} responseData - API响应数据
 * @returns {Object} 包含items和total的对象
 */
export function extractListData(responseData) {
  // 如果直接是数组（旧格式）
  if (Array.isArray(responseData)) {
    return {
      items: responseData,
      total: responseData.length,
    };
  }

  // 如果是SuccessResponse包装的ListResponse
  if (responseData && typeof responseData === 'object' && 'success' in responseData && 'data' in responseData) {
    const data = responseData.data;
    if (Array.isArray(data)) {
      return {
        items: data,
        total: data.length,
      };
    }
    if (data && typeof data === 'object' && 'items' in data) {
      return {
        items: Array.isArray(data.items) ? data.items : [],
        total: data.total || data.items.length || 0,
      };
    }
  }

  // 新格式（ListResponse）
  if (responseData && typeof responseData === 'object' && 'items' in responseData) {
    return {
      items: Array.isArray(responseData.items) ? responseData.items : [],
      total: responseData.total || responseData.items.length || 0,
    };
  }

  // 默认返回空结果
  return {
    items: [],
    total: 0,
  };
}

/**
 * 检查响应是否为成功响应
 * 
 * @param {Object} responseData - API响应数据
 * @returns {boolean} 是否为成功响应
 */
export function isSuccessResponse(responseData) {
  if (responseData && typeof responseData === 'object' && 'success' in responseData) {
    return responseData.success === true;
  }
  // 旧格式：没有success字段，假设成功（由HTTP状态码判断）
  return true;
}

/**
 * 获取响应消息
 * 
 * @param {Object} responseData - API响应数据
 * @returns {string} 响应消息
 */
export function getResponseMessage(responseData) {
  if (responseData && typeof responseData === 'object' && 'message' in responseData) {
    return responseData.message;
  }
  return '';
}

/**
 * 统一处理API响应（自动提取数据）
 * 
 * 根据响应类型自动提取数据：
 * - 单个对象：提取data字段
 * - 分页列表：提取items、total等
 * - 无分页列表：提取items、total
 * 
 * @param {Object} response - axios响应对象
 * @param {Object} options - 选项
 * @param {string} options.type - 响应类型：'single' | 'paginated' | 'list' | 'auto'
 * @returns {*} 提取的数据
 */
export function formatResponse(response, options = {}) {
  const { type = 'auto' } = options;
  const responseData = response?.data || response;

  switch (type) {
    case 'single':
      return extractData(responseData);
    case 'paginated':
      return extractPaginatedData(responseData);
    case 'list':
      return extractListData(responseData);
    case 'auto':
    default:
      // 自动判断：如果有items字段，认为是列表；否则认为是单个对象
      if (responseData && typeof responseData === 'object' && 'items' in responseData) {
        // 如果有page字段，认为是分页列表
        if ('page' in responseData) {
          return extractPaginatedData(responseData);
        }
        // 否则认为是无分页列表
        return extractListData(responseData);
      }
      // 单个对象
      return extractData(responseData);
  }
}
