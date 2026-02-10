/**
 * BaseDashboard使用示例
 * 
 * 展示如何使用BaseDashboard组件创建Dashboard页面
 */

import { BaseDashboard } from './BaseDashboard';
import { DashboardStatCard } from '../ui/card';
import { LineChart } from '../ui/charts';
import { DataTable } from '../ui/data-table';
import { api } from '../../services/api';
import { Activity, BarChart3, CheckCircle2, Clock, RefreshCw } from 'lucide-react';

// ========== 示例1：简单统计Dashboard ==========

export function SimpleStatsDashboard() {
  return (
    <BaseDashboard
      title="统计概览"
      description="查看系统整体统计数据"
      queryKey={['dashboard', 'stats']}
      queryFn={() => api.getStats()}
      renderContent={(data) => (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <DashboardStatCard
            label="总数"
            value={data.overview?.total || 0}
            icon={BarChart3}
          />
          <DashboardStatCard
            label="进行中"
            value={data.overview?.active || 0}
            icon={RefreshCw}
          />
          <DashboardStatCard
            label="待处理"
            value={data.overview?.pending || 0}
            icon={Clock}
          />
          <DashboardStatCard
            label="已完成"
            value={data.overview?.completed || 0}
            icon={CheckCircle2}
          />
        </div>
      )}
    />
  );
}

// ========== 示例2：带图表的Dashboard ==========

export function AnalyticsDashboard() {
  return (
    <BaseDashboard
      title="数据分析"
      description="查看趋势和分布分析"
      queryKey={['dashboard', 'analytics']}
      queryFn={() => api.getAnalytics()}
      refetchInterval={60000} // 每60秒自动刷新
      renderContent={(data) => (
        <div className="space-y-6">
          {/* 统计卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {Object.entries(data.overview || {}).map(([key, value]) => (
              <DashboardStatCard
                key={key}
                label={key}
                value={value}
                icon={Activity}
              />
            ))}
          </div>

          {/* 图表 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <LineChart
              title="趋势分析"
              data={data.trends || []}
            />
            <LineChart
              title="分布分析"
              data={data.distribution?.distribution || {}}
            />
          </div>
        </div>
      )}
    />
  );
}

// ========== 示例3：带列表的Dashboard ==========

export function ListDashboard() {
  return (
    <BaseDashboard
      title="项目列表"
      description="查看最近的项目和统计信息"
      queryKey={['dashboard', 'projects']}
      queryFn={() => api.getProjects()}
      renderContent={(data) => (
        <div className="space-y-6">
          {/* 统计卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <DashboardStatCard
              label="总项目数"
              value={data.overview?.total || 0}
              icon={BarChart3}
            />
            <DashboardStatCard
              label="进行中"
              value={data.overview?.active || 0}
              icon={RefreshCw}
            />
            <DashboardStatCard
              label="待处理"
              value={data.overview?.pending || 0}
              icon={Clock}
            />
            <DashboardStatCard
              label="已完成"
              value={data.overview?.completed || 0}
              icon={CheckCircle2}
            />
          </div>

          {/* 数据表格 */}
          <DataTable
            data={data.recent_items || []}
            columns={[
              { key: 'name', label: '名称' },
              { key: 'status', label: '状态' },
              { key: 'created_at', label: '创建时间' },
            ]}
          />
        </div>
      )}
    />
  );
}

// ========== 示例4：带自定义操作的Dashboard ==========

import { Button } from '../ui/button';
import { Plus, Download } from 'lucide-react';

export function CustomActionsDashboard() {
  return (
    <BaseDashboard
      title="项目管理"
      description="管理项目并查看统计信息"
      queryKey={['dashboard', 'projects']}
      queryFn={() => api.getProjectDashboard()}
      actions={
        <>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            新建项目
          </Button>
        </>
      }
      renderContent={(data) => (
        <div className="space-y-6">
          {/* 内容 */}
        </div>
      )}
    />
  );
}

// ========== 示例5：带错误处理的Dashboard ==========

export function ErrorHandlingDashboard() {
  return (
    <BaseDashboard
      title="数据监控"
      queryKey={['dashboard', 'monitoring']}
      queryFn={() => api.getMonitoringData()}
      onSuccess={(data) => {
        console.log('数据加载成功:', data);
      }}
      onError={(error) => {
        console.error('数据加载失败:', error);
        // 可以在这里添加错误上报逻辑
      }}
      renderContent={(data) => {
        // 添加额外的错误检查
        if (!data || !data.overview) {
          return (
            <div className="text-center py-12 text-muted-foreground">
              数据格式错误
            </div>
          );
        }

        return (
          <div className="space-y-6">
            {/* 内容 */}
          </div>
        );
      }}
    />
  );
}
