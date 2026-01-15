/**
 * Customer Service Dashboard Components
 * 客户服务仪表板组件导出
 */

// 导出统计卡片组件
export { ServiceStatsCard } from './ServiceStatsCard';

// 导出工单队列组件
export { TicketQueue } from './TicketQueue';

// 导出团队绩效组件
export { TeamPerformance } from './TeamPerformance';

// 导出常量配置
export {
  customerStatusConfigs,
  servicePriorityConfigs,
  serviceTypeConfigs,
  satisfactionLevelConfigs,
  serviceChannelConfigs,
  serviceStatusConfigs,
  serviceMetricConfigs,
  customerServiceTabConfigs,
  calculateServiceStats,
  formatCustomerStatus,
  formatServicePriority,
  formatServiceType,
  formatSatisfactionLevel,
  formatServiceChannel,
  formatServiceStatus,
  filterTicketsByStatus,
  filterTicketsByPriority,
  filterTicketsByType,
  filterTicketsByCustomer,
  sortByPriority,
  sortByCreateTime,
  sortByResolutionTime,
} from './customerServiceConstants';

// 默认导出
export default {
  ServiceStatsCard,
  TicketQueue,
  TeamPerformance,
  customerStatusConfigs,
  servicePriorityConfigs,
  serviceTypeConfigs,
  satisfactionLevelConfigs,
  serviceChannelConfigs,
  serviceStatusConfigs,
  serviceMetricConfigs,
  customerServiceTabConfigs,
  calculateServiceStats,
  formatCustomerStatus,
  formatServicePriority,
  formatServiceType,
  formatSatisfactionLevel,
  formatServiceChannel,
  formatServiceStatus,
  filterTicketsByStatus,
  filterTicketsByPriority,
  filterTicketsByType,
  filterTicketsByCustomer,
  sortByPriority,
  sortByCreateTime,
  sortByResolutionTime,
};