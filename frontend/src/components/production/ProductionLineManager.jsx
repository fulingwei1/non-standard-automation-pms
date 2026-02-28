/**
 * Production Line Manager Component
 * 生产线管理组件
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Factory,
  Activity,
  Users,
  Settings,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Zap,
  TrendingUp,
  TrendingDown,
  Search,
  Filter,
  Plus,
  Eye,
  Edit,
  Power,
  Pause,
  Play } from
'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui';
import { Button } from '../../components/ui';
import { Badge } from '../../components/ui';
import { Input } from '../../components/ui';
import { Progress } from '../../components/ui';
import { cn } from '../../lib/utils';
import {
  PRODUCTION_LINE_STATUS,
  EQUIPMENT_STATUS,
  WORK_SHIFT,
  getStatusColor as _getStatusColor,
  getStatusLabel as _getStatusLabel } from
'@/lib/constants/production';

export default function ProductionLineManager({
  workshops = [],
  loading = false,
  onLineAction,
  onViewDetails: _onViewDetails,
  onEditLine
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [selectedShift, setSelectedShift] = useState('all');

  // 过滤生产线数据
  const filteredWorkshops = useMemo(() => {
    return (workshops || []).filter((workshop) => {
      const matchesSearch = !searchQuery ||
      workshop.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      workshop.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
      workshop.manager?.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesStatus = filterStatus === 'all' || workshop.status === filterStatus;
      const matchesShift = selectedShift === 'all' || workshop.currentShift === selectedShift;

      return matchesSearch && matchesStatus && matchesShift;
    });
  }, [workshops, searchQuery, filterStatus, selectedShift]);

  // 计算统计数据
  const statistics = useMemo(() => {
    const total = workshops.length;
    const active = (workshops || []).filter((w) => w.status === 'active').length;
    const idle = (workshops || []).filter((w) => w.status === 'idle').length;
    const maintenance = (workshops || []).filter((w) => w.status === 'maintenance').length;
    const stopped = (workshops || []).filter((w) => w.status === 'stopped').length;

    const totalEfficiency = (workshops || []).reduce((sum, w) => sum + (w.efficiency || 0), 0);
    const avgEfficiency = total > 0 ? Math.round(totalEfficiency / total) : 0;

    const totalOutput = (workshops || []).reduce((sum, w) => sum + (w.currentOutput || 0), 0);
    const totalTarget = (workshops || []).reduce((sum, w) => sum + (w.targetOutput || 0), 0);
    const overallProgress = totalTarget > 0 ? Math.round(totalOutput / totalTarget * 100) : 0;

    return {
      total,
      active,
      idle,
      maintenance,
      stopped,
      avgEfficiency,
      overallProgress,
      totalOutput,
      totalTarget
    };
  }, [workshops]);

  // 渲染状态徽章
  const renderStatusBadge = (status) => {
    const config = PRODUCTION_LINE_STATUS[status.toUpperCase()];
    if (!config) {return <Badge variant="secondary">{status}</Badge>;}

    return (
      <Badge className={cn(config.color.replace('bg-', 'bg-'), 'text-white')}>
        {config.label}
      </Badge>);

  };

  // 渲染班次徽章
  const renderShiftBadge = (shift) => {
    const config = WORK_SHIFT[shift.toUpperCase()];
    if (!config) {return <Badge variant="outline">{shift}</Badge>;}

    return (
      <Badge variant="outline" className="border-blue-200 text-blue-700">
        {config.label}
      </Badge>);

  };

  // 获取生产线操作按钮
  const getLineActions = (workshop) => {
    const actions = [];

    switch (workshop.status) {
      case 'active':
        actions.push({
          icon: Pause,
          label: '暂停',
          action: 'pause',
          className: 'bg-orange-500 hover:bg-orange-600'
        });
        break;
      case 'idle':
        actions.push({
          icon: Play,
          label: '启动',
          action: 'start',
          className: 'bg-green-500 hover:bg-green-600'
        });
        break;
      case 'stopped':
        actions.push({
          icon: Play,
          label: '启动',
          action: 'start',
          className: 'bg-green-500 hover:bg-green-600'
        });
        break;
      case 'maintenance':
        actions.push({
          icon: CheckCircle2,
          label: '完成维护',
          action: 'complete_maintenance',
          className: 'bg-blue-500 hover:bg-blue-600'
        });
        break;
    }

    actions.push({
      icon: Edit,
      label: '编辑',
      action: 'edit',
      className: 'bg-gray-500 hover:bg-gray-600'
    });

    return actions;
  };

  // 渲染生产线卡片
  const renderWorkshopCard = (workshop, index) =>
  <motion.div
    key={workshop.id}
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3, delay: index * 0.1 }}>

      <Card className="h-full hover:shadow-lg transition-all duration-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Factory className="w-4 h-4 text-blue-600" />
              {workshop.name}
            </CardTitle>
            <div className="flex items-center gap-2">
              {renderStatusBadge(workshop.status)}
              {workshop.currentShift && renderShiftBadge(workshop.currentShift)}
            </div>
          </div>
          <div className="text-sm text-gray-600">
            编号: {workshop.code} | 负责人: {workshop.manager || '未指定'}
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* 生产进度 */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>生产进度</span>
              <span className="font-medium">
                {workshop.currentOutput || 0} / {workshop.targetOutput || 0}
              </span>
            </div>
            <Progress
            value={workshop.targetOutput > 0 ? (workshop.currentOutput || 0) / workshop.targetOutput * 100 : 0}
            className="h-2" />

          </div>
          
          {/* 性能指标 */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                <Zap className="w-3 h-3" />
                效率
              </div>
              <div className="text-lg font-bold text-gray-900">
                {workshop.efficiency || 0}%
              </div>
            </div>
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center gap-2 text-sm text-gray-600 mb-1">
                <Users className="w-3 h-3" />
                工人
              </div>
              <div className="text-lg font-bold text-gray-900">
                {workshop.activeWorkers || 0}/{workshop.totalWorkers || 0}
              </div>
            </div>
          </div>
          
          {/* 设备状态 */}
          <div className="space-y-2">
            <div className="text-sm text-gray-600">设备状态</div>
            <div className="flex flex-wrap gap-2">
              {workshop.equipments?.slice(0, 3).map((equipment) =>
            <Badge
              key={equipment.id}
              variant="outline"
              className={cn(
                'text-xs',
                equipment.status === 'running' && 'border-green-200 text-green-700',
                equipment.status === 'idle' && 'border-gray-200 text-gray-700',
                equipment.status === 'maintenance' && 'border-orange-200 text-orange-700',
                equipment.status === 'breakdown' && 'border-red-200 text-red-700'
              )}>

                  {equipment.name}
            </Badge>
            )}
              {workshop.equipments?.length > 3 &&
            <Badge variant="outline" className="text-xs">
                  +{workshop.equipments?.length - 3} 更多
            </Badge>
            }
            </div>
          </div>
          
          {/* 操作按钮 */}
          <div className="flex gap-2 pt-2">
            {getLineActions(workshop).map((action, actionIndex) => {
            const Icon = action.icon;
            return (
              <Button
                key={actionIndex}
                size="sm"
                variant="secondary"
                className={cn('flex-1', action.className, 'text-white')}
                onClick={() => {
                  if (action.action === 'edit' && onEditLine) {
                    onEditLine(workshop);
                  } else if (onLineAction) {
                    onLineAction(workshop.id, action.action);
                  }
                }}>

                  <Icon className="w-3 h-3 mr-1" />
                  {action.label}
              </Button>);

          })}
          </div>
        </CardContent>
      </Card>
  </motion.div>;


  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) =>
          <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-200 rounded mb-4" />
                <div className="space-y-3">
                  <div className="h-3 bg-gray-200 rounded" />
                  <div className="h-3 bg-gray-200 rounded w-3/4" />
                  <div className="h-8 bg-gray-200 rounded" />
                </div>
              </CardContent>
          </Card>
          )}
        </div>
      </div>);

  }

  return (
    <div className="space-y-6">
      {/* 统计概览 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Factory className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">{statistics.total}</div>
                <div className="text-sm text-gray-600">总生产线</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <Activity className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">{statistics.active}</div>
                <div className="text-sm text-gray-600">运行中</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-50 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-orange-600">{statistics.maintenance}</div>
                <div className="text-sm text-gray-600">维护中</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold text-purple-600">{statistics.avgEfficiency}%</div>
                <div className="text-sm text-gray-600">平均效率</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 搜索和筛选 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="搜索生产线名称、编号或负责人..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10" />

            </div>
            
            <div className="flex gap-2">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm">

                <option value="all">所有状态</option>
                {Object.values(PRODUCTION_LINE_STATUS).map((status) =>
                <option key={status.value} value={status.value}>
                    {status.label}
                </option>
                )}
              </select>
              
              <select
                value={selectedShift}
                onChange={(e) => setSelectedShift(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm">

                <option value="all">所有班次</option>
                {Object.values(WORK_SHIFT).map((shift) =>
                <option key={shift.value} value={shift.value}>
                    {shift.label}
                </option>
                )}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 生产线列表 */}
      <AnimatePresence>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {(filteredWorkshops || []).map(renderWorkshopCard)}
        </div>
      </AnimatePresence>
      
      {filteredWorkshops.length === 0 &&
      <Card>
          <CardContent className="p-8 text-center">
            <Factory className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">没有找到生产线</h3>
            <p className="text-gray-600">请调整搜索条件或筛选器</p>
          </CardContent>
      </Card>
      }
    </div>);

}