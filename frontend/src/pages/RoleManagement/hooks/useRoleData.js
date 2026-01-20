import { useState, useCallback, useEffect } from 'react';
import { roleApi } from '../../../services/api';

/**
 * 角色数据管理 Hook
 */
export function useRoleData() {
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [permissions, setPermissions] = useState([]);
    const [searchKeyword, setSearchKeyword] = useState('');

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
            const response = await roleApi.listPermissions();
            const data = response.data || response;
            setPermissions(data.items || data || []);
        } catch (error) {
            console.error('Failed to load permissions:', error);
        }
    }, []);

    // 创建角色
    const createRole = useCallback(async (roleData) => {
        try {
            await roleApi.create(roleData);
            await loadRoles();
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, [loadRoles]);

    // 更新角色
    const updateRole = useCallback(async (id, roleData) => {
        try {
            await roleApi.update(id, roleData);
            await loadRoles();
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, [loadRoles]);

    // 删除角色
    const deleteRole = useCallback(async (id) => {
        try {
            await roleApi.delete(id);
            await loadRoles();
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, [loadRoles]);

    // 获取角色详情
    const getRoleDetail = useCallback(async (id) => {
        try {
            const response = await roleApi.get(id);
            return response.data || response;
        } catch (error) {
            console.error('Failed to get role detail:', error);
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
            await roleApi.configureMenus(roleId, menuIds);
            return { success: true };
        } catch (error) {
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, []);

    // 初始加载
    useEffect(() => {
        loadRoles();
        loadPermissions();
    }, [loadRoles, loadPermissions]);

    return {
        roles,
        loading,
        permissions,
        searchKeyword,
        setSearchKeyword,
        loadRoles,
        createRole,
        updateRole,
        deleteRole,
        getRoleDetail,
        assignPermissions,
        configureMenus,
    };
}
