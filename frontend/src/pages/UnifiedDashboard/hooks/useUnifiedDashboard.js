/**
 * useUnifiedDashboard Hook
 *
 * 管理统一工作台的数据加载、角色切换、组件配置
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import api from '../../../services/api';
import { getRoleConfig } from '../config/roleWidgetConfig';

/**
 * 统一工作台数据管理 Hook
 *
 * @param {string} roleCode - 当前角色编码
 * @returns {Object} { widgets, loading, error, widgetData, roleConfig, refresh }
 */
export function useUnifiedDashboard(roleCode) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [widgetData, setWidgetData] = useState({});

  // 获取角色配置
  const roleConfig = useMemo(() => {
    return getRoleConfig(roleCode);
  }, [roleCode]);

  // 加载工作台数据
  const loadDashboardData = useCallback(async () => {
    if (!roleCode) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 尝试从后端获取工作台数据
      // 后端会根据角色返回对应的数据
      const response = await api.get(`/dashboard/unified/${roleCode}`);
      setWidgetData(response.data || {});
    } catch (err) {
      console.warn('Dashboard API not available, using default data:', err.message);
      // API 不可用时使用空数据，组件自行加载
      setWidgetData({});
    } finally {
      setLoading(false);
    }
  }, [roleCode]);

  // 角色变更时重新加载数据
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // 构建组件配置（合并数据）
  const widgets = useMemo(() => {
    if (!roleConfig?.widgets) {
      return [];
    }

    return roleConfig.widgets.map(widget => ({
      ...widget,
      props: {
        ...widget.props,
        // 注入组件数据
        data: widgetData[widget.id],
      },
    }));
  }, [roleConfig, widgetData]);

  // 刷新数据
  const refresh = useCallback(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  return {
    widgets,
    loading,
    error,
    widgetData,
    roleConfig,
    refresh,
  };
}

/**
 * 获取用户角色列表 Hook
 *
 * @returns {Object} { roles, loading, primaryRole }
 */
export function useUserRoles() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUserRoles = async () => {
      try {
        // 从 localStorage 获取用户信息
        const userStr = localStorage.getItem('user');
        if (userStr) {
          const user = JSON.parse(userStr);

          // 处理角色数据
          let userRoles = [];

          // 支持多种数据格式
          if (user.roles && Array.isArray(user.roles)) {
            // 新格式：roles 数组
            userRoles = user.roles.map(r => ({
              role_code: r.role_code || r.code || r,
              role_name: r.role_name || r.name || r.role_code || r,
              is_primary: r.is_primary || false,
            }));
          } else if (user.role) {
            // 旧格式：单个 role 字符串
            userRoles = [{
              role_code: user.role,
              role_name: getRoleDisplayName(user.role),
              is_primary: true,
            }];
          }

          // 如果是超级管理员，添加管理员角色
          if (user.is_superuser || user.isSuperuser) {
            const hasAdmin = userRoles.some(r => r.role_code === 'ADMIN' || r.role_code === 'SUPER_ADMIN');
            if (!hasAdmin) {
              userRoles.unshift({
                role_code: 'SUPER_ADMIN',
                role_name: '超级管理员',
                is_primary: true,
              });
            }
          }

          setRoles(userRoles);
        }
      } catch (err) {
        console.error('Failed to load user roles:', err);
        setRoles([]);
      } finally {
        setLoading(false);
      }
    };

    loadUserRoles();
  }, []);

  // 获取主要角色
  const primaryRole = useMemo(() => {
    const primary = roles.find(r => r.is_primary);
    return primary?.role_code || roles[0]?.role_code || 'DEFAULT';
  }, [roles]);

  return { roles, loading, primaryRole };
}

/**
 * 角色编码到显示名称的映射
 */
function getRoleDisplayName(roleCode) {
  const roleNames = {
    'admin': '系统管理员',
    'ADMIN': '系统管理员',
    'super_admin': '超级管理员',
    'SUPER_ADMIN': '超级管理员',
    'sales': '销售工程师',
    'SALES': '销售工程师',
    'sales_manager': '销售经理',
    'SALES_MANAGER': '销售经理',
    'sales_director': '销售总监',
    'SALES_DIRECTOR': '销售总监',
    'presales': '售前工程师',
    'PRESALES': '售前工程师',
    'engineer': '工程师',
    'ENGINEER': '工程师',
    'me_engineer': '机械工程师',
    'ME_ENGINEER': '机械工程师',
    'ee_engineer': '电气工程师',
    'EE_ENGINEER': '电气工程师',
    'sw_engineer': '软件工程师',
    'SW_ENGINEER': '软件工程师',
    'te_engineer': '测试工程师',
    'TE_ENGINEER': '测试工程师',
    'pmc': '项目经理(PMC)',
    'PMC': '项目经理(PMC)',
    'pm': '项目经理',
    'PM': '项目经理',
    'PMO_DIR': '项目管理部总监',
    'procurement': '采购工程师',
    'PROCUREMENT': '采购工程师',
    'procurement_manager': '采购经理',
    'PROCUREMENT_MANAGER': '采购经理',
    'buyer': '采购员',
    'BUYER': '采购员',
    'production': '生产管理',
    'PRODUCTION': '生产管理',
    'production_manager': '生产经理',
    'PRODUCTION_MANAGER': '生产经理',
    'manufacturing_dir': '制造总监',
    'MANUFACTURING_DIR': '制造总监',
    'assembler': '装配工',
    'ASSEMBLER': '装配工',
    'customer_service': '客服工程师',
    'CUSTOMER_SERVICE': '客服工程师',
    'finance': '财务专员',
    'FINANCE': '财务专员',
    'finance_manager': '财务经理',
    'FINANCE_MANAGER': '财务经理',
    'hr': 'HR专员',
    'HR': 'HR专员',
    'hr_manager': 'HR经理',
    'HR_MANAGER': 'HR经理',
    'gm': '总经理',
    'GM': '总经理',
    'chairman': '董事长',
    'CHAIRMAN': '董事长',
    'vp': '副总经理',
    'VP': '副总经理',
  };

  return roleNames[roleCode] || roleCode;
}

export default useUnifiedDashboard;
