/**
 * 项目交付排产计划 - 甘特图页面
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Tabs, TabsContent, TabsList, TabsTrigger, Alert } from '@/components/ui';
import { projectDeliveryApi } from '@/services/api/projectDelivery';

export default function ProjectDeliveryScheduleGantt() {
  const { scheduleId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [ganttData, setGanttData] = useState(null);
  const [conflicts, setConflicts] = useState([]);

  useEffect(() => { loadGanttData(); loadConflicts(); }, [scheduleId]);

  const loadGanttData = async () => {
    try { setLoading(true); setGanttData(await projectDeliveryApi.getGanttData(scheduleId)); }
    catch (error) { console.error('加载甘特图失败:', error); }
    finally { setLoading(false); }
  };

  const loadConflicts = async () => {
    try { setConflicts(await projectDeliveryApi.getConflicts(scheduleId)); }
    catch (error) { console.error('加载冲突失败:', error); }
  };

  if (loading) return <div className="p-6">加载中...</div>;
  if (!ganttData) return <div className="p-6"><Alert variant="destructive">加载失败</Alert></div>;

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div><h1 className="text-2xl font-bold mb-2">{ganttData.schedule_name} - 甘特图</h1><p className="text-gray-500">版本：{ganttData.version}</p></div>
        <div className="space-x-2">
          <Button variant="outline" onClick={() => navigate(-1)}>返回</Button>
          <Button>导出 Excel</Button><Button>导出 PDF</Button>
        </div>
      </div>
      {conflicts.has_conflicts && (
        <Alert variant="destructive" className="mb-6">
          <div className="font-bold">发现 {conflicts.total_conflicts} 个冲突</div>
          <ul className="list-disc list-inside mt-2">
            {conflicts.engineer_conflicts?.map((c, i) => <li key={i}>{c.engineer_name} - {c.task1_name} 与 {c.task2_name} 冲突（{c.overlap_days}天）</li>)}
            {conflicts.purchase_conflicts?.map((c, i) => <li key={i}>{c.material_name} - {c.reason}</li>)}
          </ul>
        </Alert>
      )}
      <Tabs defaultValue="tasks">
        <TabsList><TabsTrigger value="tasks">任务</TabsTrigger><TabsTrigger value="purchases">长周期采购</TabsTrigger><TabsTrigger value="dependencies">依赖关系</TabsTrigger></TabsList>
        <TabsContent value="tasks">
          <Card><CardHeader><CardTitle>任务列表</CardTitle></CardHeader><CardContent>
            {ganttData.tasks.length === 0 ? <div className="text-center py-8 text-gray-500">暂无任务</div> : (
              <div className="space-y-2">
                {ganttData.tasks.map(task => (
                  <div key={task.id} className={`p-4 border rounded ${task.has_conflict ? 'border-red-500 bg-red-50' : ''}`}>
                    <div className="flex justify-between">
                      <div>
                        <div className="font-bold">{task.task_no} - {task.name}</div>
                        <div className="text-sm text-gray-500">工程师：{task.engineer || '-'} | 时间：{task.start} 至 {task.end} | 工时：{task.hours}h | 进度：{task.progress}%</div>
                      </div>
                      <div>{task.has_conflict && <Badge variant="destructive">冲突</Badge>}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="purchases">
          <Card><CardHeader><CardTitle>长周期采购清单</CardTitle></CardHeader><CardContent>
            {ganttData.long_cycle_purchases.length === 0 ? <div className="text-center py-8 text-gray-500">暂无</div> : (
              <div className="space-y-2">
                {ganttData.long_cycle_purchases.map(item => (
                  <div key={item.id} className="p-4 border rounded">
                    <div className="font-bold">{item.item_no} - {item.material}</div>
                    <div className="text-sm text-gray-500">供应商：{item.supplier} | 交期：{item.lead_time}天 | 到货：{item.arrival_date}</div>
                    {item.is_critical && <Badge variant="destructive" className="mt-2">关键物料</Badge>}
                  </div>
                ))}
              </div>
            )}
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="dependencies">
          <Card><CardHeader><CardTitle>依赖关系</CardTitle></CardHeader><CardContent>
            {ganttData.dependencies.length === 0 ? <div className="text-center py-8 text-gray-500">暂无</div> : (
              <div className="space-y-2">
                {ganttData.dependencies.map((dep, i) => <div key={i} className="p-4 border rounded">任务 {dep.from_task} → 任务 {dep.to_task} ({dep.type}, 延迟{dep.lag_days}天)</div>)}
              </div>
            )}
          </CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
