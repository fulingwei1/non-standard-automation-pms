/**
 * Material Alerts Component
 * 物料准备状态警报组件
 * 显示物料准备过程中的警报和异常信息
 */

import { useState, useMemo } from "react";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../../components/ui/dialog";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent } from
"../../components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger } from
"../../components/ui/tooltip";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  AlertTriangle,
  Info,
  Search,
  Filter,
  Download,
  RefreshCw,
  Eye,
  ExternalLink,
  Calendar,
  Package,
  MapPin,
  Phone,
  Mail,
  User } from
"lucide-react";
import {
  cn,
  formatDate as _formatDate,
  formatDateTime,
  formatCurrency as _formatCurrency,
  formatRelativeTime } from
"../../lib/utils";
import {
  getReadinessStatusConfig as _getReadinessStatusConfig,
  getMaterialTypeConfig as _getMaterialTypeConfig,
  getUrgencyConfig as _getUrgencyConfig,
  calculateReadinessProgress as _calculateReadinessProgress,
  formatReadinessStatus as _formatReadinessStatus,
  formatMaterialType,
  formatUrgency as _formatUrgency,
  isMaterialReady as _isMaterialReady,
  isMaterialDelayed as _isMaterialDelayed,
  isMaterialCritical as _isMaterialCritical } from
"./materialReadinessConstants";

/**
 * 警报级别配置
 */
const alertLevelConfigs = {
  CRITICAL: {
    label: "严重",
    color: "bg-red-500",
    textColor: "text-red-50",
    icon: <XCircle className="h-4 w-4" />
  },
  HIGH: {
    label: "高",
    color: "bg-orange-500",
    textColor: "text-orange-50",
    icon: <AlertTriangle className="h-4 w-4" />
  },
  MEDIUM: {
    label: "中",
    color: "bg-yellow-500",
    textColor: "text-yellow-50",
    icon: <AlertCircle className="h-4 w-4" />
  },
  LOW: {
    label: "低",
    color: "bg-blue-500",
    textColor: "text-blue-50",
    icon: <Info className="h-4 w-4" />
  },
  INFO: {
    label: "信息",
    color: "bg-gray-500",
    textColor: "text-gray-50",
    icon: <Info className="h-4 w-4" />
  }
};

/**
 * 警报类型配置
 */
const alertTypeConfigs = {
  DELAY_WARNING: {
    label: "延期警告",
    description: "物料交付时间可能延期",
    color: "bg-orange-100",
    borderColor: "border-orange-200",
    icon: <Clock className="h-5 w-5 text-orange-600" />
  },
  STOCK_INSUFFICIENT: {
    label: "库存不足",
    description: "库存数量低于需求量",
    color: "bg-red-100",
    borderColor: "border-red-200",
    icon: <Package className="h-5 w-5 text-red-600" />
  },
  PRICE_INCREASE: {
    label: "价格上涨",
    description: "物料采购价格上涨",
    color: "bg-yellow-100",
    borderColor: "border-yellow-200",
    icon: <AlertTriangle className="h-5 w-5 text-yellow-600" />
  },
  QUALITY_ISSUE: {
    label: "质量问题",
    description: "物料质量检验不合格",
    color: "bg-red-100",
    borderColor: "border-red-200",
    icon: <XCircle className="h-5 w-5 text-red-600" />
  },
  SUPPLIER_CHANGE: {
    label: "供应商变更",
    description: "供应商信息变更或风险",
    color: "bg-blue-100",
    borderColor: "border-blue-200",
    icon: <User className="h-5 w-5 text-blue-600" />
  },
  DELIVERY_EXCEPTION: {
    label: "交付异常",
    description: "交付过程出现异常",
    color: "bg-red-100",
    borderColor: "border-red-200",
    icon: <Truck className="h-5 w-5 text-red-600" />
  },
  APPROACHING_DEADLINE: {
    label: "临近截止",
    description: "交付时间临近截止日期",
    color: "bg-amber-100",
    borderColor: "border-amber-200",
    icon: <Calendar className="h-5 w-5 text-amber-600" />
  },
  STOCK_WARNING: {
    label: "库存预警",
    description: "库存处于预警水平",
    color: "bg-yellow-100",
    borderColor: "border-yellow-200",
    icon: <Package className="h-5 w-5 text-yellow-600" />
  }
};

/**
 * 物料警报项组件
 * @param {object} props - 组件属性
 * @param {object} props.alert - 警报信息
 * @param {string} props.alert.id - 警报ID
 * @param {string} props.alert.level - 警报级别
 * @param {string} props.alert.type - 警报类型
 * @param {string} props.alert.title - 警报标题
 * @param {string} props.alert.description - 警报描述
 * @param {object} props.alert.material - 相关物料信息
 * @param {string} props.alert.supplier - 供应商信息
 * @param {string} props.alert.project - 项目信息
 * @param {Date} props.alert.created_at - 创建时间
 * @param {Date} props.alert.resolved_at - 解决时间
 * @param {boolean} props.alert.is_resolved - 是否已解决
 * @param {function} [props.onView] - 查看详情回调
 * @param {function} [props.onResolve] - 解决警报回调
 * @param {function} [props.onEscalate] - 升级警报回调
 * @returns {JSX.Element}
 */
export function MaterialAlertItem({
  alert,
  onView: _onView,
  onResolve,
  onEscalate,
  className
}) {
  const [showDetail, setShowDetail] = useState(false);

  // 获取配置
  const levelConfig = alertLevelConfigs[alert.level];
  const typeConfig = alertTypeConfigs[alert.type];

  // 格式化时间
  const timeAgo = formatRelativeTime(alert.created_at);

  return (
    <TooltipProvider>
      <Card
        className={cn(
          "transition-all hover:shadow-md",
          typeConfig.color,
          typeConfig.borderColor,
          "border",
          alert.is_resolved && "opacity-60",
          className
        )}>

        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            {/* 警报图标和信息 */}
            <div className="flex items-start space-x-3 flex-1">
              <div className={cn(
                "flex items-center justify-center rounded-full p-1.5",
                levelConfig.color,
                levelConfig.textColor
              )}>
                {levelConfig.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <h3 className="text-sm font-semibold text-gray-900 truncate">
                    {alert.title}
                  </h3>
                  {!alert.is_resolved &&
                  <Badge
                    className={cn(
                      "text-xs",
                      levelConfig.color,
                      levelConfig.textColor
                    )}>

                      {levelConfig.label}
                  </Badge>
                  }
                  <Badge
                    variant="outline"
                    className="text-xs">

                    {typeConfig.label}
                  </Badge>
                </div>
                <p className="text-xs text-gray-600 mb-2">
                  {alert.description}
                </p>
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <Package className="h-3 w-3" />
                    <span className="truncate">
                      {alert.material?.code || "未知物料"}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <MapPin className="h-3 w-3" />
                    <span className="truncate">
                      {alert.project?.code || "未知项目"}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <User className="h-3 w-3" />
                    <span className="truncate">
                      {alert.supplier?.name || "未知供应商"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* 操作按钮 */}
            <div className="flex items-center space-x-2 ml-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    onClick={() => setShowDetail(!showDetail)}>

                    <Eye className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>查看详情</p>
                </TooltipContent>
              </Tooltip>

              {!alert.is_resolved &&
              <>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => onResolve?.(alert)}>

                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>标记为已解决</p>
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      onClick={() => onEscalate?.(alert)}>

                        <AlertTriangle className="h-4 w-4 text-orange-600" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>升级警报</p>
                    </TooltipContent>
                  </Tooltip>
              </>
              }

              {alert.is_resolved &&
              <div className="flex items-center space-x-1 text-xs text-gray-500">
                  <CheckCircle2 className="h-3 w-3 text-green-600" />
                  <span>已解决</span>
              </div>
              }
            </div>
          </div>

          {/* 时间信息 */}
          <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
            <span>{timeAgo}</span>
            {alert.resolved_at &&
            <span>
                解决于 {formatDateTime(alert.resolved_at)}
            </span>
            }
          </div>

          {/* 详情对话框 */}
          {showDetail &&
          <Dialog
            open={showDetail}
            onOpenChange={setShowDetail}>

              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>警报详情</DialogTitle>
                </DialogHeader>
                <DialogBody>
                  <div className="space-y-4">
                    {/* 基本信息 */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        警报信息
                      </h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">警报ID</span>
                          <span>{alert.id}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">警报级别</span>
                          <Badge
                          className={cn(
                            levelConfig.color,
                            levelConfig.textColor
                          )}>

                            {levelConfig.label}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">警报类型</span>
                          <span>{typeConfig.label}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">标题</span>
                          <span>{alert.title}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">描述</span>
                          <span>{alert.description}</span>
                        </div>
                      </div>
                    </div>

                    {/* 相关信息 */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        相关信息
                      </h4>
                      <div className="space-y-1 text-sm">
                        {alert.material &&
                      <>
                            <div className="flex justify-between">
                              <span className="text-gray-500">物料编码</span>
                              <span>{alert.material.code}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">物料名称</span>
                              <span>{alert.material.name}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">物料类型</span>
                              <span>{formatMaterialType(alert.material.type)}</span>
                            </div>
                      </>
                      }
                        {alert.supplier &&
                      <>
                            <div className="flex justify-between">
                              <span className="text-gray-500">供应商</span>
                              <span>{alert.supplier.name}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">联系人</span>
                              <span>{alert.supplier.contact || '-'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">联系电话</span>
                              <span>{alert.supplier.phone || '-'}</span>
                            </div>
                      </>
                      }
                        {alert.project &&
                      <>
                            <div className="flex justify-between">
                              <span className="text-gray-500">项目编码</span>
                              <span>{alert.project.code}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-500">项目名称</span>
                              <span>{alert.project.name || '-'}</span>
                            </div>
                      </>
                      }
                      </div>
                    </div>

                    {/* 时间信息 */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        时间信息
                      </h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">创建时间</span>
                          <span>{formatDateTime(alert.created_at)}</span>
                        </div>
                        {alert.resolved_at &&
                      <div className="flex justify-between">
                            <span className="text-gray-500">解决时间</span>
                            <span>{formatDateTime(alert.resolved_at)}</span>
                      </div>
                      }
                        <div className="flex justify-between">
                          <span className="text-gray-500">状态</span>
                          <Badge
                          className={cn(
                            alert.is_resolved ?
                            "bg-green-500 text-green-50" :
                            "bg-red-500 text-red-50"
                          )}>

                            {alert.is_resolved ? "已解决" : "未解决"}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    {/* 解决方案 */}
                    {alert.resolution &&
                  <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">
                          解决方案
                        </h4>
                        <p className="text-sm text-gray-600">
                          {alert.resolution}
                        </p>
                  </div>
                  }
                  </div>
                </DialogBody>
                <DialogFooter>
                  {!alert.is_resolved &&
                <>
                      <Button variant="outline" onClick={() => onResolve?.(alert)}>
                        标记为已解决
                      </Button>
                      <Button variant="outline" onClick={() => onEscalate?.(alert)}>
                        升级警报
                      </Button>
                </>
                }
                  <Button onClick={() => setShowDetail(false)}>
                    关闭
                  </Button>
                </DialogFooter>
              </DialogContent>
          </Dialog>
          }
        </CardContent>
      </Card>
    </TooltipProvider>);

}

/**
 * 物料警报列表组件
 * @param {object} props - 组件属性
 * @param {Array<object>} props.alerts - 警报列表
 * @param {string} [props.filter="active"] - 过滤器 ('active', 'resolved', 'all')
 * @param {string} [props.sort="newest"] - 排序 ('newest', 'oldest', 'level')
 * @param {boolean} [props.showStats=true] - 是否显示统计信息
 * @param {function} [props.onView] - 查看详情回调
 * @param {function} [props.onResolve] - 解决警报回调
 * @param {function} [props.onEscalate] - 升级警报回调
 * @param {function} [props.onExport] - 导出警报回调
 * @param {function} [props.onRefresh] - 刷新警报回调
 * @returns {JSX.Element}
 */
export function MaterialAlerts({
  alerts,
  filter = "active",
  sort = "newest",
  showStats = true,
  onView,
  onResolve,
  onEscalate,
  onExport,
  onRefresh,
  className
}) {
  // 过滤警报
  const filteredAlerts = useMemo(() => {
    let filtered = [...alerts];

    if (filter === "active") {
      filtered = filtered.filter((alert) => !alert.is_resolved);
    } else if (filter === "resolved") {
      filtered = filtered.filter((alert) => alert.is_resolved);
    }

    // 排序
    if (sort === "newest") {
      filtered.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (sort === "oldest") {
      filtered.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    } else if (sort === "level") {
      const levelOrder = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"];
      filtered.sort((a, b) => levelOrder.indexOf(a.level) - levelOrder.indexOf(b.level));
    }

    return filtered;
  }, [alerts, filter, sort]);

  // 统计信息
  const stats = useMemo(() => {
    const total = alerts.length;
    const critical = alerts.filter((a) => a.level === "CRITICAL").length;
    const high = alerts.filter((a) => a.level === "HIGH").length;
    const medium = alerts.filter((a) => a.level === "MEDIUM").length;
    const low = alerts.filter((a) => a.level === "LOW").length;
    const info = alerts.filter((a) => a.level === "INFO").length;
    const resolved = alerts.filter((a) => a.is_resolved).length;
    const active = total - resolved;

    return { total, critical, high, medium, low, info, resolved, active };
  }, [alerts]);

  // 按级别分组
  const _alertsByLevel = useMemo(() => {
    const grouped = {
      CRITICAL: [],
      HIGH: [],
      MEDIUM: [],
      LOW: [],
      INFO: []
    };

    filteredAlerts.forEach((alert) => {
      grouped[alert.level].push(alert);
    });

    return grouped;
  }, [filteredAlerts]);

  return (
    <div className={cn("space-y-4", className)}>
      {/* 标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">
            物料准备警报
          </h2>
          <p className="text-sm text-gray-600">
            共 {stats.total} 个警报，{stats.active} 个未解决
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {onRefresh &&
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}>

              <RefreshCw className="h-4 w-4 mr-1" />
              刷新
          </Button>
          }
          {onExport &&
          <Button
            variant="outline"
            size="sm"
            onClick={onExport}>

              <Download className="h-4 w-4 mr-1" />
              导出
          </Button>
          }
        </div>
      </div>

      {/* 统计卡片 */}
      {showStats &&
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
          <Card>
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-gray-900">
                {stats.total}
              </div>
              <div className="text-xs text-gray-500">总计</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-red-600">
                {stats.critical}
              </div>
              <div className="text-xs text-gray-500">严重</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-orange-600">
                {stats.high}
              </div>
              <div className="text-xs text-gray-500">高</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {stats.medium}
              </div>
              <div className="text-xs text-gray-500">中</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-blue-600">
                {stats.low}
              </div>
              <div className="text-xs text-gray-500">低</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-gray-600">
                {stats.info}
              </div>
              <div className="text-xs text-gray-500">信息</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-green-600">
                {stats.resolved}
              </div>
              <div className="text-xs text-gray-500">已解决</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <div className="text-2xl font-bold text-orange-500">
                {stats.active}
              </div>
              <div className="text-xs text-gray-500">未解决</div>
            </CardContent>
          </Card>
      </div>
      }

      {/* 过滤器和排序 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Tabs value={filter} onValueChange={(value) => filter = value}>
            <TabsList>
              <TabsTrigger value="active">
                未解决 ({stats.active})
              </TabsTrigger>
              <TabsTrigger value="resolved">
                已解决 ({stats.resolved})
              </TabsTrigger>
              <TabsTrigger value="all">
                全部 ({stats.total})
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">排序：</span>
          <select
            className="text-sm border rounded px-2 py-1"
            value={sort}
            onChange={(e) => sort = e.target.value}>

            <option value="newest">最新优先</option>
            <option value="oldest">最早优先</option>
            <option value="level">级别优先</option>
          </select>
        </div>
      </div>

      {/* 警报列表 */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ?
        <Card>
            <CardContent className="p-8 text-center">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {filter === "resolved" ? "暂无已解决的警报" :
              filter === "active" ? "暂无未解决的警报" :
              "暂无警报"}
              </p>
            </CardContent>
        </Card> :

        filteredAlerts.map((alert) =>
        <MaterialAlertItem
          key={alert.id}
          alert={alert}
          onView={onView}
          onResolve={onResolve}
          onEscalate={onEscalate} />

        )
        }
      </div>
    </div>);

}

export default MaterialAlerts;