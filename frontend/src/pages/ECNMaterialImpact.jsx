/**
 * ECN 物料影响跟踪页面
 * 功能：
 * - ECN 物料影响分析
 * - 执行进度跟踪
 * - 相关人员管理
 * - 物料处置决策
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
} from '@/components/ui';
import { ecnApi } from '@/services/api';

export default function ECNMaterialImpact() {
  const { ecnId } = useParams();
  const [loading, setLoading] = useState(true);
  const [materialImpact, setMaterialImpact] = useState(null);
  const [executionProgress, setExecutionProgress] = useState(null);
  const [stakeholders, setStakeholders] = useState([]);

  useEffect(() => {
    loadMaterialImpact();
  }, [ecnId]);

  const loadMaterialImpact = async () => {
    try {
      setLoading(true);
      const response = await ecnApi.analyzeMaterialImpact(ecnId);
      setMaterialImpact(response.data);
    } catch (error) {
      console.error('加载物料影响分析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadExecutionProgress = async () => {
    try {
      const response = await ecnApi.getExecutionProgress(ecnId);
      setExecutionProgress(response.data);
    } catch (error) {
      console.error('加载执行进度失败:', error);
    }
  };

  const handleMaterialDisposition = async (materialId, dispositionData) => {
    try {
      await ecnApi.updateMaterialDisposition(ecnId, materialId, dispositionData);
      loadExecutionProgress();
    } catch (error) {
      console.error('更新物料处置失败:', error);
    }
  };

  const STATUS_COLORS = {
    NOT_PURCHASED: 'bg-gray-200',
    ORDERED: 'bg-blue-200',
    IN_TRANSIT: 'bg-yellow-200',
    IN_STOCK: 'bg-green-200',
  };

  const STATUS_LABELS = {
    NOT_PURCHASED: '未采购',
    ORDERED: '已下单',
    IN_TRANSIT: '在途',
    IN_STOCK: '已入库',
  };

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">ECN 物料影响跟踪</h1>
        <p className="text-gray-500">跟踪 ECN 对物料的影响和执行进度</p>
      </div>

      <Tabs defaultValue="impact" className="space-y-4">
        <TabsList>
          <TabsTrigger value="impact">物料影响分析</TabsTrigger>
          <TabsTrigger value="progress">执行进度</TabsTrigger>
          <TabsTrigger value="stakeholders">相关人员</TabsTrigger>
        </TabsList>

        {/* 物料影响分析 */}
        <TabsContent value="impact">
          <Card>
            <CardHeader>
              <CardTitle>物料影响分析</CardTitle>
              <Button onClick={loadMaterialImpact} size="sm">
                重新分析
              </Button>
            </CardHeader>
            <CardContent>
              {materialImpact && (
                <div className="space-y-4">
                  {/* 概览统计 */}
                  <div className="grid grid-cols-4 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">受影响物料数</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {materialImpact.affected_materials_count || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">潜在损失</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-red-600">
                          ¥{materialImpact.potential_loss?.toLocaleString() || '0'}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">影响订单数</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {materialImpact.affected_orders_count || 0}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">交付影响</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {materialImpact.delivery_impact_days || 0} 天
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* 受影响物料清单 */}
                  <Card>
                    <CardHeader>
                      <CardTitle>受影响物料清单</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <thead>
                          <tr>
                            <th>物料编码</th>
                            <th>物料名称</th>
                            <th>当前状态</th>
                            <th>变更类型</th>
                            <th>影响分析</th>
                          </tr>
                        </thead>
                        <tbody>
                          {materialImpact.affected_materials?.map((material) => (
                            <tr key={material.id}>
                              <td>{material.material_code}</td>
                              <td>{material.material_name}</td>
                              <td>
                                <Badge className={STATUS_COLORS[material.current_status]}>
                                  {STATUS_LABELS[material.current_status] || material.current_status}
                                </Badge>
                              </td>
                              <td>{material.change_type}</td>
                              <td>{material.impact_analysis}</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 执行进度 */}
        <TabsContent value="progress">
          <Card>
            <CardHeader>
              <CardTitle>执行进度跟踪</CardTitle>
              <Button onClick={loadExecutionProgress} size="sm">
                刷新
              </Button>
            </CardHeader>
            <CardContent>
              {executionProgress && (
                <div className="space-y-4">
                  {/* 执行阶段进度 */}
                  <Card>
                    <CardHeader>
                      <CardTitle>执行阶段</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {executionProgress.phases?.map((phase) => (
                          <div key={phase.name} className="space-y-2">
                            <div className="flex justify-between">
                              <span>{phase.name}</span>
                              <span>{phase.progress}%</span>
                            </div>
                            <Progress value={phase.progress} />
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* 物料处理状态 */}
                  <Card>
                    <CardHeader>
                      <CardTitle>物料处理状态</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <thead>
                          <tr>
                            <th>物料</th>
                            <th>处置决策</th>
                            <th>状态</th>
                            <th>预计完成</th>
                            <th>操作</th>
                          </tr>
                        </thead>
                        <tbody>
                          {executionProgress.material_dispositions?.map((item) => (
                            <tr key={item.id}>
                              <td>{item.material_name}</td>
                              <td>
                                <Badge>{item.disposition}</Badge>
                              </td>
                              <td>{item.status}</td>
                              <td>{item.estimated_completion}</td>
                              <td>
                                <Button size="sm" variant="outline">
                                  更新
                                </Button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </CardContent>
                  </Card>

                  {/* 阻塞问题 */}
                  {executionProgress.blocking_issues?.length > 0 && (
                    <Alert variant="destructive">
                      <div className="font-bold">阻塞问题</div>
                      <ul className="list-disc list-inside mt-2">
                        {executionProgress.blocking_issues.map((issue, idx) => (
                          <li key={idx}>{issue}</li>
                        ))}
                      </ul>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 相关人员 */}
        <TabsContent value="stakeholders">
          <Card>
            <CardHeader>
              <CardTitle>相关人员</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <thead>
                  <tr>
                    <th>姓名</th>
                    <th>角色</th>
                    <th>订阅状态</th>
                    <th>通知渠道</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {stakeholders.map((stakeholder) => (
                    <tr key={stakeholder.id}>
                      <td>{stakeholder.name}</td>
                      <td>{stakeholder.role}</td>
                      <td>
                        <Badge variant={stakeholder.is_subscribed ? 'success' : 'default'}>
                          {stakeholder.is_subscribed ? '已订阅' : '未订阅'}
                        </Badge>
                      </td>
                      <td>{stakeholder.notification_channels?.join(', ')}</td>
                      <td>
                        <Button size="sm" variant="outline">
                          管理订阅
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
