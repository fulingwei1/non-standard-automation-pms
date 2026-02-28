/**
 * Constants Index - 统一常量导出入口
 * 
 * 注意：由于各模块存在大量同名导出（如 getStatusColor, TABLE_CONFIG 等），
 * 不能使用 export * 全量导出。各页面应直接从具体模块文件导入。
 * 
 * 此 index 仅导出通用常量（common.js），供历史代码兼容使用。
 */

// 通用常量（common.js 是基础）
export * from './common';

// projectDetail 中的 PROJECT_STATUS 更完整
export { PROJECT_STATUS } from './projectDetail';
