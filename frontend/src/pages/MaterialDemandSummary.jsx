/**
 * Material Demand Summary Page - 物料需求汇总页面
 * Features: 多项目物料需求汇总、需求与库存对比、自动生成采购需求
 */
import { useState, useEffect, useMemo } from "react";
import {
  Package,
  Search,
  Filter,
  Download,
  Plus,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
  Calendar,
  RefreshCw } from
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
import { cn, formatCurrency as _formatCurrency, formatDate } from "../lib/utils";
import { materialDemandApi, projectApi } from "../services/api";
export default function MaterialDemandSummary() {
  const [loading, setLoading] = useState(true);
  const [demands, setDemands] = useState([]);
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);
  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterMaterial, _setFilterMaterial] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  // Dialogs
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [showVsStockDialog, setShowVsStockDialog] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [vsStockData, setVsStockData] = useState(null);
  // Form state
  const [generateParams, setGenerateParams] = useState({
    project_ids: [],
    material_ids: [],
    supplier_id: null
  });
  useEffect(() => {
    fetchProjects();
    fetchDemands();
  }, [filterProject, filterMaterial, startDate, endDate, searchKeyword]);
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  };
  const fetchDemands = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject) params.project_id = filterProject;
      if (filterMaterial) params.material_id = filterMaterial;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      if (searchKeyword) params.search = searchKeyword;
      const res = await materialDemandApi.list(params);
      const demandList = res.data?.items || res.data || [];
      setDemands(demandList);
      // Calculate summary
      const totalDemand = demandList.reduce(
        (sum, item) => sum + (item.total_demand || 0),
        0
      );
      const totalProjects = new Set(demandList.map((item) => item.project_id)).
      size;
      setSummary({
        total_materials: demandList.length,
        total_demand: totalDemand,
        total_projects: totalProjects
      });
    } catch (error) {
      console.error("Failed to fetch demands:", error);
    } finally {
      setLoading(false);
    }
  };
  const handleViewVsStock = async (materialId) => {
    try {
      const res = await materialDemandApi.getVsStock(materialId);
      setSelectedMaterial(demands.find((d) => d.material_id === materialId));
      setVsStockData(res.data || res);
      setShowVsStockDialog(true);
    } catch (error) {
      console.error("Failed to fetch vs stock data:", error);
    }
  };
  const handleGeneratePR = async () => {
    try {
      const params = {};
      if (generateParams.project_ids.length > 0) {
        params.project_ids = generateParams.project_ids.join(",");
      }
      if (generateParams.material_ids.length > 0) {
        params.material_ids = generateParams.material_ids.join(",");
      }
      if (generateParams.supplier_id) {
        params.supplier_id = generateParams.supplier_id;
      }
      await materialDemandApi.generatePR(params);
      setShowGenerateDialog(false);
      alert("采购需求生成成功");
    } catch (error) {
      console.error("Failed to generate PR:", error);
      alert(
        "生成采购需求失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };
  const filteredDemands = useMemo(() => {
    return demands.filter((demand) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          demand.material_code?.toLowerCase().includes(keyword) ||
          demand.material_name?.toLowerCase().includes(keyword));

      }
      return true;
    });
  }, [demands, searchKeyword]);
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="物料需求汇总"
        description="多项目物料需求汇总、需求与库存对比、自动生成采购需求" />

      {/* Summary Cards */}
      {summary &&
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">物料种类</div>
                  <div className="text-2xl font-bold">
                    {summary.total_materials || 0}
                  </div>
                </div>
                <Package className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">总需求数量</div>
                  <div className="text-2xl font-bold">
                    {summary.total_demand || 0}
                  </div>
                </div>
                <TrendingUp className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">涉及项目</div>
                  <div className="text-2xl font-bold">
                    {summary.total_projects || 0}
                  </div>
                </div>
                <BarChart3 className="w-8 h-8 text-violet-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      }
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索物料编码、名称..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10" />

            </div>
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
            <Input
              type="date"
              placeholder="开始日期"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)} />

            <Input
              type="date"
              placeholder="结束日期"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)} />

            <Button onClick={() => setShowGenerateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              生成采购需求
            </Button>
          </div>
        </CardContent>
      </Card>
      {/* Demand List */}
      <Card>
        <CardHeader>
          <CardTitle>物料需求列表</CardTitle>
          <CardDescription>
            共 {filteredDemands.length} 项物料需求
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ?
          <div className="text-center py-8 text-slate-400">加载中...</div> :
          filteredDemands.length === 0 ?
          <div className="text-center py-8 text-slate-400">暂无需求数据</div> :

          <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>物料编码</TableHead>
                  <TableHead>物料名称</TableHead>
                  <TableHead>总需求数量</TableHead>
                  <TableHead>最早需求日期</TableHead>
                  <TableHead>最晚需求日期</TableHead>
                  <TableHead>需求次数</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDemands.map((demand) =>
              <TableRow key={demand.material_id}>
                    <TableCell className="font-mono text-sm">
                      {demand.material_code}
                    </TableCell>
                    <TableCell className="font-medium">
                      {demand.material_name}
                    </TableCell>
                    <TableCell className="font-medium">
                      {demand.total_demand || 0}
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {demand.earliest_date ?
                  formatDate(demand.earliest_date) :
                  "-"}
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {demand.latest_date ?
                  formatDate(demand.latest_date) :
                  "-"}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {demand.demand_count || 0}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewVsStock(demand.material_id)}>

                          <BarChart3 className="w-4 h-4 mr-2" />
                          库存对比
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
              )}
              </TableBody>
            </Table>
          }
        </CardContent>
      </Card>
      {/* Generate PR Dialog */}
      <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>生成采购需求</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  选择项目（可选）
                </label>
                <Select
                  value={generateParams.project_ids[0]?.toString() || ""}
                  onValueChange={(val) =>
                  setGenerateParams({
                    ...generateParams,
                    project_ids: val ? [parseInt(val)] : []
                  })
                  }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择项目（留空则包含所有项目）" />
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
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">
                  默认供应商（可选）
                </label>
                <Input
                  type="number"
                  value={generateParams.supplier_id || ""}
                  onChange={(e) =>
                  setGenerateParams({
                    ...generateParams,
                    supplier_id: e.target.value ?
                    parseInt(e.target.value) :
                    null
                  })
                  }
                  placeholder="供应商ID" />

              </div>
              <div className="text-sm text-slate-500">
                将根据物料需求与库存对比，自动生成采购需求单
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowGenerateDialog(false)}>

              取消
            </Button>
            <Button onClick={handleGeneratePR}>生成</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Vs Stock Dialog */}
      <Dialog open={showVsStockDialog} onOpenChange={setShowVsStockDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              {selectedMaterial?.material_name} - 需求与库存对比
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {vsStockData &&
            <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-sm text-slate-500 mb-1">总需求</div>
                      <div className="text-2xl font-bold">
                        {vsStockData.total_demand || 0}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-sm text-slate-500 mb-1">
                        当前库存
                      </div>
                      <div className="text-2xl font-bold">
                        {vsStockData.current_stock || 0}
                      </div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-4">
                      <div className="text-sm text-slate-500 mb-1">缺口</div>
                      <div
                      className={cn(
                        "text-2xl font-bold",
                        (vsStockData.shortage || 0) > 0 ?
                        "text-red-600" :
                        "text-emerald-600"
                      )}>

                        {vsStockData.shortage || 0}
                      </div>
                    </CardContent>
                  </Card>
                </div>
                {vsStockData.details && vsStockData.details.length > 0 &&
              <div>
                    <div className="text-sm font-medium mb-3">需求明细</div>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>项目</TableHead>
                          <TableHead>机台</TableHead>
                          <TableHead>需求数量</TableHead>
                          <TableHead>需求日期</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {vsStockData.details.map((detail, index) =>
                    <TableRow key={index}>
                            <TableCell>{detail.project_name}</TableCell>
                            <TableCell>{detail.machine_name || "-"}</TableCell>
                            <TableCell>{detail.demand_qty}</TableCell>
                            <TableCell className="text-slate-500 text-sm">
                              {detail.required_date ?
                        formatDate(detail.required_date) :
                        "-"}
                            </TableCell>
                          </TableRow>
                    )}
                      </TableBody>
                    </Table>
                  </div>
              }
              </div>
            }
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowVsStockDialog(false)}>

              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>);

}