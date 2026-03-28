/**
 * ECN 成本影响跟踪页面
 * 功能：
 * - ECN 成本影响分析
 * - 成本执行跟踪
 * - 成本记录管理
 * - 成本预警
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
  Alert,
  AlertDescription,
} from '@/components/ui';
import { ecnApi } from '@/services/api';

export default function ECNCostImpact() {
  const { ecnId } = useParams();
  const [loading, setLoading] = useState(true);
  const [costImpact, setCostImpact] = useState(null);
  const [costTracking, setCostTracking] = useState(null);
  const [costRecords, setCostRecords] = useState([]);
  const [alerts, setAlerts] = useState([]);

  // 加载成本影响分析
  useEffect(() => {
    loadCostImpact();
  }, [ecnId]);

  const loadCostImpact = async () => {
    try {
      setLoading(true);
      const response = await ecnApi.analyzeCostImpact(ecnId);
      setCostImpact(response.data);
    } catch (error) {
      console.error('加载成本影响分析失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCostTracking = async () => {
    try {
      const response = await ecnApi.getCostTracking(ecnId);
      setCostTracking(response.data);
    } catch (error) {
      console.error('加载成本跟踪失败:', error);
    }
  };

  const loadCostRecords = async () => {
    try {
      const response = await ecnApi.getCostRecords(ecnId);
      setCostRecords(response.data);
    } catch (error) {
      console.error('加载成本记录失败:', error);
    }
  };

  const handleAddCostRecord = async (recordData) => {
    try {
      await ecnApi.createCostRecord(ecnId, recordData);
      loadCostRecords();
      loadCostTracking();
    } catch (error) {
      console.error('添加成本记录失败:', error);
    }
  };

  const COST_TYPE_LABELS = {
    SCRAP: '报废',
    REWORK: '返工',
    NEW_PURCHASE: '新购',
    CLAIM: '索赔',
    DELAY: '延期',
    MANAGEMENT: '管理',
  };

  const PRIORITY_LABELS = {
    LOW: '低',
    NORMAL: '普通',
    HIGH: '高',
    URGENT: '紧急',
  };

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">ECN 成本影响跟踪</h1>
        <p className="text-gray-500">跟踪 ECN 导致的成本变化和执行情况</p>
      </div>

      <Tabs defaultValue="impact" className="space-y-4">
        <TabsList>
          <TabsTrigger value="impact">成本影响分析</TabsTrigger>
          <TabsTrigger value="tracking">成本执行跟踪</TabsTrigger>
          <TabsTrigger value="records">成本记录</TabsTrigger>
          <TabsTrigger value="alerts">成本预警</TabsTrigger>
        </TabsList>

        {/* 成本影响分析 */}
        <TabsContent value="impact">
          <Card>
            <CardHeader>
              <CardTitle>成本影响分析</CardTitle>
              <Button onClick={loadCostImpact} size="sm">
                重新分析
              </Button>
            </CardHeader>
            <CardContent>
              {costImpact && (
                <div className="space-y-4">
                  {/* 总成本影响 */}
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">直接成本</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          ¥{costImpact.direct_cost?.toLocaleString() || '0'}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">间接成本</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          ¥{costImpact.indirect_cost?.toLocaleString() || '0'}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">总成本</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-red-600">
                          ¥{costImpact.total_cost?.toLocaleString() || '0'}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* 按类型统计 */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">按成本类型统计</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <thead>
                          <tr>
                            <th>成本类型</th>
                            <th>金额</th>
                            <th>占比</th>
                          </tr>
                        </thead>
                        <tbody>
                          {costImpact.by_type?.map((item) => (
                            <tr key={item.type}>
                              <td>{COST_TYPE_LABELS[item.type] || item.type}</td>
                              <td>¥{item.amount?.toLocaleString() || '0'}</td>
                              <td>{item.percentage || '0'}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </Table>
                    </CardContent>
                  </Card>

                  {/* 成本影响最大的物料 TOP10 */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">成本影响最大的物料 TOP10</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <thead>
                          <tr>
                            <th>物料编码</th>
                            <th>物料名称</th>
                            <th>成本影响</th>
                            <th>类型</th>
                          </tr>
                        </thead>
                        <tbody>
                          {costImpact.top_materials?.slice(0, 10).map((material) => (
                            <tr key={material.id}>
                              <td>{material.material_code}</td>
                              <td>{material.material_name}</td>
                              <td className="text-red-600">
                                ¥{material.cost_impact?.toLocaleString() || '0'}
                              </td>
                              <td>
                                <Badge variant={material.cost_impact > 10000 ? 'destructive' : 'default'}>
                                  {COST_TYPE_LABELS[material.cost_type] || material.cost_type}
                                </Badge>
                              </td>
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

        {/* 成本执行跟踪 */}
        <TabsContent value="tracking">
          <Card>
            <CardHeader>
              <CardTitle>成本执行跟踪</CardTitle>
              <Button onClick={loadCostTracking} size="sm">
                刷新
              </Button>
            </CardHeader>
            <CardContent>
              {costTracking && (
                <div className="space-y-4">
                  {/* 预算 vs 实际 */}
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">预算</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          ¥{costTracking.budget?.toLocaleString() || '0'}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">实际</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          ¥{costTracking.actual?.toLocaleString() || '0'}
                        </div>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">偏差</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className={`text-2xl font-bold ${costTracking.variance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {costTracking.variance >= 0 ? '+' : ''}{costTracking.variance?.toFixed(2) || '0'}%
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* 成本趋势 */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-sm">成本趋势</CardTitle>
                    </CardHeader>
                    <CardContent>
                      {/* TODO: 添加图表组件 */}
                      <div className="h-64 bg-gray-100 rounded flex items-center justify-center">
                        图表区域 - 显示月度成本趋势
                      </div>
                    </CardContent>
                  </Card>

                  {/* 预计最终成本 */}
                  <Alert>
                    <AlertDescription>
                      预计最终成本：¥{costTracking.estimated_final_cost?.toLocaleString() || '0'}
                      {costTracking.estimated_final_cost > costTracking.budget && (
                        <span className="text-red-600 ml-2">（超预算）</span>
                      )}
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 成本记录 */}
        <TabsContent value="records">
          <Card>
            <CardHeader>
              <CardTitle>成本记录</CardTitle>
              <Button onClick={() => loadCostRecords()} size="sm">
                刷新
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>成本类型</th>
                    <th>金额</th>
                    <th>原因</th>
                    <th>状态</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {costRecords.map((record) => (
                    <tr key={record.id}>
                      <td>{new Date(record.created_at).toLocaleDateString()}</td>
                      <td>
                        <Badge>{COST_TYPE_LABELS[record.cost_type] || record.cost_type}</Badge>
                      </td>
                      <td className="text-red-600">
                        ¥{record.amount?.toLocaleString() || '0'}
                      </td>
                      <td>{record.reason}</td>
                      <td>
                        <Badge variant={
                          record.status === 'APPROVED' ? 'success' :
                          record.status === 'PENDING' ? 'warning' : 'default'
                        }>
                          {record.status === 'APPROVED' ? '已批准' :
                           record.status === 'PENDING' ? '待审批' : '已拒绝'}
                        </Badge>
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

        {/* 成本预警 */}
        <TabsContent value="alerts">
          <Card>
            <CardHeader>
              <CardTitle>成本预警</CardTitle>
            </CardHeader>
            <CardContent>
              <Alert variant="destructive">
                <AlertDescription>
                  成本预警功能开发中...
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
