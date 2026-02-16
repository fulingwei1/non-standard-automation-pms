/**
 * 预警详情页面
 * Team 3 - Smart Shortage Alert Detail
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getAlertDetail, resolveAlert } from '@/services/api/shortage';
import { ALERT_LEVELS, ALERT_STATUS } from '../constants';
import ImpactAnalysis from './components/ImpactAnalysis';
import { ArrowLeft, Lightbulb, CheckCircle, Package, Calendar, Loader2 } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

const AlertDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(false);

  // 加载预警详情
  useEffect(() => {
    const loadDetail = async () => {
      try {
        setLoading(true);
        const response = await getAlertDetail(id);
        setAlert(response.data);
      } catch (error) {
        console.error('Failed to load alert detail:', error);
        toast({
          title: '加载失败',
          description: error.message,
          variant: 'destructive',
        });
      } finally {
        setLoading(false);
      }
    };

    loadDetail();
  }, [id]);

  // 标记解决
  const handleResolve = async () => {
    try {
      setResolving(true);
      await resolveAlert(id, {
        resolution_type: 'MANUAL',
        notes: '手动标记解决',
      });
      
      toast({
        title: '操作成功',
        description: '预警已标记为已解决',
      });
      
      // 重新加载数据
      const response = await getAlertDetail(id);
      setAlert(response.data);
    } catch (error) {
      toast({
        title: '操作失败',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setResolving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!alert) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-gray-500">预警不存在</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const levelConfig = ALERT_LEVELS[alert.alert_level];
  const statusConfig = ALERT_STATUS[alert.status];

  return (
    <div className="p-6 space-y-6">
      {/* 返回按钮 */}
      <Button
        variant="ghost"
        onClick={() => navigate('/shortage/dashboard')}
        className="mb-4"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        返回看板
      </Button>

      {/* 页面标题 */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-3xl">{levelConfig.icon}</span>
            <h1 className="text-3xl font-bold text-gray-900">
              {alert.material_name}
            </h1>
            <Badge variant="outline" className={levelConfig.textColor}>
              {levelConfig.label}
            </Badge>
            <Badge variant="outline" className={statusConfig.color}>
              {statusConfig.label}
            </Badge>
          </div>
          <p className="text-gray-500">
            预警单号: {alert.alert_no} | 物料编码: {alert.material_code}
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={() => navigate(`/shortage/alerts/${id}/solutions`)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <Lightbulb className="mr-2 h-4 w-4" />
            查看AI方案
          </Button>
          {alert.status === 'PENDING' && (
            <Button
              onClick={handleResolve}
              disabled={resolving}
              variant="outline"
              className="border-green-600 text-green-600 hover:bg-green-50"
            >
              {resolving ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <CheckCircle className="mr-2 h-4 w-4" />
              )}
              标记解决
            </Button>
          )}
        </div>
      </div>

      {/* 基本信息 */}
      <Card>
        <CardHeader>
          <CardTitle>基本信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 缺料数量 */}
            <div className="flex items-start gap-3 p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="p-2 bg-red-100 rounded-lg">
                <Package className="h-5 w-5 text-red-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-gray-600 mb-1">缺料数量</p>
                <p className="text-2xl font-bold text-red-600">
                  {alert.shortage_qty}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  需求: {alert.required_qty} | 可用: {alert.available_qty}
                </p>
                {alert.in_transit_qty > 0 && (
                  <p className="text-xs text-blue-600 mt-1">
                    在途: {alert.in_transit_qty}
                  </p>
                )}
              </div>
            </div>

            {/* 需求日期 */}
            <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Calendar className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-gray-600 mb-1">需求日期</p>
                <p className="text-2xl font-bold text-blue-600">
                  {alert.required_date}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  距离缺料: {alert.days_to_shortage} 天
                </p>
                <p className="text-xs text-gray-400">
                  预警日期: {alert.alert_date}
                </p>
              </div>
            </div>

            {/* 其他信息 */}
            <div className="space-y-3">
              <div>
                <p className="text-sm text-gray-500">项目ID</p>
                <p className="font-semibold">{alert.project_id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">工单ID</p>
                <p className="font-semibold">{alert.work_order_id || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">检测时间</p>
                <p className="font-semibold text-xs">{alert.detected_at}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 影响分析 */}
      <ImpactAnalysis alert={alert} />

      {/* 处理记录 */}
      {alert.resolved_at && (
        <Card>
          <CardHeader>
            <CardTitle>处理记录</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">解决时间</span>
                <span className="font-semibold">{alert.resolved_at}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">解决方式</span>
                <span className="font-semibold">{alert.resolution_type || '-'}</span>
              </div>
              {alert.handling_plan_id && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">处理方案ID</span>
                  <span className="font-semibold">{alert.handling_plan_id}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AlertDetail;
