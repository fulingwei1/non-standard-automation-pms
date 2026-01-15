/**
 * Knowledge Base Constants
 * 知识库管理系统常量配置
 */

export const KNOWLEDGE_TYPES = {
  SOLUTION: { value: 'solution', label: '历史方案', icon: '🏗️', color: '#1890ff' },
  PRODUCT: { value: 'product', label: '产品知识', icon: '📦', color: '#52c41a' },
  PROCESS: { value: 'process', label: '工艺知识', icon: '⚙️', color: '#722ed1' },
  COMPETITOR: { value: 'competitor', label: '竞品情报', icon: '🔍', color: '#faad14' },
  TEMPLATE: { value: 'template', label: '模板库', icon: '📋', color: '#13c2c2' },
  TECHNICAL: { value: 'technical', label: '技术文档', icon: '📖', color: '#eb2f96' }
};

export const FILE_TYPES = {
  DOCUMENT: { value: 'document', label: '文档', extensions: ['.pdf', '.doc', '.docx'], icon: '📄' },
  IMAGE: { value: 'image', label: '图片', extensions: ['.jpg', '.jpeg', '.png', '.gif'], icon: '🖼️' },
  VIDEO: { value: 'video', label: '视频', extensions: ['.mp4', '.avi', '.mov'], icon: '🎥' },
  SPREADSHEET: { value: 'spreadsheet', label: '表格', extensions: ['.xls', '.xlsx', '.csv'], icon: '📊' },
  PRESENTATION: { value: 'presentation', label: '演示文稿', extensions: ['.ppt', '.pptx'], icon: '📽️' },
  ARCHIVE: { value: 'archive', label: '压缩包', extensions: ['.zip', '.rar', '.7z'], icon: '🗜️' }
};

export const ACCESS_LEVELS = {
  PUBLIC: { value: 'public', label: '公开', color: '#52c41a' },
  INTERNAL: { value: 'internal', label: '内部', color: '#1890ff' },
  RESTRICTED: { value: 'restricted', label: '受限', color: '#faad14' },
  PRIVATE: { value: 'private', label: '私有', color: '#ff4d4f' }
};

export const CATEGORIES = {
  ENGINEERING: { value: 'engineering', label: '工程技术' },
  SALES: { value: 'sales', label: '销售支持' },
  MARKETING: { value: 'marketing', label: '市场营销' },
  CUSTOMER_SERVICE: { value: 'customer_service', label: '客户服务' },
  QUALITY: { value: 'quality', label: '质量管理' },
  PRODUCTION: { value: 'production', label: '生产制造' },
  PROCUREMENT: { value: 'procurement', label: '采购管理' },
  FINANCE: { value: 'finance', label: '财务行政' }
};

export const SORT_OPTIONS = {
  NEWEST: { value: 'newest', label: '最新发布' },
  OLDEST: { value: 'oldest', label: '最早发布' },
  MOST_VIEWED: { value: 'most_viewed', label: '最多查看' },
  HIGHEST_RATED: { value: 'highest_rated', label: '评分最高' },
  MOST_DOWNLOADED: { value: 'most_downloaded', label: '最多下载' },
  LAST_MODIFIED: { value: 'last_modified', label: '最近更新' }
};

export const SEARCH_FILTERS = {
  TITLE: { value: 'title', label: '标题' },
  CONTENT: { value: 'content', label: '内容' },
  TAGS: { value: 'tags', label: '标签' },
  AUTHOR: { value: 'author', label: '作者' },
  CATEGORY: { value: 'category', label: '分类' }
};

export const VIEW_LAYOUTS = {
  GRID: { value: 'grid', label: '网格视图', icon: '📱' },
  LIST: { value: 'list', label: '列表视图', icon: '📋' },
  CARD: { value: 'card', label: '卡片视图', icon: '🎴' }
};

export const IMPORTANCE_LEVELS = {
  HIGH: { value: 'high', label: '重要', color: '#ff4d4f', weight: 3 },
  MEDIUM: { value: 'medium', label: '一般', color: '#faad14', weight: 2 },
  LOW: { value: 'low', label: '普通', color: '#52c41a', weight: 1 }
};

export const STATUS_OPTIONS = {
  PUBLISHED: { value: 'published', label: '已发布', color: '#52c41a' },
  DRAFT: { value: 'draft', label: '草稿', color: '#d9d9d9' },
  ARCHIVED: { value: 'archived', label: '已归档', color: '#8c8c8c' },
  PENDING_REVIEW: { value: 'pending_review', label: '待审核', color: '#faad14' }
};

export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1200, y: 500 },
  size: 'middle'
};

export const DEFAULT_FILTERS = {
  type: null,
  category: null,
  accessLevel: null,
  status: 'published',
  tags: [],
  dateRange: null
};