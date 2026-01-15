/**
 * Meeting Management Constants
 * 会议管理系统常量配置
 */

export const MEETING_TYPES = {
  REGULAR: { value: 'regular', label: '常规会议', color: '#1890ff' },
  PROJECT: { value: 'project', label: '项目会议', color: '#52c41a' },
  TRAINING: { value: 'training', label: '培训会议', color: '#722ed1' },
  REVIEW: { value: 'review', label: '评审会议', color: '#faad14' },
  BRAINSTORM: { value: 'brainstorm', label: '头脑风暴', color: '#13c2c2' },
  CLIENT: { value: 'client', label: '客户会议', color: '#eb2f96' }
};

export const MEETING_STATUS = {
  SCHEDULED: { value: 'scheduled', label: '已安排', color: '#1890ff' },
  IN_PROGRESS: { value: 'in_progress', label: '进行中', color: '#52c41a' },
  COMPLETED: { value: 'completed', label: '已完成', color: '#8c8c8c' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: '#ff4d4f' },
  POSTPONED: { value: 'postponed', label: '已延期', color: '#faad14' }
};