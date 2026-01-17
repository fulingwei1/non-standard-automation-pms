import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { cn as _cn } from "../lib/utils";
import { rdProjectApi } from "../services/api";
import { formatDate as _formatDate, formatCurrency } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  Button,
  Badge,
  Progress,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent } from
"../components/ui";
import {
  ArrowLeft,
  Calculator,
  DollarSign,
  TrendingUp,
  BarChart3,
  PieChart,
  Download,
  Users,
  Clock } from
"lucide-react";

export default function RdCostSummary() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [costSummary, setCostSummary] = useState(null);
  const [timesheetSummary, setTimesheetSummary] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    if (id) {
      fetchProject();
      fetchCostSummary();
      fetchTimesheetSummary();
    }
  }, [id]);

  const fetchProject = async () => {
    try {
      const response = await rdProjectApi.get(id);
      const projectData = response.data?.data || response.data || response;
      setProject(projectData);
    } catch (err) {
      console.error("Failed to fetch project:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCostSummary = async () => {
    try {
      const response = await rdProjectApi.getCostSummary(id);
      const data = response.data?.data || response.data || response;
      setCostSummary(data);
    } catch (err) {
      console.error("Failed to fetch cost summary:", err);
    }
  };

  const fetchTimesheetSummary = async () => {
    try {
      const response = await rdProjectApi.getTimesheetSummary(id);
      const data = response.data?.data || response.data || response;
      setTimesheetSummary(data);
    } catch (err) {
      console.error("Failed to fetch timesheet summary:", err);
    }
  };

  if (loading) {
    return <div className="text-center py-12">加载中...</div>;
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">研发项目不存在</p>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => navigate("/rd-projects")}>

          返回列表
        </Button>
      </div>);

  }

  return (
    <motion.div initial="hidden" animate="visible">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(`/rd-projects/${id}`)}>

            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-white">研发费用汇总</h1>
            <p className="text-sm text-slate-400 mt-1">
              {project.project_name}
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate(`/rd-projects/${id}/reports`)}>

          <Download className="h-4 w-4 mr-2" />
          导出报表
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400">总费用</p>
              <DollarSign className="h-4 w-4 text-primary" />
            </div>
            <p className="text-2xl font-semibold text-white">
              {formatCurrency(costSummary?.total_cost || 0)}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              预算: {formatCurrency(project.budget_amount || 0)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400">人工费用</p>
              <Users className="h-4 w-4 text-emerald-400" />
            </div>
            <p className="text-2xl font-semibold text-emerald-400">
              {formatCurrency(costSummary?.labor_cost || 0)}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {costSummary?.labor_cost && costSummary?.total_cost ?
              (
              costSummary.labor_cost / costSummary.total_cost *
              100).
              toFixed(1) :
              0}
              %占比
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400">材料费用</p>
              <BarChart3 className="h-4 w-4 text-blue-400" />
            </div>
            <p className="text-2xl font-semibold text-blue-400">
              {formatCurrency(costSummary?.material_cost || 0)}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {costSummary?.material_cost && costSummary?.total_cost ?
              (
              costSummary.material_cost / costSummary.total_cost *
              100).
              toFixed(1) :
              0}
              %占比
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-400">加计扣除</p>
              <TrendingUp className="h-4 w-4 text-primary" />
            </div>
            <p className="text-2xl font-semibold text-primary">
              {formatCurrency(costSummary?.deductible_amount || 0)}
            </p>
            <p className="text-xs text-slate-500 mt-1">175%扣除</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">费用概览</TabsTrigger>
          <TabsTrigger value="byType">按类型汇总</TabsTrigger>
          <TabsTrigger value="timesheet">工时汇总</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Budget Progress */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                预算执行情况
              </h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-slate-400">已归集费用</span>
                    <span className="text-white font-medium">
                      {formatCurrency(costSummary?.total_cost || 0)} /{" "}
                      {formatCurrency(project.budget_amount || 0)}
                    </span>
                  </div>
                  <Progress
                    value={
                    project.budget_amount && project.budget_amount > 0 ?
                    (costSummary?.total_cost || 0) /
                    project.budget_amount *
                    100 :
                    0
                    }
                    color={
                    project.budget_amount &&
                    (costSummary?.total_cost || 0) > project.budget_amount ?
                    "danger" :
                    "primary"
                    } />

                  <div className="flex justify-between text-xs text-slate-500 mt-2">
                    <span>
                      执行率:{" "}
                      {project.budget_amount && project.budget_amount > 0 ?
                      (
                      (costSummary?.total_cost || 0) /
                      project.budget_amount *
                      100).
                      toFixed(1) :
                      0}
                      %
                    </span>
                    <span>
                      剩余预算:{" "}
                      {formatCurrency(
                        (project.budget_amount || 0) - (
                        costSummary?.total_cost || 0)
                      )}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Cost Breakdown */}
          {costSummary &&
          <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-white mb-4">
                  费用构成
                </h3>
                <div className="space-y-4">
                  {costSummary.by_type && costSummary.by_type.length > 0 ?
                costSummary.by_type.map((item, idx) =>
                <div key={idx} className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">
                            {item.type_name}
                          </span>
                          <span className="text-white font-medium">
                            {formatCurrency(item.total_amount || 0)}
                          </span>
                        </div>
                        <Progress
                    value={
                    costSummary.total_cost && costSummary.total_cost > 0 ?
                    (item.total_amount || 0) /
                    costSummary.total_cost *
                    100 :
                    0
                    }
                    color="primary" />

                      </div>
                ) :

                <div className="text-center py-8 text-slate-500">
                      暂无费用数据
                    </div>
                }
                </div>
              </CardContent>
            </Card>
          }
        </TabsContent>

        {/* By Type Tab */}
        <TabsContent value="byType" className="space-y-6">
          {costSummary?.by_type && costSummary.by_type.length > 0 ?
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {costSummary.by_type.map((item, idx) =>
            <Card key={idx}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-white">
                        {item.type_name}
                      </h4>
                      <Badge variant="outline">
                        {costSummary.total_cost && costSummary.total_cost > 0 ?
                    (
                    (item.total_amount || 0) /
                    costSummary.total_cost *
                    100).
                    toFixed(1) :
                    0}
                        %
                      </Badge>
                    </div>
                    <p className="text-2xl font-bold text-primary mb-2">
                      {formatCurrency(item.total_amount || 0)}
                    </p>
                    <p className="text-sm text-slate-400">
                      {item.count || 0} 条记录
                    </p>
                  </CardContent>
                </Card>
            )}
            </div> :

          <Card>
              <CardContent className="p-6">
                <div className="text-center py-12 text-slate-500">
                  暂无费用数据
                </div>
              </CardContent>
            </Card>
          }
        </TabsContent>

        {/* Timesheet Tab */}
        <TabsContent value="timesheet" className="space-y-6">
          {timesheetSummary ?
          <>
              <Card>
                <CardContent className="p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">
                    工时统计
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-lg bg-white/[0.03]">
                      <p className="text-sm text-slate-400 mb-1">总工时</p>
                      <p className="text-2xl font-semibold text-white">
                        {timesheetSummary.total_hours?.toFixed(1) || 0} 小时
                      </p>
                    </div>
                    <div className="p-4 rounded-lg bg-white/[0.03]">
                      <p className="text-sm text-slate-400 mb-1">参与人数</p>
                      <p className="text-2xl font-semibold text-white">
                        {timesheetSummary.total_participants || 0} 人
                      </p>
                    </div>
                    <div className="p-4 rounded-lg bg-white/[0.03]">
                      <p className="text-sm text-slate-400 mb-1">工作天数</p>
                      <p className="text-2xl font-semibold text-white">
                        {timesheetSummary.total_days || 0} 天
                      </p>
                    </div>
                    <div className="p-4 rounded-lg bg-white/[0.03]">
                      <p className="text-sm text-slate-400 mb-1">平均工时</p>
                      <p className="text-2xl font-semibold text-white">
                        {timesheetSummary.total_participants &&
                      timesheetSummary.total_hours ?
                      (
                      timesheetSummary.total_hours /
                      timesheetSummary.total_participants).
                      toFixed(1) :
                      0}{" "}
                        小时/人
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {timesheetSummary.by_user &&
            timesheetSummary.by_user.length > 0 &&
            <Card>
                    <CardContent className="p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">
                        按人员统计
                      </h3>
                      <div className="space-y-3">
                        {timesheetSummary.by_user.map((user, idx) =>
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 rounded-lg bg-white/[0.02]">

                            <div className="flex items-center gap-3">
                              <div className="p-2 rounded-lg bg-primary/20">
                                <Users className="h-4 w-4 text-primary" />
                              </div>
                              <div>
                                <p className="font-medium text-white">
                                  {user.user_name}
                                </p>
                                <p className="text-xs text-slate-500">
                                  {user.days || 0} 天
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-semibold text-white">
                                {user.total_hours?.toFixed(1) || 0} 小时
                              </p>
                              <p className="text-xs text-slate-500">
                                {timesheetSummary.total_hours &&
                        timesheetSummary.total_hours > 0 ?
                        (
                        (user.total_hours || 0) /
                        timesheetSummary.total_hours *
                        100).
                        toFixed(1) :
                        0}
                                %占比
                              </p>
                            </div>
                          </div>
                  )}
                      </div>
                    </CardContent>
                  </Card>
            }
            </> :

          <Card>
              <CardContent className="p-6">
                <div className="text-center py-12 text-slate-500">
                  <Clock className="h-12 w-12 mx-auto mb-4 text-slate-600" />
                  <p>暂无工时数据</p>
                  <p className="text-xs mt-2">
                    {project.linked_project_id ?
                  "工时数据从关联的非标项目中统计" :
                  "请先关联非标项目"}
                  </p>
                </div>
              </CardContent>
            </Card>
          }
        </TabsContent>
      </Tabs>
    </motion.div>);

}