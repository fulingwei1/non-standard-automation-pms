/**
 * 项目总览仪表盘
 * 功能：生产/采购/交付/售后各模块状态卡片
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from '@/components/ui';

export default function ProjectOverviewDashboard() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);

  useEffect(() => { loadOverview(); }, [projectId]);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const res = await fetch(`/api/v1/projects/${projectId}/overview`);
      setOverview(await res.json());
    } catch (error) { console.error('加载失败:', error); }
    finally { setLoading(false); }
  };

  if (loading) return <div className="p-6">加载中...</div>;
  if (!overview) return <div className="p-6">项目不存在</div>;

  const prod = overview.production || {};
  const proc = overview.procurement || {};
  const del_ = overview.delivery || {};
  const as_ = overview.after_sales || {};

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">项目总览</h1>
        <p className="text-gray-500">项目 #{projectId} - 生产/采购/交付/售后全链路状态</p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* 生产模块 */}
        <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => navigate(`/projects/${projectId}/production`)}>
          <CardHeader><CardTitle className="flex items-center justify-between"><span>🏭 生产状态</span><Badge>查看详情</Badge></CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div><div className="text-2xl font-bold text-blue-600">{prod.work_orders_count || 0}</div><div className="text-sm text-gray-500">工单总数</div></div>
              <div><div className="text-2xl font-bold text-green-600">{prod.completed_count || 0}</div><div className="text-sm text-gray-500">已完成</div></div>
              <div><div className="text-2xl font-bold text-yellow-600">{prod.in_progress_count || 0}</div><div className="text-sm text-gray-500">进行中</div></div>
            </div>
            <Progress value={prod.work_orders_count ? (prod.completed_count / prod.work_orders_count * 100) : 0} className="mt-4" />
          </CardContent>
        </Card>

        {/* 采购模块 */}
        <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => navigate(`/projects/${projectId}/procurement`)}>
          <CardHeader><CardTitle className="flex items-center justify-between"><span>🛒 采购状态</span><Badge>查看详情</Badge></CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div><div className="text-2xl font-bold text-blue-600">{proc.purchase_requests_count || 0}</div><div className="text-sm text-gray-500">采购申请</div></div>
              <div><div className="text-2xl font-bold text-blue-600">{proc.purchase_orders_count || 0}</div><div className="text-sm text-gray-500">采购订单</div></div>
              <div><div className="text-2xl font-bold text-green-600">{proc.received_count || 0}</div><div className="text-sm text-gray-500">已收货</div></div>
            </div>
            <Progress value={proc.purchase_orders_count ? (proc.received_count / proc.purchase_orders_count * 100) : 0} className="mt-4" />
          </CardContent>
        </Card>

        {/* 交付模块 */}
        <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => navigate(`/projects/${projectId}/delivery`)}>
          <CardHeader><CardTitle className="flex items-center justify-between"><span>📦 交付状态</span><Badge>查看详情</Badge></CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div><div className="text-2xl font-bold text-blue-600">{del_.schedules_count || 0}</div><div className="text-sm text-gray-500">排产计划</div></div>
              <div><div className="text-2xl font-bold text-green-600">{del_.confirmed_count || 0}</div><div className="text-sm text-gray-500">已确认</div></div>
              <div><div className="text-2xl font-bold text-yellow-600">{del_.in_filling_count || 0}</div><div className="text-sm text-gray-500">填写中</div></div>
            </div>
          </CardContent>
        </Card>

        {/* 售后模块 */}
        <Card className="cursor-pointer hover:shadow-lg transition" onClick={() => navigate(`/projects/${projectId}/after-sales`)}>
          <CardHeader><CardTitle className="flex items-center justify-between"><span>🔧 售后状态</span><Badge>查看详情</Badge></CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div><div className="text-2xl font-bold text-blue-600">{as_.feedback_count || 0}</div><div className="text-sm text-gray-500">客户反馈</div></div>
              <div><div className="text-2xl font-bold text-blue-600">{as_.maintenance_count || 0}</div><div className="text-sm text-gray-500">维修保养</div></div>
              <div><div className="text-2xl font-bold text-red-600">{as_.support_tickets_count || 0}</div><div className="text-sm text-gray-500">支持工单</div></div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 数据流通操作 */}
      <Card className="mt-6">
        <CardHeader><CardTitle>📊 数据流通操作</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center">
              <span className="text-lg mb-1">📋→🏭</span>
              <span className="text-sm">WBS→生产工单</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center">
              <span className="text-lg mb-1">📦→🛒</span>
              <span className="text-sm">BOM→采购申请</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center">
              <span className="text-lg mb-1">🎯→📦</span>
              <span className="text-sm">里程碑→交付计划</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center">
              <span className="text-lg mb-1">✅→🔧</span>
              <span className="text-sm">验收→售后</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
