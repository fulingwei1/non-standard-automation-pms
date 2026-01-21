import { useState, useCallback, useEffect } from 'react';
import { roleApi, permissionApi } from '../../../services/api';

/**
 * 角色数据管理 Hook
 *
 * 支持功能：
 * - 角色 CRUD
 * - 角色继承（parent_id）
 * - 权限分配
 * - 角色对比
 * - 角色模板
 */
export function useRoleData() {
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [permissions, setPermissions] = useState([]);
    const [searchKeyword, setSearchKeyword] = useState('');
    const [inheritanceTree, setInheritanceTree] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [permissionMatrix, setPermissionMatrix] = useState(null);

    // 加载角色列表
    const loadRoles = useCallback(async () => {
        try {
            setLoading(true);
            const response = await roleApi.list({
                page: 1,
                page_size: 100,
                keyword: searchKeyword || undefined,
            });
            const data = response.data || response;
            setRoles(data.items || data || []);
        } catch (error) {
            console.error('Failed to load roles:', error);
            setRoles([]);
        } finally {
            setLoading(false);
        }
    }, [searchKeyword]);

    // 加载权限列表
    const loadPermissions = useCallback(async () => {
        try {
            const response = await roleApi.permissions();
            const data = response.data || response;
            setPermissions(data.items || data || []);
        } catch (error) {
            console.error('Failed to load permissions:', error);
        }
    }, []);

    // 加载权限矩阵
    const loadPermissionMatrix = useCallback(async () => {
        try {
            const response = await permissionApi.getMatrix();
            const data = response.data || response;
            setPermissionMatrix(data.data || data);
        } catch (error) {
            console.error('Failed to load permission matrix:', error);
        }
    }, []);

    // 加载角色继承树
    const loadInheritanceTree = useCallback(async () => {
        try {
            const response = await roleApi.getInheritanceTree();
            const data = response.data || response;
            setInheritanceTree(data.data?.tree || []);
        } catch (error) {
            console.error('Failed to load inheritance tree:', error);
        }
    }, []);

    // 加载角色模板列表
    const loadTemplates = useCallback(async () => {
        try {
            const response = await roleApi.listTemplates();
            const data = response.data || response;
            setTemplates(data.data?.items || []);
        } catch (error) {
            console.error('Failed to load templates:', error);
        }
    }, []);

    // 创建角色
    const createRole = useCallback(async (roleData) => {
        try {
            await roleApi.create(roleData);
            await loadRoles();
            await loadInheritanceTree();
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, [loadRoles, loadInheritanceTree]);

    // 更新角色
    const updateRole = useCallback(async (id, roleData) => {
        try {
            await roleApi.update(id, roleData);
            await loadRoles();
            await loadInheritanceTree();
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, [loadRoles, loadInheritanceTree]);

    // 删除角色
    const deleteRole = useCallback(async (id) => {
        try {
            await roleApi.delete(id);
            await loadRoles();
            await loadInheritanceTree();
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, [loadRoles, loadInheritanceTree]);

    // 获取角色详情（含继承权限）
    const getRoleDetail = useCallback(async (id) => {
        try {
            const response = await roleApi.getDetail(id);
            const data = response.data || response;
            return data.data || data;
        } catch (error) {
            console.error('Failed to get role detail:', error);
            throw error;
        }
    }, []);

    // 获取简单角色信息
    const getRole = useCallback(async (id) => {
        try {
            const response = await roleApi.get(id);
            return response.data || response;
        } catch (error) {
            console.error('Failed to get role:', error);
            throw error;
        }
    }, []);

    // 分配权限
    const assignPermissions = useCallback(async (roleId, permissionIds) => {
        try {
            await roleApi.assignPermissions(roleId, permissionIds);
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, []);

    // 配置菜单
    const configureMenus = useCallback(async (roleId, menuIds) => {
        try {
            await roleApi.updateNavGroups(roleId, menuIds);
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, []);

    // 对比角色
    const compareRoles = useCallback(async (roleIds) => {
        try {
            const response = await roleApi.compare(roleIds);
            const data = response.data || response;
            return { success: true, data: data.data || data };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, []);

    // 从模板创建角色
    const createRoleFromTemplate = useCallback(async (templateId, roleData) => {
        try {
            await roleApi.createFromTemplate(templateId, roleData);
            await loadRoles();
            await loadInheritanceTree();
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, [loadRoles, loadInheritanceTree]);

    // 初始加载
    useEffect(() => {
        loadRoles();
        loadPermissions();
        loadInheritanceTree();
        loadTemplates();
        loadPermissionMatrix();
    }, [loadRoles, loadPermissions, loadInheritanceTree, loadTemplates, loadPermissionMatrix]);

    return {
        // 数据状态
        roles,
        loading,
        permissions,
        searchKeyword,
        inheritanceTree,
        templates,
        permissionMatrix,
        // 设置函数
        setSearchKeyword,
        // 加载函数
        loadRoles,
        loadInheritanceTree,
        loadTemplates,
        loadPermissionMatrix,
        // CRUD 操作
        createRole,
        updateRole,
        deleteRole,
        getRole,
        getRoleDetail,
        // 权限操作
        assignPermissions,
        configureMenus,
        // 高级功能
        compareRoles,
        createRoleFromTemplate,
    };
}
