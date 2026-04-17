import { createElement } from 'react';

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

export function renderDataScopeBadge(scope) {
    const config = DATA_SCOPE_MAP[scope] || DATA_SCOPE_MAP['OWN'];
    return createElement(
        'span',
        { className: `px-2 py-0.5 rounded text-xs font-medium ${config.color}` },
        config.label,
    );
}
