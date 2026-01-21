/**
 * 统一工作台 (Unified Dashboard)
 *
 * 将26个角色工作台合并为统一工作台
 * 通过角色权限控制显示内容
 *
 * 核心功能：
 * - 自动识别用户角色
 * - 多角色用户可切换视图
 * - 动态渲染组件
 */

import { useState, useEffect, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import { PageHeader } from '../../components/layout';
import { Button } from '../../components/ui/button';
import { RoleSwitcher } from './RoleSwitcher';
import { DashboardRenderer } from './DashboardRenderer';
import { useUnifiedDashboard, useUserRoles } from './hooks/useUnifiedDashboard';

/**
 * 统一工作台主组件
 */
export default function UnifiedDashboard() {
  // 获取用户角色
  const { roles, loading: rolesLoading, primaryRole } = useUserRoles();

  // 当前选中的角色
  const [currentRole, setCurrentRole] = useState(null);

  // 初始化：设置默认角色
  useEffect(() => {
    if (!rolesLoading && primaryRole && !currentRole) {
      setCurrentRole(primaryRole);
    }
  }, [rolesLoading, primaryRole, currentRole]);

  // 获取工作台数据
  const {
    widgets,
    loading: dataLoading,
    error,
    roleConfig,
    refresh,
  } = useUnifiedDashboard(currentRole);

  // 角色切换处理
  const handleRoleChange = useCallback((roleCode) => {
    setCurrentRole(roleCode);
  }, []);

  // 刷新处理
  const handleRefresh = useCallback(() => {
    refresh();
  }, [refresh]);

  // 加载中
  const isLoading = rolesLoading || dataLoading;

  return (
    <div className="unified-dashboard min-h-screen bg-background">
      <PageHeader
        title="工作台"
        description={roleConfig?.label ? `${roleConfig.label}视图` : '统一工作台'}
      >
        <div className="flex items-center gap-4">
          <RoleSwitcher
            roles={roles}
            currentRole={currentRole}
            onChange={handleRoleChange}
          />

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </PageHeader>

      {error && (
        <div className="mx-4 mb-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg">
          <p className="text-sm text-destructive">{error.message || '加载失败'}</p>
        </div>
      )}

      <DashboardRenderer
        widgets={widgets}
        loading={isLoading}
        layout={roleConfig?.layout || '2-column'}
      />
    </div>
  );
}
