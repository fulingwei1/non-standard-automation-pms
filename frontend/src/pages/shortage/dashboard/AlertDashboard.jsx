/**
 * 缺料预警看板主页面
 * Team 3 - Smart Shortage Alert Dashboard
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { getAlerts } from '@/services/api/shortage';
import { ALERT_LEVELS } from '../constants';
import AlertLevelCards from './components/AlertLevelCards';
import AlertList from './components/AlertList';
import QuickScanButton from './components/QuickScanButton';
import { Search, Filter } from 'lucide-react';

const AlertDashboard = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [filters, setFilters] = useState({
    alert_level: '',
    status: '',
    search: '',
  });

  // 加载预警数据
  const loadAlerts = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filters.alert_level) params.alert_level = filters.alert_level;
      if (filters.status) params.status = filters.status;
      
      const response = await getAlerts(params);
      const alertData = response.data.items || [];
      setAlerts(alertData);
      
      // 计算统计数据
      const newStats = alertData.reduce((acc, alert) => {
        acc[alert.alert_level] = (acc[alert.alert_level] || 0) + 1;
        return acc;
      }, {});
      setStats(newStats);
    } catch (error) {
      console.error('Failed to load alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [filters.alert_level, filters.status]);

  // 处理级别卡片点击
  const handleLevelClick = (level) => {
    setFilters((prev) => ({
      ...prev,
      alert_level: prev.alert_level === level ? '' : level,
    }));
  };

  // 处理扫描完成
  const handleScanComplete = () => {
    loadAlerts();
  };

  // 搜索过滤
  const filteredAlerts = alerts.filter((alert) => {
    if (!filters.search) return true;
    const searchLower = filters.search.toLowerCase();
    return (
      alert.material_name?.toLowerCase().includes(searchLower) ||
      alert.material_code?.toLowerCase().includes(searchLower) ||
      alert.alert_no?.toLowerCase().includes(searchLower)
    );
  });

  return (
    <div className="p-6 space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">智能缺料预警</h1>
          <p className="text-gray-500 mt-1">实时监控物料缺口，提前预警风险</p>
        </div>
        <QuickScanButton onScanComplete={handleScanComplete} />
      </div>

      {/* 预警级别统计卡片 */}
      <AlertLevelCards stats={stats} onLevelClick={handleLevelClick} />

      {/* 筛选和搜索 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            筛选条件
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 搜索框 */}
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索物料名称、编码、预警单号..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="pl-10"
              />
            </div>

            {/* 预警级别筛选 */}
            <Select
              value={filters.alert_level}
              onValueChange={(value) => setFilters({ ...filters, alert_level: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择预警级别" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部级别</SelectItem>
                {Object.entries(ALERT_LEVELS).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.icon} {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* 状态筛选 */}
            <Select
              value={filters.status}
              onValueChange={(value) => setFilters({ ...filters, status: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部状态</SelectItem>
                <SelectItem value="PENDING">待处理</SelectItem>
                <SelectItem value="PROCESSING">处理中</SelectItem>
                <SelectItem value="RESOLVED">已解决</SelectItem>
                <SelectItem value="CLOSED">已关闭</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* 预警列表 */}
      <Card>
        <CardHeader>
          <CardTitle>
            预警列表
            {filteredAlerts.length > 0 && (
              <span className="ml-2 text-sm font-normal text-gray-500">
                (共 {filteredAlerts.length} 条)
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <AlertList alerts={filteredAlerts} loading={loading} />
        </CardContent>
      </Card>
    </div>
  );
};

export default AlertDashboard;
