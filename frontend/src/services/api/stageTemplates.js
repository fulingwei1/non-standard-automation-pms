/**
 * 阶段模板管理 API
 *
 * 提供项目阶段模板的 CRUD、复制、导入导出等功能
 */
import { api } from "./client.js";

export const stageTemplateApi = {
  // ==================== 模板管理 ====================

  /**
   * 获取模板列表
   * @param {Object} params - 查询参数
   * @param {string} params.project_type - 项目类型筛选
   * @param {boolean} params.is_active - 是否启用
   * @param {boolean} params.include_stages - 是否包含阶段信息
   */
  list: (params) => api.get("/stage-templates/", { params }),

  /**
   * 获取模板详情
   * @param {number} templateId - 模板ID
   */
  get: (templateId) => api.get(`/stage-templates/${templateId}`),

  /**
   * 创建模板
   * @param {Object} data - 模板数据
   */
  create: (data) => api.post("/stage-templates/", data),

  /**
   * 更新模板
   * @param {number} templateId - 模板ID
   * @param {Object} data - 更新数据
   */
  update: (templateId, data) => api.put(`/stage-templates/${templateId}`, data),

  /**
   * 删除模板
   * @param {number} templateId - 模板ID
   */
  delete: (templateId) => api.delete(`/stage-templates/${templateId}`),

  /**
   * 复制模板
   * @param {number} templateId - 模板ID
   * @param {Object} data - 复制参数
   * @param {string} data.new_code - 新模板编码
   * @param {string} data.new_name - 新模板名称
   */
  copy: (templateId, data) => api.post(`/stage-templates/${templateId}/copy`, data),

  /**
   * 设置为默认模板
   * @param {number} templateId - 模板ID
   */
  setDefault: (templateId) => api.post(`/stage-templates/${templateId}/set-default`),

  /**
   * 获取默认模板
   * @param {string} projectType - 项目类型
   */
  getDefault: (projectType) => api.get(`/stage-templates/default/${projectType}`),

  /**
   * 导出模板
   * @param {number} templateId - 模板ID
   */
  export: (templateId) => api.get(`/stage-templates/${templateId}/export`),

  /**
   * 导入模板
   * @param {Object} data - 导入数据
   */
  import: (data) => api.post("/stage-templates/import", data),

  // ==================== 阶段定义管理 ====================

  stages: {
    /**
     * 添加阶段定义
     * @param {number} templateId - 模板ID
     * @param {Object} data - 阶段数据
     */
    add: (templateId, data) => api.post(`/stage-templates/${templateId}/stages`, data),

    /**
     * 更新阶段定义
     * @param {number} stageId - 阶段ID
     * @param {Object} data - 更新数据
     */
    update: (stageId, data) => api.put(`/stage-templates/stages/${stageId}`, data),

    /**
     * 删除阶段定义
     * @param {number} stageId - 阶段ID
     */
    delete: (stageId) => api.delete(`/stage-templates/stages/${stageId}`),

    /**
     * 重新排序阶段
     * @param {number} templateId - 模板ID
     * @param {Object} data - 排序数据
     * @param {number[]} data.stage_ids - 阶段ID列表
     */
    reorder: (templateId, data) => api.post(`/stage-templates/${templateId}/stages/reorder`, data),
  },

  // ==================== 节点定义管理 ====================

  nodes: {
    /**
     * 添加节点定义
     * @param {number} stageId - 阶段ID
     * @param {Object} data - 节点数据
     */
    add: (stageId, data) => api.post(`/stage-templates/stages/${stageId}/nodes`, data),

    /**
     * 更新节点定义
     * @param {number} nodeId - 节点ID
     * @param {Object} data - 更新数据
     */
    update: (nodeId, data) => api.put(`/stage-templates/nodes/${nodeId}`, data),

    /**
     * 删除节点定义
     * @param {number} nodeId - 节点ID
     */
    delete: (nodeId) => api.delete(`/stage-templates/nodes/${nodeId}`),

    /**
     * 重新排序节点
     * @param {number} stageId - 阶段ID
     * @param {Object} data - 排序数据
     * @param {number[]} data.node_ids - 节点ID列表
     */
    reorder: (stageId, data) => api.post(`/stage-templates/stages/${stageId}/nodes/reorder`, data),

    /**
     * 设置节点依赖关系
     * @param {number} nodeId - 节点ID
     * @param {Object} data - 依赖数据
     * @param {number[]} data.dependency_node_ids - 依赖节点ID列表
     */
    setDependencies: (nodeId, data) => api.put(`/stage-templates/nodes/${nodeId}/dependencies`, data),
  },
};
