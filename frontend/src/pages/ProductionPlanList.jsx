/**
 * Production Plan List Page - 生产计划列表页面
 * Features: 生产计划列表、创建、审批、发布
 */
import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  Calendar,
  Plus,
  Search,
  Filter,
  Eye,
  Edit,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  TrendingUp } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../components/ui/dialog";
import { cn as _cn, formatDate } from "../lib/utils";
import { productionApi, projectApi } from "../services/api";
import { confirmAction } from "@/lib/confirmAction";
const statusConfigs = {
  DRAFT: { label: "草稿", color: "bg-slate-500" },
  SUBMITTED: { label: "已提交", color: "bg-blue-500" },
  APPROVED: { label: "已批准", color: "bg-emerald-500" },
  PUBLISHED: { label: "已发布", color: "bg-violet-500" },
  EXECUTING: { label: "执行中", color: "bg-amber-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" }
};
const typeConfigs = {
  MASTER: { label: "主计划", color: "bg-blue-500" },
  WORKSHOP: { label: "车间计划", color: "bg-purple-500" }
};
export default function ProductionPlanList() {
  const _navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState([]);
  const [projects, setProjects] = useState([]);
  const [workshops, setWorkshops] = useState([]);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterWorkshop, setFilterWorkshop] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  // Dialogs
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);
  // Form state
  const [newPlan, setNewPlan] = useState({
    plan_name: "",
    plan_type: "MASTER",
    project_id: null,
    workshop_id: null,
    plan_start_date: "",
    plan_end_date: "",
    description: "",
    remark: ""
  });
  useEffect(() => {
    fetchProjects();
    fetchWorkshops();
    fetchPlans();
  }, [filterType, filterProject, filterWorkshop, filterStatus, searchKeyword]);
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };
  const fetchWorkshops = async () => {
    try {
      const res = await productionApi.workshops.list({ page_size: 1000 });
      setWorkshops(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch workshops:", error);
    }
  };
  const fetchPlans = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterType) {params.plan_type = filterType;}
      if (filterProject) {params.project_id = filterProject;}
      if (filterWorkshop) {params.workshop_id = filterWorkshop;}
      if (filterStatus) {params.status = filterStatus;}
      if (searchKeyword) {params.search = searchKeyword;}
      const res = await productionApi.productionPlans.list(params);
      const planList = res.data?.items || res.data || [];
      setPlans(planList);
    } catch (error) {
      console.error("Failed to fetch plans:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleCreatePlan = async () => {
    if (
    !newPlan.plan_name ||
    !newPlan.plan_start_date ||
    !newPlan.plan_end_date)
    {
      alert("请填写计划名称和日期");
      return;
    }
    try {
      await productionApi.productionPlans.create(newPlan);
      setShowCreateDialog(false);
      setNewPlan({
        plan_name: "",
        plan_type: "MASTER",
        project_id: null,
        workshop_id: null,
        plan_start_date: "",
        plan_end_date: "",
        description: "",
        remark: ""
      });
      fetchPlans();
    } catch (error) {
      console.error("Failed to create plan:", error);
      alert("创建计划失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const handleViewDetail = async (planId) => {
    try {
      const res = await productionApi.productionPlans.get(planId);
      setSelectedPlan(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch plan detail:", error);
    }
  };
  const handlePublish = async (planId) => {
    if (!await confirmAction("确认发布此生产计划？")) {return;}
    try {
      await productionApi.productionPlans.publish(planId);
      fetchPlans();
      if (showDetailDialog) {
        handleViewDetail(planId);
      }
    } catch (error) {
      console.error("Failed to publish plan:", error);
      alert("发布失败: " + (error.response?.data?.detail || error.message));
    }
  };
  const filteredPlans = useMemo(() => {
    return plans.filter((plan) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          plan.plan_no?.toLowerCase().includes(keyword) ||
          plan.plan_name?.toLowerCase().includes(keyword));

      }
      return true;
    });
  }, [plans, searchKeyword]);
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="生产计划管理"
        description="生产计划列表、创建、审批、发布" />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索计划编号、名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10" />

            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(typeConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterProject} onValueChange={setFilterProject}>
              <SelectTrigger>
                <SelectValue placeholder="选择项目" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部项目</SelectItem>
                {projects.map((proj) =>
                <SelectItem key={proj.id} value={proj.id.toString()}>
                    {proj.project_name}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterWorkshop} onValueChange={setFilterWorkshop}>
              <SelectTrigger>
                <SelectValue placeholder="选择车间" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部车间</SelectItem>
                {workshops.map((ws) =>
                <SelectItem key={ws.id} value={ws.id.toString()}>
                    {ws.workshop_name}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Action Bar */}
      <div className="flex justify-end">
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          新建计划
        </Button>
      </div>
      {/* Plan List */}
      <Card>
        <CardHeader>
          <CardTitle>生产计划列表</CardTitle>
          <CardDescription>
            共 {filteredPlans.length} 个生产计划
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          filteredPlans.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无生产计划</div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>计划编号</TableHead>
                  <TableHead>计划名称</TableHead>
                  <TableHead>类型</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>车间</TableHead>
                  <TableHead>计划日期</TableHead>
                  <TableHead>进度</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPlans.map((plan) =>
              <TableRow key={plan.id}>
                    <TableCell className="font-mono text-sm">
                      {plan.plan_no}
                    </TableCell>
                    <TableCell className="font-medium">
                      {plan.plan_name}
                    </TableCell>
                    <TableCell>
                      <Badge
                    className={
                    typeConfigs[plan.plan_type]?.color || "bg-slate-500"
                    }>

                        {typeConfigs[plan.plan_type]?.label || plan.plan_type}
                      </Badge>
                    </TableCell>
                    <TableCell>{plan.project_name || "-"}</TableCell>
                    <TableCell>{plan.workshop_name || "-"}</TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {plan.plan_start_date ?
                  formatDate(plan.plan_start_date) :
                  "-"}
                      {plan.plan_end_date &&
                  <>
                          <span className="mx-1">-</span>
                          {formatDate(plan.plan_end_date)}
                  </>
                  }
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span>{plan.progress || 0}%</span>
                        </div>
                        <Progress
                      value={plan.progress || 0}
                      className="h-1.5" />

                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                    className={
                    statusConfigs[plan.status]?.color || "bg-slate-500"
                    }>

                        {statusConfigs[plan.status]?.label || plan.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewDetail(plan.id)}>

                          <Eye className="w-4 h-4" />
                        </Button>
                        {plan.status === "APPROVED" &&
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handlePublish(plan.id)}>

                            <CheckCircle2 className="w-4 h-4" />
                    </Button>
                    }
                      </div>
                    </TableCell>
              </TableRow>
              )}
              </TableBody>
          </Table>
          }
        </CardContent>
      </Card>
      {/* Create Plan Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>新建生产计划</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  计划名称 *
                </label>
                <Input
                  value={newPlan.plan_name}
                  onChange={(e) =>
                  setNewPlan({ ...newPlan, plan_name: e.target.value })
                  }
                  placeholder="请输入计划名称" />

              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划类型
                  </label>
                  <Select
                    value={newPlan.plan_type}
                    onValueChange={(val) =>
                    setNewPlan({ ...newPlan, plan_type: val })
                    }>

                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(typeConfigs).map(([key, config]) =>
                      <SelectItem key={key} value={key}>
                          {config.label}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">项目</label>
                  <Select
                    value={newPlan.project_id?.toString() || ""}
                    onValueChange={(val) =>
                    setNewPlan({
                      ...newPlan,
                      project_id: val ? parseInt(val) : null
                    })
                    }>

                    <SelectTrigger>
                      <SelectValue placeholder="选择项目" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">无</SelectItem>
                      {projects.map((proj) =>
                      <SelectItem key={proj.id} value={proj.id.toString()}>
                          {proj.project_name}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {newPlan.plan_type === "WORKSHOP" &&
              <div>
                  <label className="text-sm font-medium mb-2 block">车间</label>
                  <Select
                  value={newPlan.workshop_id?.toString() || ""}
                  onValueChange={(val) =>
                  setNewPlan({
                    ...newPlan,
                    workshop_id: val ? parseInt(val) : null
                  })
                  }>

                    <SelectTrigger>
                      <SelectValue placeholder="选择车间" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">无</SelectItem>
                      {workshops.map((ws) =>
                    <SelectItem key={ws.id} value={ws.id.toString()}>
                          {ws.workshop_name}
                    </SelectItem>
                    )}
                    </SelectContent>
                  </Select>
              </div>
              }
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划开始日期 *
                  </label>
                  <Input
                    type="date"
                    value={newPlan.plan_start_date}
                    onChange={(e) =>
                    setNewPlan({
                      ...newPlan,
                      plan_start_date: e.target.value
                    })
                    } />

                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    计划结束日期 *
                  </label>
                  <Input
                    type="date"
                    value={newPlan.plan_end_date}
                    onChange={(e) =>
                    setNewPlan({ ...newPlan, plan_end_date: e.target.value })
                    } />

                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">描述</label>
                <textarea
                  className="w-full min-h-[80px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={newPlan.description}
                  onChange={(e) =>
                  setNewPlan({ ...newPlan, description: e.target.value })
                  }
                  placeholder="计划描述..." />

              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowCreateDialog(false)}>

              取消
            </Button>
            <Button onClick={handleCreatePlan}>创建</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Plan Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              {selectedPlan?.plan_name} - {selectedPlan?.plan_no}
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedPlan &&
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划编号</div>
                    <div className="font-mono">{selectedPlan.plan_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge
                    className={statusConfigs[selectedPlan.status]?.color}>

                      {statusConfigs[selectedPlan.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划类型</div>
                    <Badge
                    className={typeConfigs[selectedPlan.plan_type]?.color}>

                      {typeConfigs[selectedPlan.plan_type]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">项目</div>
                    <div>{selectedPlan.project_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">车间</div>
                    <div>{selectedPlan.workshop_name || "-"}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">进度</div>
                    <div className="space-y-1">
                      <div className="text-lg font-bold">
                        {selectedPlan.progress || 0}%
                      </div>
                      <Progress
                      value={selectedPlan.progress || 0}
                      className="h-2" />

                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划开始</div>
                    <div>
                      {selectedPlan.plan_start_date ?
                    formatDate(selectedPlan.plan_start_date) :
                    "-"}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">计划结束</div>
                    <div>
                      {selectedPlan.plan_end_date ?
                    formatDate(selectedPlan.plan_end_date) :
                    "-"}
                    </div>
                  </div>
                </div>
                {selectedPlan.description &&
              <div>
                    <div className="text-sm text-slate-500 mb-1">描述</div>
                    <div>{selectedPlan.description}</div>
              </div>
              }
            </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}>

              关闭
            </Button>
            {selectedPlan && selectedPlan.status === "APPROVED" &&
            <Button onClick={() => handlePublish(selectedPlan.id)}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                发布计划
            </Button>
            }
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}