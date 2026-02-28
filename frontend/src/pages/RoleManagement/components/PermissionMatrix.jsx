/**
 * 权限矩阵组件
 *
 * 功能：
 * - 按模块 → 页面 → 操作展示权限
 * - 支持勾选/取消权限
 * - 显示权限依赖关系
 * - 批量操作（全选模块/页面）
 */

import React, { useState, useEffect } from 'react';
import {
    Check,
    ChevronDown,
    ChevronRight,
    Lock,
    AlertCircle,
} from 'lucide-react';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Checkbox } from '../../../components/ui/checkbox';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '../../../components/ui/tooltip';

// 操作类型映射
const ACTION_TYPE_MAP = {
    'VIEW': { label: '查看', order: 1, color: 'bg-blue-100 text-blue-700' },
    'CREATE': { label: '创建', order: 2, color: 'bg-green-100 text-green-700' },
    'EDIT': { label: '编辑', order: 3, color: 'bg-yellow-100 text-yellow-700' },
    'DELETE': { label: '删除', order: 4, color: 'bg-red-100 text-red-700' },
    'APPROVE': { label: '审批', order: 5, color: 'bg-purple-100 text-purple-700' },
    'EXPORT': { label: '导出', order: 6, color: 'bg-gray-100 text-gray-700' },
};

// 操作类型顺序
const ACTION_ORDER = ['VIEW', 'CREATE', 'EDIT', 'DELETE', 'APPROVE', 'EXPORT'];

/**
 * 权限矩阵组件
 * @param {Object} props
 * @param {Object} props.matrix - 权限矩阵数据 { matrix: [], action_types: [] }
 * @param {number[]} props.selectedPermissions - 已选择的权限ID列表
 * @param {number[]} props.inheritedPermissions - 继承的权限ID列表（只读）
 * @param {Object} props.dependencies - 权限依赖关系 { permId: { depends_on_id, depends_on_code } }
 * @param {function} props.onSelectionChange - 选择变化回调 (newSelection: number[]) => void
 * @param {boolean} props.readonly - 是否只读模式
 */
export function PermissionMatrix({
    matrix,
    selectedPermissions = [],
    inheritedPermissions = [],
    dependencies = {},
    onSelectionChange,
    readonly = false,
}) {
    const [expandedModules, setExpandedModules] = useState({});
    const [expandedPages, setExpandedPages] = useState({});

    // 展开所有模块
    useEffect(() => {
        if (matrix?.matrix) {
            const expanded = {};
            (matrix.matrix || []).forEach(mod => {
                expanded[mod.module_code] = true;
            });
            setExpandedModules(expanded);
        }
    }, [matrix]);

    // 检查权限是否被选中
    const isSelected = (permId) => {
        return selectedPermissions.includes(permId) || inheritedPermissions.includes(permId);
    };

    // 检查权限是否是继承的（只读）
    const isInherited = (permId) => {
        return inheritedPermissions.includes(permId);
    };

    // 检查权限是否有未满足的依赖
    const hasMissingDependency = (permId) => {
        const dep = dependencies[permId];
        if (!dep?.depends_on_id) return false;
        return !isSelected(dep.depends_on_id);
    };

    // 获取权限的依赖信息
    const getDependencyInfo = (permId) => {
        return dependencies[permId];
    };

    // 切换权限选择
    const togglePermission = (permId) => {
        if (readonly || isInherited(permId)) return;

        const dep = getDependencyInfo(permId);

        if (selectedPermissions.includes(permId)) {
            // 取消选择 - 检查是否有其他权限依赖于此权限
            const dependentPerms = Object.entries(dependencies)
                .filter(([_, d]) => d.depends_on_id === permId)
                .map(([id]) => parseInt(id));

            const selectedDependents = (dependentPerms || []).filter(id => selectedPermissions.includes(id));
            if (selectedDependents.length > 0) {
                alert('存在依赖此权限的其他权限，请先取消它们的选择');
                return;
            }

            onSelectionChange?.((selectedPermissions || []).filter(id => id !== permId));
        } else {
            // 选择权限 - 自动选择依赖的权限
            let newSelection = [...selectedPermissions, permId];

            if (dep?.depends_on_id && !isSelected(dep.depends_on_id)) {
                newSelection = [...newSelection, dep.depends_on_id];
            }

            onSelectionChange?.(newSelection);
        }
    };

    // 切换模块展开
    const toggleModule = (moduleCode) => {
        setExpandedModules(prev => ({
            ...prev,
            [moduleCode]: !prev[moduleCode],
        }));
    };

    // 切换页面展开
    const togglePage = (moduleCode, pageCode) => {
        const key = `${moduleCode}:${pageCode}`;
        setExpandedPages(prev => ({
            ...prev,
            [key]: !prev[key],
        }));
    };

    // 选择/取消模块下所有权限
    const toggleModuleAll = (module) => {
        if (readonly) return;

        const allPermIds = (module.pages || []).flatMap(page =>
            (page.permissions || []).map(p => p.id)
        ).filter(id => !isInherited(id));

        const allSelected = (allPermIds || []).every(id => selectedPermissions.includes(id));

        if (allSelected) {
            onSelectionChange?.((selectedPermissions || []).filter(id => !allPermIds.includes(id)));
        } else {
            const newSelection = [...new Set([...selectedPermissions, ...allPermIds])];
            onSelectionChange?.(newSelection);
        }
    };

    // 选择/取消页面下所有权限
    const togglePageAll = (page) => {
        if (readonly) return;

        const allPermIds = (page.permissions || []).map(p => p.id).filter(id => !isInherited(id));
        const allSelected = (allPermIds || []).every(id => selectedPermissions.includes(id));

        if (allSelected) {
            onSelectionChange?.((selectedPermissions || []).filter(id => !allPermIds.includes(id)));
        } else {
            const newSelection = [...new Set([...selectedPermissions, ...allPermIds])];
            onSelectionChange?.(newSelection);
        }
    };

    // 计算模块选中状态
    const getModuleCheckState = (module) => {
        const allPermIds = (module.pages || []).flatMap(page =>
            (page.permissions || []).map(p => p.id)
        );
        const selectedCount = (allPermIds || []).filter(id => isSelected(id)).length;

        if (selectedCount === 0) return 'none';
        if (selectedCount === allPermIds.length) return 'all';
        return 'partial';
    };

    // 计算页面选中状态
    const getPageCheckState = (page) => {
        const allPermIds = (page.permissions || []).map(p => p.id);
        const selectedCount = (allPermIds || []).filter(id => isSelected(id)).length;

        if (selectedCount === 0) return 'none';
        if (selectedCount === allPermIds.length) return 'all';
        return 'partial';
    };

    if (!matrix?.matrix) {
        return <div className="text-center py-8 text-slate-400">加载权限矩阵中...</div>;
    }

    return (
        <TooltipProvider>
            <div className="space-y-2">
                {/* 图例 */}
                <div className="flex items-center gap-4 text-sm text-slate-600 mb-4 pb-4 border-b">
                    <div className="flex items-center gap-1">
                        <div className="w-4 h-4 rounded border-2 border-blue-500 bg-blue-100 flex items-center justify-center">
                            <Check className="w-3 h-3 text-blue-600" />
                        </div>
                        <span>已选择</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-4 h-4 rounded border-2 border-green-500 bg-green-100 flex items-center justify-center">
                            <Lock className="w-3 h-3 text-green-600" />
                        </div>
                        <span>继承（不可修改）</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <div className="w-4 h-4 rounded border border-slate-300"></div>
                        <span>未选择</span>
                    </div>
                </div>

                {/* 矩阵内容 */}
                {(matrix.matrix || []).map((module) => {
                    const isExpanded = expandedModules[module.module_code];
                    const checkState = getModuleCheckState(module);

                    return (
                        <div key={module.module_code} className="border rounded-lg overflow-hidden">
                            {/* 模块头 */}
                            <div
                                className="flex items-center gap-2 px-4 py-3 bg-slate-50 cursor-pointer hover:bg-slate-100"
                                onClick={() => toggleModule(module.module_code)}
                            >
                                {isExpanded ? (
                                    <ChevronDown className="w-4 h-4 text-slate-400" />
                                ) : (
                                    <ChevronRight className="w-4 h-4 text-slate-400" />
                                )}

                                {!readonly && (
                                    <div
                                        className={`w-4 h-4 rounded border-2 flex items-center justify-center cursor-pointer
                                            ${checkState === 'all' ? 'bg-blue-500 border-blue-500' : ''}
                                            ${checkState === 'partial' ? 'bg-blue-200 border-blue-400' : ''}
                                            ${checkState === 'none' ? 'border-slate-300' : ''}
                                        `}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            toggleModuleAll(module);
                                        }}
                                    >
                                        {checkState !== 'none' && (
                                            <Check className="w-3 h-3 text-white" />
                                        )}
                                    </div>
                                )}

                                <span className="font-medium">{module.module_name}</span>
                                <Badge variant="outline" className="ml-2">
                                    {(module.pages || []).reduce((sum, p) => sum + p.permissions?.length, 0)} 权限
                                </Badge>
                            </div>

                            {/* 页面列表 */}
                            {isExpanded && (
                                <div className="divide-y">
                                    {(module.pages || []).map((page) => {
                                        const pageKey = `${module.module_code}:${page.page_code}`;
                                        const isPageExpanded = expandedPages[pageKey] !== false; // 默认展开
                                        const pageCheckState = getPageCheckState(page);

                                        return (
                                            <div key={page.page_code}>
                                                {/* 页面头 */}
                                                <div
                                                    className="flex items-center gap-2 px-6 py-2 bg-slate-25 cursor-pointer hover:bg-slate-50"
                                                    onClick={() => togglePage(module.module_code, page.page_code)}
                                                >
                                                    {isPageExpanded ? (
                                                        <ChevronDown className="w-3 h-3 text-slate-400" />
                                                    ) : (
                                                        <ChevronRight className="w-3 h-3 text-slate-400" />
                                                    )}

                                                    {!readonly && (
                                                        <div
                                                            className={`w-3.5 h-3.5 rounded border flex items-center justify-center cursor-pointer
                                                                ${pageCheckState === 'all' ? 'bg-blue-500 border-blue-500' : ''}
                                                                ${pageCheckState === 'partial' ? 'bg-blue-200 border-blue-400' : ''}
                                                                ${pageCheckState === 'none' ? 'border-slate-300' : ''}
                                                            `}
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                togglePageAll(page);
                                                            }}
                                                        >
                                                            {pageCheckState !== 'none' && (
                                                                <Check className="w-2.5 h-2.5 text-white" />
                                                            )}
                                                        </div>
                                                    )}

                                                    <span className="text-sm text-slate-700">{page.page_name}</span>
                                                    <span className="text-xs text-slate-400">({page.permissions?.length})</span>
                                                </div>

                                                {/* 权限列表 */}
                                                {isPageExpanded && (
                                                    <div className="px-8 py-2 flex flex-wrap gap-2">
                                                        {page.permissions
                                                            .sort((a, b) => {
                                                                const orderA = ACTION_TYPE_MAP[a.action]?.order || 99;
                                                                const orderB = ACTION_TYPE_MAP[b.action]?.order || 99;
                                                                return orderA - orderB;
                                                            })
                                                            .map((perm) => {
                                                                const selected = isSelected(perm.id);
                                                                const inherited = isInherited(perm.id);
                                                                const missingDep = hasMissingDependency(perm.id);
                                                                const depInfo = getDependencyInfo(perm.id);
                                                                const actionConfig = ACTION_TYPE_MAP[perm.action] || {};

                                                                return (
                                                                    <Tooltip key={perm.id}>
                                                                        <TooltipTrigger asChild>
                                                                            <div
                                                                                className={`
                                                                                    flex items-center gap-1.5 px-2 py-1 rounded border text-sm
                                                                                    ${inherited
                                                                                        ? 'bg-green-50 border-green-300 cursor-not-allowed'
                                                                                        : selected
                                                                                            ? 'bg-blue-50 border-blue-300 cursor-pointer hover:bg-blue-100'
                                                                                            : 'bg-white border-slate-200 cursor-pointer hover:bg-slate-50'
                                                                                    }
                                                                                    ${missingDep ? 'ring-2 ring-yellow-400' : ''}
                                                                                    ${readonly && !inherited ? 'cursor-default' : ''}
                                                                                `}
                                                                                onClick={() => togglePermission(perm.id)}
                                                                            >
                                                                                {inherited ? (
                                                                                    <Lock className="w-3 h-3 text-green-600" />
                                                                                ) : selected ? (
                                                                                    <Check className="w-3 h-3 text-blue-600" />
                                                                                ) : (
                                                                                    <div className="w-3 h-3 rounded border border-slate-300" />
                                                                                )}
                                                                                <span className={`px-1.5 py-0.5 rounded text-xs ${actionConfig.color || 'bg-gray-100'}`}>
                                                                                    {actionConfig.label || perm.action}
                                                                                </span>
                                                                                <span className="text-slate-700">{perm.name}</span>
                                                                                {depInfo && (
                                                                                    <AlertCircle className="w-3 h-3 text-yellow-500" />
                                                                                )}
                                                                            </div>
                                                                        </TooltipTrigger>
                                                                        <TooltipContent side="top">
                                                                            <div className="text-xs space-y-1">
                                                                                <div className="font-mono">{perm.code}</div>
                                                                                {perm.description && (
                                                                                    <div className="text-slate-400">{perm.description}</div>
                                                                                )}
                                                                                {inherited && (
                                                                                    <div className="text-green-600">继承自父角色</div>
                                                                                )}
                                                                                {depInfo && (
                                                                                    <div className="text-yellow-600">
                                                                                        依赖: {depInfo.depends_on_code || depInfo.depends_on_name}
                                                                                    </div>
                                                                                )}
                                                                            </div>
                                                                        </TooltipContent>
                                                                    </Tooltip>
                                                                );
                                                            })}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </TooltipProvider>
    );
}

export default PermissionMatrix;
