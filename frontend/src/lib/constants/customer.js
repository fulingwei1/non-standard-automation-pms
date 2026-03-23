/**
 * 向后兼容：重新导出所有客户常量
 * 实际实现已拆分到 customer/ 目录
 */
export * from './customer/index';
export { default } from './customer/index';
