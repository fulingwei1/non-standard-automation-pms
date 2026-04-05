/**
 * 项目物料进度查看页面
 * 功能：
 * - 项目物料进度总览
 * - BOM 物料明细进度
 * - 缺料跟踪看板
 * - 通知订阅管理
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Table,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Progress,
  Alert,
  Switch,
} from '@/components/ui';
import { projectApi } from '@/services/api';

export default function MaterialProgressView() {
  const { projectId } = useParams();
  const [loading, setLoading] = useState(true);
  const [materialProgress, setMaterialProgress] = useState(null);
  const [bomProgress, setBomProgress] = useState([]);
  const [shortageTracker, setShortageTracker] = useState([]);
  const [subscription, setSubscription] = useState({
    kitting_change: true,
    arrival_notify: true,
    shortage_alert: true,
  });

  useEffect(() => {
    loadMaterialProgress();
  }, [projectId]);

  const loadMaterialProgress = async () => {
    try {
      setLoading(true);
      const response = await projectApi.getMaterialProgress(projectId);
      setMaterialProgress(response.data);
    } catch (error) {
      console.error('加载物料进度失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadBomProgress = async () => {
    try {
      const response = await projectApi.getBomProgress(projectId);
      setBomProgress(response.data);
    } catch (error) {
      console.error('加载 BOM 进度失败:', error);
    }
  };

  const loadShortageTracker = async () => {
    try {
      const response = await projectApi.getShortageTracker(projectId);
      setShortageTracker(response.data);
    } catch (error) {
      console.error('加载缺料跟踪失败:', error);
    }
  };

  const handleSync = async () => {
    try {
      await projectApi.syncKittingRate([projectId]);
      loadMaterialProgress();
    } catch (error) {
      console.error('同步齐套率失败:', error);
    }
  };

  const handleSubscribe = async () => {
    try {
      await projectApi.subscribeMaterialProgress(projectId, subscription);
    } catch (error) {
      console.error('更新订阅失败:', error);
    }
  };

  const STATUS_COLORS = {
    PENDING: 'bg-gray-200',
    IN_PROGRESS: 'bg-blue-200',
    PARTIAL_ARRIVAL: 'bg-yellow-200',
    COMPLETE: 'bg-green-200',
    SHORTAGE: 'bg-red-200',
  };

  const STATUS_LABELS = {
    PENDING: '待采购',
    IN_PROGRESS: '采购中',
    PARTIAL_ARRIVAL: '部分到货',
    COMPLETE: '齐套',
    SHORTAGE: '缺料',
  };

  const PRIORITY_COLORS = {
    CRITICAL: 'destructive',
    HIGH: 'destructive',
    MEDIUM: 'warning',
    LOW: 'default',
  };

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold mb-2">项目物料进度</h1>
          <p className="text-gray-500">实时跟踪项目物料齐套情况</p>
        </div>
        <div className="space-x-2">
          <Button onClick={handleSync} variant="outline">
            同步齐套率
          </Button>
          <Button onClick={() => loadBomProgress()} variant="outline">
            刷新 BOM
          </Button>
          <Button onClick={() => loadShortageTracker()} variant="outline">
            刷新缺料
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">进度总览</TabsTrigger>
          <TabsTrigger value="bom">BOM 明细</TabsTrigger>
          <TabsTrigger value="shortage">缺料跟踪</TabsTrigger>
          <TabsTrigger value="subscription">通知订阅</TabsTrigger>
        </TabsList>

        {/* 进度总览 */}
        <TabsContent value="overview">
          <div className="grid grid-cols-4 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">齐套率</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">
                  {materialProgress?.kitting_rate?.toFixed(1) || '0'}%
                </div>
                <Progress value={materialProgress?.kitting_rate || 0} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">物料状态</CardTitle>
              </CardHeader>
              <CardContent>
                <Badge className={STATUS_COLORS[materialProgress?.material_status]}>
                  {STATUS_LABELS[materialProgress?.material_status] || '未知'}
                </Badge>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">缺料项数</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-red-600">
                  {materialProgress?.shortage_items_count || 0}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-sm">预计齐套日期</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-xl font-bold">
                  {materialProgress?.estimated_complete_date || '未定'}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 齐套率趋势 */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>近 30 天齐套率趋势</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                图表区域 - 显示齐套率变化趋势
              </div>
            </CardContent>
          </Card>

          {/* 关键物料 */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>关键物料清单</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <thead>
                  <tr>
                    <th>物料编码</th>
                    <th>物料名称</th>
                    <th>需求数量</th>
                    <th>已到货</th>
                    <th>在途</th>
                    <th>缺料</th>
                    <th>预计到货</th>
                  </tr>
                </thead>
                <tbody>
                  {materialProgress?.critical_materials?.map((material) => (
                    <tr key={material.id}>
                      <td>{material.material_code}</td>
                      <td>{material.material_name}</td>
                      <td>{material.required_qty}</td>
                      <td className="text-green-600">{material.arrived_qty}</td>
                      <td className="text-blue-600">{material.in_transit_qty}</td>
                      <td className="text-red-600">{material.shortage_qty}</td>
                      <td>{material.expected_arrival_date || '未定'}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* BOM 明细 */}
        <TabsContent value="bom">
          <Card>
            <CardHeader>
              <CardTitle>BOM 物料明细进度</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <thead>
                  <tr>
                    <th>BOM 名称</th>
                    <th>齐套状态</th>
                    <th>需求数量</th>
                    <th>已到货</th>
                    <th>缺料</th>
                    <th>齐套率</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {bomProgress.map((bom) => (
                    <tr key={bom.id}>
                      <td>{bom.bom_name}</td>
                      <td>
                        <Badge className={STATUS_COLORS[bom.kitting_status]}>
                          {STATUS_LABELS[bom.kitting_status]}
                        </Badge>
                      </td>
                      <td>{bom.required_qty}</td>
                      <td>{bom.arrived_qty}</td>
                      <td className="text-red-600">{bom.shortage_qty}</td>
                      <td>
                        <Progress value={bom.kitting_rate} className="w-24" />
                        {bom.kitting_rate?.toFixed(1)}%
                      </td>
                      <td>
                        <Button size="sm" variant="outline">
                          详情
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 缺料跟踪 */}
        <TabsContent value="shortage">
          <Card>
            <CardHeader>
              <CardTitle>缺料跟踪看板</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <thead>
                  <tr>
                    <th>物料编码</th>
                    <th>物料名称</th>
                    <th>缺料数量</th>
                    <th>影响等级</th>
                    <th>影响天数</th>
                    <th>处理进度</th>
                    <th>责任人</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {shortageTracker.map((item) => (
                    <tr key={item.id}>
                      <td>{item.material_code}</td>
                      <td>{item.material_name}</td>
                      <td className="text-red-600">{item.shortage_qty}</td>
                      <td>
                        <Badge variant={PRIORITY_COLORS[item.priority]}>
                          {item.priority}
                        </Badge>
                      </td>
                      <td>{item.impact_days} 天</td>
                      <td>
                        <Progress value={item.progress} className="w-24" />
                        {item.progress}%
                      </td>
                      <td>{item.owner}</td>
                      <td>
                        <Button size="sm">催货</Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 通知订阅 */}
        <TabsContent value="subscription">
          <Card>
            <CardHeader>
              <CardTitle>通知订阅管理</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">齐套率变化通知</div>
                    <div className="text-sm text-gray-500">
                      齐套率每变化 10% 发送通知
                    </div>
                  </div>
                  <Switch
                    checked={subscription.kitting_change}
                    onCheckedChange={(checked) =>
                      setSubscription({ ...subscription, kitting_change: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">关键物料到货通知</div>
                    <div className="text-sm text-gray-500">
                      关键物料到货时立即通知
                    </div>
                  </div>
                  <Switch
                    checked={subscription.arrival_notify}
                    onCheckedChange={(checked) =>
                      setSubscription({ ...subscription, arrival_notify: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">缺料预警通知</div>
                    <div className="text-sm text-gray-500">
                      发现缺料时立即预警
                    </div>
                  </div>
                  <Switch
                    checked={subscription.shortage_alert}
                    onCheckedChange={(checked) =>
                      setSubscription({ ...subscription, shortage_alert: checked })
                    }
                  />
                </div>

                <Button onClick={handleSubscribe} className="mt-4">
                  保存订阅设置
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
