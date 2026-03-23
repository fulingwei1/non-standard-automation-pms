/**
 * 角色管理页面常量配置
 */

// 数据权限范围映射
export const DATA_SCOPE_MAP = {
  'OWN': { label: '仅本人', color: 'bg-blue-100 text-blue-700' },
  'SUBORDINATE': { label: '本人及下属', color: 'bg-green-100 text-green-700' },
  'DEPT': { label: '本部门', color: 'bg-yellow-100 text-yellow-700' },
  'DEPT_SUB': { label: '本部门及下级', color: 'bg-orange-100 text-orange-700' },
  'PROJECT': { label: '所属项目', color: 'bg-purple-100 text-purple-700' },
  'ALL': { label: '全部', color: 'bg-red-100 text-red-700' },
  'CUSTOM': { label: '自定义', color: 'bg-gray-100 text-gray-700' },
};

// 创建表单默认值
export const DEFAULT_CREATE_FORM = {
  role_code: '',
  role_name: '',
  description: '',
  data_scope: 'OWN',
  parent_id: null,
};

// 编辑表单默认值
export const DEFAULT_EDIT_FORM = {
  id: null,
  role_code: '',
  role_name: '',
  description: '',
  data_scope: 'OWN',
  parent_id: null,
};

// 模板表单默认值
export const DEFAULT_TEMPLATE_FORM = {
  template_id: null,
  role_code: '',
  role_name: '',
  description: '',
};
