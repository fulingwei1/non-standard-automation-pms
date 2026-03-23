/**
 * Delay Reasons Report Page - 延期原因统计报表页面
 * Features: 显示任务延期原因统计（Top N），支持按原因/负责人分组
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";








import { progressApi, projectApi } from "../services/api";
import { cn } from "../lib/utils";

export default function DelayReasonsReport() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const projectIdFromQuery = searchParams.get("project_id");

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [personData, setPersonData] = useState(null);
  const [selectedProjectId, setSelectedProjectId] = useState(
    id ?
    parseInt(id) :
    projectIdFromQuery ?
    parseInt(projectIdFromQuery) :
    null
  );
  const [topN, setTopN] = useState(10);
  const [projects, setProjects] = useState([]);
  const [viewMode, setViewMode] = useState("reason"); // "reason" | "person"

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const res = await projectApi.list({ page: 1, page_size: 100 });
        const items = res.data?.items || res.data?.items || res.data || [];
        setProjects(Array.isArray(items) ? items : []);
      } catch (_error) {
        setProjects([]);
      }
    };
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      fetchProject();
    }
    fetchReportData();
  }, [selectedProjectId, topN]);

  const fetchProject = async () => {
    if (!selectedProjectId) {return;}
    try {
      const res = await projectApi.get(selectedProjectId);
      setProject(res.data || res);
    } catch (_error) {
      // 非关键操作失败时静默降级
    }
  };

  const fetchReportData = async () => {
    try {
      setLoading(true);
      const res = await progressApi.reports.getDelayReasons(
        selectedProjectId,
        topN
      );
      const data = res.data || res || {};
      setReportData(data);

      // 按负责人分组数据：从延期原因数据中聚合
      // 注：如果后端有专门的 API，可以替换为 API 调用
      if (data.detailed_tasks) {
        const personMap = {};
        (data.detailed_tasks || []).forEach((task) => {
          const personName = task.assignee_name || "未分配";
          if (!personMap[personName]) {
            personMap[personName] = {
              name: personName,
              count: 0,
              total_delay_days: 0,
              tasks: [],
            };
          }
          personMap[personName].count++;
          personMap[personName].total_delay_days += task.delay_days || 0;
          personMap[personName].tasks.push(task);
        });

        const personList = Object.values(personMap)
          .sort((a, b) => b.count - a.count)
          .slice(0, topN)
          .map((p, idx) => ({
            ...p,
            rank: idx + 1,
            avg_delay_days: p.count > 0 ? (p.total_delay_days / p.count).toFixed(1) : 0,
            percentage: data.total_delayed_tasks > 0
              ? ((p.count / data.total_delayed_tasks) * 100).toFixed(1)
              : 0,
          }));

        setPersonData({ persons: personList, total: data.total_delayed_tasks });
      } else {
        // 如果没有详细任务数据，使用模拟数据结构
        setPersonData(null);
      }
    } catch (_error) {
      // 非关键操作失败时静默降级
    } finally {
      setLoading(false);
    }
  };

  // 获取延期严重程度颜色
  const getDelayLevelColor = (avgDays) => {
    if (avgDays >= 14) return "text-red-400";
    if (avgDays >= 7) return "text-amber-400";
    if (avgDays >= 3) return "text-yellow-400";
    return "text-slate-400";
  };

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>);

  }

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {selectedProjectId &&
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${selectedProjectId}`)}>

              <ArrowLeft className="w-4 h-4 mr-2" />
              返回项目
          </Button>
          }
          <PageHeader
            title={
            selectedProjectId ?
            `${project?.project_name || "项目"} - 延期原因统计` :
            "延期原因统计"
            }
            description="分析任务延期的主要原因" />

        </div>
        <Button variant="outline" onClick={fetchReportData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="project-select">项目筛选</Label>
              <Select
                value={selectedProjectId?.toString() || "all"}
                onValueChange={(value) =>
                setSelectedProjectId(value === "all" ? null : parseInt(value))
                }>

                <SelectTrigger id="project-select" className="mt-2">
                  <SelectValue placeholder="选择项目" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部项目</SelectItem>
                  {(projects || []).map((p) => (
                    <SelectItem key={p.id} value={p.id?.toString()}>
                      {p.project_name || p.project_code || `项目#${p.id}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="top-n">显示Top N</Label>
              <Input
                id="top-n"
                type="number"
                min="1"
                max="50"
                value={topN || "unknown"}
                onChange={(e) =>
                setTopN(
                  Math.max(1, Math.min(50, parseInt(e.target.value) || 10))
                )
                }
                className="mt-2" />

            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Card */}
      {reportData && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">延期任务总数</div>
                <div className="text-3xl font-bold text-red-600">
                  {reportData.total_delayed_tasks || 0}
                </div>
              </div>
              <AlertTriangle className="w-12 h-12 text-red-500" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* 视图切换 Tabs */}
      <Tabs value={viewMode} onValueChange={setViewMode} className="space-y-4">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="reason" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            按原因分组
          </TabsTrigger>
          <TabsTrigger value="person" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            按负责人分组
          </TabsTrigger>
        </TabsList>

        {/* 按原因分组视图 */}
        <TabsContent value="reason" className="space-y-4">
          {reportData?.reasons && reportData.reasons?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  延期原因统计（Top {topN}）
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {(reportData.reasons || []).map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1">
                          <Badge
                            variant="outline"
                            className="w-8 h-8 flex items-center justify-center"
                          >
                            {index + 1}
                          </Badge>
                          <div className="flex-1">
                            <div className="font-medium">
                              {item.reason || "未填写原因"}
                            </div>
                            <div className="text-sm text-slate-500 mt-1">
                              {item.count} 个任务 ({item.percentage.toFixed(1)}%)
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">{item.count}</div>
                          <div className="text-xs text-slate-500">任务数</div>
                        </div>
                      </div>
                      <Progress value={item.percentage} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {reportData?.reasons && reportData.reasons?.length === 0 && (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-slate-400">
                  {reportData.total_delayed_tasks === 0
                    ? "暂无延期任务"
                    : "暂无延期原因数据"}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 按负责人分组视图 */}
        <TabsContent value="person" className="space-y-4">
          {personData?.persons && personData.persons.length > 0 ? (
            <>
              {/* 负责人排行榜 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    负责人延期排行榜（Top {topN}）
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="rounded-md border border-slate-800">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-16">排名</TableHead>
                          <TableHead>负责人</TableHead>
                          <TableHead className="text-right">延期任务数</TableHead>
                          <TableHead className="text-right">占比</TableHead>
                          <TableHead className="text-right">平均延期天数</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {personData.persons.map((person) => (
                          <TableRow key={person.name}>
                            <TableCell>
                              <Badge
                                variant={person.rank <= 3 ? "destructive" : "outline"}
                                className="w-8 h-8 flex items-center justify-center"
                              >
                                {person.rank}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <User className="w-4 h-4 text-slate-400" />
                                <span className="font-medium">{person.name}</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <span className="font-bold text-red-400">{person.count}</span>
                            </TableCell>
                            <TableCell className="text-right">
                              <Badge variant="secondary">{person.percentage}%</Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <span className={cn("font-medium", getDelayLevelColor(parseFloat(person.avg_delay_days)))}>
                                {person.avg_delay_days} 天
                              </span>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>

              {/* 负责人分析洞察 */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingDown className="w-5 h-5" />
                    负责人分析洞察
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 text-sm">
                    {personData.persons[0] && (
                      <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/30">
                        <div className="font-medium text-red-300 mb-1">延期最多</div>
                        <div className="text-slate-300">
                          {personData.persons[0].name} 负责的任务延期最多，共 {personData.persons[0].count} 个任务，
                          占总延期任务的 {personData.persons[0].percentage}%，
                          平均延期 {personData.persons[0].avg_delay_days} 天。
                        </div>
                      </div>
                    )}

                    {personData.persons.length >= 3 && (
                      <div className="p-3 bg-slate-500/10 rounded-lg border border-slate-500/30">
                        <div className="font-medium text-slate-300 mb-1">前3名占比</div>
                        <div className="text-slate-400">
                          前3名负责人共有 {personData.persons.slice(0, 3).reduce((sum, p) => sum + p.count, 0)} 个延期任务，
                          占总延期任务的 {personData.persons.slice(0, 3).reduce((sum, p) => sum + parseFloat(p.percentage), 0).toFixed(1)}%。
                        </div>
                      </div>
                    )}

                    {personData.persons.some((p) => parseFloat(p.avg_delay_days) >= 14) && (
                      <div className="p-3 bg-amber-500/10 rounded-lg border border-amber-500/30">
                        <div className="font-medium text-amber-300 mb-1">严重延期警告</div>
                        <div className="text-slate-300">
                          {personData.persons.filter((p) => parseFloat(p.avg_delay_days) >= 14).map((p) => p.name).join("、")} 的平均延期超过2周，需重点关注。
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-slate-400">
                  暂无负责人延期数据（需要后端提供详细任务数据）
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Insights */}
      {reportData?.reasons && reportData.reasons?.length > 0 &&
      <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              分析洞察
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              {reportData.reasons[0] &&
            <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="font-medium text-blue-900 mb-1">主要原因</div>
                  <div className="text-blue-700">
                    "{reportData.reasons[0].reason || "未填写原因"}"
                    是导致任务延期的主要原因， 涉及{" "}
                    {reportData.reasons[0].count} 个任务，占比{" "}
                    {reportData.reasons[0].percentage.toFixed(1)}%。
                  </div>
            </div>
            }
              {reportData.reasons?.length > 1 &&
            <div className="p-3 bg-slate-50 rounded-lg">
                  <div className="font-medium text-slate-900 mb-1">
                    前3大原因占比
                  </div>
                  <div className="text-slate-700">
                    前3大延期原因共涉及{" "}
                    {reportData.reasons.
                slice(0, 3).
                reduce((sum, item) => sum + item.count, 0)}{" "}
                    个任务， 占总延期任务的{" "}
                    {reportData.reasons.
                slice(0, 3).
                reduce((sum, item) => sum + item.percentage, 0).
                toFixed(1)}
                    %。
                  </div>
            </div>
            }
            </div>
          </CardContent>
      </Card>
      }
    </div>);

}
