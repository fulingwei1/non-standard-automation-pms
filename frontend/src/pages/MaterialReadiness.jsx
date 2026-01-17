/**
 * Material Readiness - 齐套管理
 * 统一管理物料齐套检查（工单级别）和齐套分析（项目级别）
 */

import { useState, useEffect, useCallback as _useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Package,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
  Search,
  Filter,
  Eye,
  Play,
  Calendar,
  TrendingUp,
  TrendingDown,
  Truck,
  Box,
  BarChart3,
  PieChart,
  LineChart,
  Download,
  Wrench,
  Zap,
  Cable,
  Bug,
  FileText,
  Settings,
  Plus,
  Edit,
  Trash2,
  ArrowUp,
  ArrowDown,
  Minus } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
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
  DialogFooter } from
"../components/ui/dialog";
import { cn as _cn, formatDate } from "../lib/utils";
import { materialApi, projectApi, supplierApi } from "../services/api";
import { toast } from "../components/ui/toast";
import {
  MATERIAL_STATUS,
  READINESS_STATUS,
  MATERIAL_TYPE,
  PRIORITY_LEVEL,
  MATERIAL_STATUS_LABELS,
  READINESS_STATUS_LABELS,
  MATERIAL_TYPE_LABELS,
  PRIORITY_LEVEL_LABELS,
  MATERIAL_STATUS_COLORS,
  READINESS_STATUS_COLORS,
  PRIORITY_COLORS,
  MATERIAL_STATUS_FILTER_OPTIONS,
  TYPE_FILTER_OPTIONS,
  PRIORITY_FILTER_OPTIONS,
  calculateReadinessRate,
  getMaterialStatusStats,
  getCriticalShortages,
  calculateReadinessStatus,
  getMaterialStatusLabel,
  getReadinessStatusLabel,
  getMaterialTypeLabel,
  getPriorityLevelLabel,
  getMaterialStatusColor,
  getReadinessStatusColor,
  getPriorityColor } from
"../components/material-readiness";

export default function MaterialReadiness() {
  const [loading, setLoading] = useState(true);
  const [materials, setMaterials] = useState([]);
  const [projects, setProjects] = useState([]);
  const [_suppliers, setSuppliers] = useState([]);
  const [selectedProject, setSelectedProject] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [viewMode, setViewMode] = useState("overview"); // overview, list, analytics
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);

  useEffect(() => {
    fetchData();
  }, [selectedProject, searchQuery, filterStatus, filterType, filterPriority]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {
        project_id: selectedProject && selectedProject !== "all" ? selectedProject : undefined,
        search: searchQuery,
        status: filterStatus || undefined,
        type: filterType || undefined,
        priority: filterPriority || undefined
      };

      const [materialsRes, projectsRes, suppliersRes] = await Promise.all([
      materialApi.list(params),
      projectApi.list({ page_size: 1000 }),
      supplierApi.list({ page_size: 1000 })]
      );

      setMaterials(materialsRes.data || []);
      setProjects(projectsRes.data || []);
      setSuppliers(suppliersRes.data || []);
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  };

  // 计算统计数据
  const stats = useMemo(() => {
    const statusStats = getMaterialStatusStats(materials);
    const readinessRate = calculateReadinessRate(materials);
    const criticalShortages = getCriticalShortages(materials);
    const readinessStatus = calculateReadinessStatus(materials);

    return {
      total: statusStats.total,
      available: statusStats.available,
      outOfStock: statusStats.outOfStock,
      onOrder: statusStats.onOrder,
      readinessRate,
      criticalShortages: criticalShortages.length,
      readinessStatus
    };
  }, [materials]);

  // 获取类型分布
  const typeDistribution = useMemo(() => {
    const distribution = {};

    Object.values(MATERIAL_TYPE).forEach((type) => {
      distribution[type] = 0;
    });

    materials.forEach((material) => {
      if (material.type) {
        distribution[material.type] = (distribution[material.type] || 0) + 1;
      }
    });

    return distribution;
  }, [materials]);

  // 获取紧急物料
  const urgentMaterials = useMemo(() => {
    return materials.filter((material) =>
    material.priority === PRIORITY_LEVEL.URGENT &&
    material.status !== MATERIAL_STATUS.AVAILABLE
    );
  }, [materials]);

  // 获取即将到货物料
  const arrivingMaterials = useMemo(() => {
    const today = new Date();
    const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

    return materials.filter((material) =>
    material.status === MATERIAL_STATUS.ON_ORDER &&
    material.expected_date &&
    new Date(material.expected_date) <= nextWeek
    );
  }, [materials]);

  const getStatusBadge = (status) => {
    return (
      <Badge
        variant="secondary"
        className="border-0"
        style={{
          backgroundColor: getMaterialStatusColor(status) + '20',
          color: getMaterialStatusColor(status)
        }}>

        {getMaterialStatusLabel(status)}
      </Badge>);

  };

  const getReadinessBadge = (status) => {
    return (
      <Badge
        variant="secondary"
        className="border-0"
        style={{
          backgroundColor: getReadinessStatusColor(status) + '20',
          color: getReadinessStatusColor(status)
        }}>

        {getReadinessStatusLabel(status)}
      </Badge>);

  };

  const getPriorityBadge = (priority) => {
    return (
      <Badge
        variant="secondary"
        className="border-0"
        style={{
          backgroundColor: getPriorityColor(priority) + '20',
          color: getPriorityColor(priority)
        }}>

        {getPriorityLevelLabel(priority)}
      </Badge>);

  };

  const getTypeIcon = (type) => {
    const iconMap = {
      [MATERIAL_TYPE.RAW_MATERIAL]: Package,
      [MATERIAL_TYPE.COMPONENT]: Box,
      [MATERIAL_TYPE.EQUIPMENT]: Wrench,
      [MATERIAL_TYPE.TOOL]: Settings,
      [MATERIAL_TYPE.CONSUMABLE]: Zap,
      [MATERIAL_TYPE.SOFTWARE]: FileText,
      [MATERIAL_TYPE.DOCUMENTATION]: FileText
    };

    const Icon = iconMap[type] || Package;
    return <Icon className="h-4 w-4" />;
  };

  const handleRefreshData = () => {
    fetchData();
  };

  const handleViewMaterial = (material) => {
    setSelectedMaterial(material);
    setShowDetailDialog(true);
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case 'createMaterial':
        toast.info('创建物料功能开发中...');
        break;
      case 'criticalShortages':
        setFilterPriority(PRIORITY_LEVEL.URGENT);
        setFilterStatus(MATERIAL_STATUS.OUT_OF_STOCK);
        setViewMode('list');
        break;
      case 'readinessAnalysis':
        setViewMode('analytics');
        break;
      case 'materialRequest':
        toast.info('物料申请功能开发中...');
        break;
      default:
        break;
    }
  };

  // 渲染概览视图
  const renderOverview = () =>
  <div className="space-y-6">
      {/* 关键指标 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">总物料数</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">
              可用: {stats.available}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">齐套率</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.readinessRate}%</div>
            <div className="text-xs text-muted-foreground">
              {getReadinessBadge(stats.readinessStatus)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">缺料</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.outOfStock}</div>
            <p className="text-xs text-muted-foreground">
              关键缺料: {stats.criticalShortages}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">在途物料</CardTitle>
            <Truck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.onOrder}</div>
            <p className="text-xs text-muted-foreground">
              即将到货: {arrivingMaterials.length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 状态分布 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>物料状态分布</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(MATERIAL_STATUS).map(([key, value]) => {
              const count = stats[key.toLowerCase()] || 0;
              const percentage = stats.total > 0 ? (count / stats.total * 100).toFixed(1) : 0;

              return (
                <div key={value} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getMaterialStatusColor(value) }} />

                      <span className="text-sm">{getMaterialStatusLabel(value)}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="secondary">{count}</Badge>
                      <span className="text-xs text-muted-foreground">{percentage}%</span>
                    </div>
                  </div>);

            })}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>紧急提醒</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <span className="text-sm font-medium">关键缺料</span>
                </div>
                <Badge variant="destructive">{stats.criticalShortages}</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Clock className="h-4 w-4 text-orange-600" />
                  <span className="text-sm font-medium">紧急物料</span>
                </div>
                <Badge variant="secondary">{urgentMaterials.length}</Badge>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <Truck className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium">即将到货</span>
                </div>
                <Badge variant="outline">{arrivingMaterials.length}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 类型分布 */}
      <Card>
        <CardHeader>
          <CardTitle>物料类型分布</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(typeDistribution).map(([type, count]) => {
            if (count === 0) return null;
            const percentage = stats.total > 0 ? (count / stats.total * 100).toFixed(1) : 0;

            return (
              <div key={type} className="text-center p-4 border rounded-lg">
                  <div className="flex justify-center mb-2">
                    {getTypeIcon(type)}
                  </div>
                  <p className="text-sm font-medium">{getMaterialTypeLabel(type)}</p>
                  <p className="text-2xl font-bold">{count}</p>
                  <p className="text-xs text-muted-foreground">{percentage}%</p>
                </div>);

          })}
          </div>
        </CardContent>
      </Card>

      {/* 快速操作 */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
            variant="outline"
            className="h-auto p-4 flex flex-col items-center space-y-2"
            onClick={() => handleQuickAction('createMaterial')}>

              <Plus className="h-6 w-6" />
              <span className="text-sm">新建物料</span>
            </Button>
            
            <Button
            variant="outline"
            className="h-auto p-4 flex flex-col items-center space-y-2"
            onClick={() => handleQuickAction('criticalShortages')}>

              <AlertTriangle className="h-6 w-6" />
              <span className="text-sm">关键缺料</span>
            </Button>
            
            <Button
            variant="outline"
            className="h-auto p-4 flex flex-col items-center space-y-2"
            onClick={() => handleQuickAction('materialRequest')}>

              <Truck className="h-6 w-6" />
              <span className="text-sm">物料申请</span>
            </Button>
            
            <Button
            variant="outline"
            className="h-auto p-4 flex flex-col items-center space-y-2"
            onClick={() => handleQuickAction('readinessAnalysis')}>

              <BarChart3 className="h-6 w-6" />
              <span className="text-sm">齐套分析</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>;


  // 渲染列表视图
  const renderListView = () =>
  <Card>
      <CardHeader>
        <CardTitle>物料列表</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>物料名称</TableHead>
                <TableHead>类型</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>优先级</TableHead>
                <TableHead>数量</TableHead>
                <TableHead>预计到货</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ?
            <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    加载中...
                  </TableCell>
                </TableRow> :
            materials.length === 0 ?
            <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    暂无物料数据
                  </TableCell>
                </TableRow> :

            materials.map((material) =>
            <TableRow key={material.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center space-x-2">
                        {getTypeIcon(material.type)}
                        <span>{material.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>{getMaterialTypeLabel(material.type)}</TableCell>
                    <TableCell>{getStatusBadge(material.status)}</TableCell>
                    <TableCell>{getPriorityBadge(material.priority)}</TableCell>
                    <TableCell>
                      {material.quantity} {material.unit}
                    </TableCell>
                    <TableCell>
                      {material.expected_date ? formatDate(material.expected_date) : '-'}
                    </TableCell>
                    <TableCell>
                      <div className="flex space-x-1">
                        <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleViewMaterial(material)}>

                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                    variant="ghost"
                    size="sm">

                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
            )
            }
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>;


  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-6">

      <PageHeader
        title="物料齐套管理"
        description="统一管理物料齐套检查和分析"
        actions={
        <div className="flex space-x-2">
            <Button variant="outline" onClick={handleRefreshData}>
              <RefreshCw className="mr-2 h-4 w-4" />
              刷新
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              导出
            </Button>
          </div>
        } />


      {/* 视图切换 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex items-center space-x-2">
              <Button
                variant={viewMode === "overview" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("overview")}>

                概览
              </Button>
              <Button
                variant={viewMode === "list" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("list")}>

                列表
              </Button>
              <Button
                variant={viewMode === "analytics" ? "default" : "outline"}
                size="sm"
                onClick={() => setViewMode("analytics")}>

                分析
              </Button>
            </div>

            <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="搜索物料..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10" />

              </div>
              
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="状态" />
                </SelectTrigger>
                <SelectContent>
                  {MATERIAL_STATUS_FILTER_OPTIONS.map((option) =>
                  <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>

              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger>
                  <SelectValue placeholder="类型" />
                </SelectTrigger>
                <SelectContent>
                  {TYPE_FILTER_OPTIONS.map((option) =>
                  <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>

              <Select value={selectedProject} onValueChange={setSelectedProject}>
                <SelectTrigger>
                  <SelectValue placeholder="项目" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部项目</SelectItem>
                  {projects.map((project) =>
                  <SelectItem key={project.id} value={project.id}>
                      {project.name}
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 主要内容区域 */}
      {viewMode === "overview" && renderOverview()}
      {viewMode === "list" && renderListView()}
      {viewMode === "analytics" &&
      <Card>
          <CardHeader>
            <CardTitle>齐套分析</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 text-muted-foreground">
              齐套分析图表功能开发中...
            </div>
          </CardContent>
        </Card>
      }

      {/* 详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>物料详情</DialogTitle>
          </DialogHeader>
          {selectedMaterial &&
          <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">物料名称</p>
                  <p className="font-medium">{selectedMaterial.name}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">类型</p>
                  <p className="font-medium">{getMaterialTypeLabel(selectedMaterial.type)}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">状态</p>
                  <div className="mt-1">{getStatusBadge(selectedMaterial.status)}</div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">优先级</p>
                  <div className="mt-1">{getPriorityBadge(selectedMaterial.priority)}</div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">数量</p>
                  <p className="font-medium">{selectedMaterial.quantity} {selectedMaterial.unit}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">供应商</p>
                  <p className="font-medium">{selectedMaterial.supplier?.name || '-'}</p>
                </div>
              </div>
              
              {selectedMaterial.description &&
            <div>
                  <p className="text-sm text-muted-foreground">描述</p>
                  <p className="font-medium">{selectedMaterial.description}</p>
                </div>
            }
            </div>
          }
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>);

}