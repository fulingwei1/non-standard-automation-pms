/**
 * Material Readiness Card Component
 * 物料准备状态卡片组件
 * 显示单个物料的准备状态信息
 */

import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Progress } from "../../components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody
} from "../../components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "../../components/ui/tooltip";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  XCircle,
  ChevronDown,
  ChevronRight,
  Eye,
  Edit,
  Download,
  MoreVertical,
  Package,
  Truck,
  Package2,
  AlertTriangle,
  Info
} from "lucide-react";
import {
  cn,
  formatDate,
  formatCurrency
} from "../../lib/utils";
import {
  getReadinessStatusConfig,
  getMaterialTypeConfig,
  getUrgencyConfig,
  getProcurementStatusConfig,
  getInspectionStatusConfig,
  calculateReadinessProgress,
  formatReadinessStatus,
  formatMaterialType,
  formatUrgency,
  formatProcurementStatus,
  formatInspectionStatus,
  isMaterialReady,
  isMaterialDelayed,
  isMaterialCritical
} from "@/lib/constants/materialReadiness";

/**
 * 物料准备状态卡片组件
 * @param {object} props - 组件属性
 * @param {object} props.material - 物料信息
 * @param {string} props.material.code - 物料编码
 * @param {string} props.material.name - 物料名称
 * @param {string} props.material.type - 物料类型
 * @param {string} props.material.readiness_status - 准备状态
 * @param {string} props.material.urgency_level - 紧急程度
 * @param {string} props.material.procurement_status - 采购状态
 * @param {string} props.material.inspection_status - 质检状态
 * @param {number} props.material.quantity - 数量
 * @param {number} props.material.unit_price - 单价
 * @param {string} props.material.project_code - 项目编码
 * @param {string} props.material.supplier - 供应商
 * @param {string} props.material.estimated_delivery - 预计交付日期
 * @param {string} props.material.actual_delivery - 实际交付日期
 * @param {string} props.material.updated_at - 更新时间
 * @param {boolean} [props.compact=false] - 是否紧凑模式
 * @param {boolean} [props.showActions=true] - 是否显示操作按钮
 * @param {function} [props.onView] - 查看详情回调
 * @param {function} [props.onEdit] - 编辑回调
 * @param {function} [props.onDownload] - 下载回调
 * @returns {JSX.Element}
 */
export function ReadinessCard({
  material,
  compact = false,
  showActions = true,
  onView,
  onEdit,
  onDownload,
  className
}) {
  const [showDetail, setShowDetail] = useState(false);

  // 获取配置
  const statusConfig = getReadinessStatusConfig(material.readiness_status);
  const typeConfig = getMaterialTypeConfig(material.type);
  const urgencyConfig = getUrgencyConfig(material.urgency_level);
  const procurementConfig = getProcurementStatusConfig(material.procurement_status);
  const inspectionConfig = getInspectionStatusConfig(material.inspection_status);

  // 计算进度
  const progress = calculateReadinessProgress(material.readiness_status);

  // 获取状态图标
  const getStatusIcon = () => {
    if (isMaterialReady(material.readiness_status)) {
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    }
    if (isMaterialDelayed(material.readiness_status)) {
      return <XCircle className="h-5 w-5 text-red-600" />;
    }
    return <Clock className="h-5 w-5 text-orange-600" />;
  };

  // 获取状态颜色
  const getStatusColor = () => {
    if (isMaterialReady(material.readiness_status)) {
      return "text-green-700 bg-green-50 border-green-200";
    }
    if (isMaterialDelayed(material.readiness_status)) {
      return "text-red-700 bg-red-50 border-red-200";
    }
    return "text-blue-700 bg-blue-50 border-blue-200";
  };

  // 获取紧急程度图标
  const getUrgencyIcon = () => {
    if (isMaterialCritical(material.urgency_level)) {
      return <AlertTriangle className="h-4 w-4" />;
    }
    return <Info className="h-4 w-4" />;
  };

  // 是否显示供应商信息
  const hasSupplierInfo = material.supplier && material.estimated_delivery;

  // 紧凑模式
  if (compact) {
    return (
      <Card
        className={cn(
          "h-full cursor-pointer transition-all hover:shadow-md",
          getStatusColor(),
          className
        )}
        onClick={() => onView?.(material)}
      >
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <typeConfig.icon className="h-4 w-4"  />
              <span className="font-medium text-sm">{material.code}</span>
            </div>
            {getUrgencyIcon()}
          </div>
          <p className="text-xs text-gray-600 mb-2 truncate">{material.name}</p>
          <div className="flex items-center justify-between">
            <Badge
              variant="secondary"
              className={cn(
                "text-xs",
                statusConfig.color,
                statusConfig.textColor
              )}
            >
              {statusConfig.label}
            </Badge>
            <span className="text-xs text-gray-500">
              {material.quantity}
            </span>
          </div>
          {hasSupplierInfo && (
            <div className="mt-2 flex items-center space-x-1 text-xs text-gray-500">
              <Truck className="h-3 w-3" />
              <span>{material.supplier}</span>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // 完整模式
  return (
    <TooltipProvider>
      <Card className={cn(
        "transition-all hover:shadow-lg",
        isMaterialCritical(material.urgency_level) && "border-red-200",
        className
      )}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3">
              <div className={cn(
                "flex items-center justify-center rounded-full p-2",
                getStatusColor()
              )}>
                {getStatusIcon()}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-1">
                  <Badge
                    variant="secondary"
                    className={cn(
                      "text-xs",
                      typeConfig.color,
                      typeConfig.textColor
                    )}
                  >
                    {typeConfig.label}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      urgencyConfig.color,
                      urgencyConfig.textColor
                    )}
                  >
                    {getUrgencyIcon()}
                    {urgencyConfig.label}
                  </Badge>
                </div>
                <CardTitle className="text-base font-semibold truncate">
                  {material.name}
                </CardTitle>
                <p className="text-sm text-gray-500">
                  {material.code}
                </p>
              </div>
            </div>
            {showActions && (
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDetail(!showDetail);
                }}
              >
                {showDetail ? (
                  <ChevronDown className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          {/* 基本信息 */}
          <div className="space-y-3">
            {/* 进度条 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  准备进度
                </span>
                <span className="text-sm text-gray-500">
                  {progress}%
                </span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>

            {/* 状态信息 */}
            <div className="grid grid-cols-2 gap-3">
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="p-3 rounded-lg bg-gray-50">
                    <div className="text-xs text-gray-500 mb-1">准备状态</div>
                    <div className="flex items-center space-x-2">
                      <Badge
                        className={cn(
                          "text-xs",
                          statusConfig.color,
                          statusConfig.textColor
                        )}
                      >
                        {statusConfig.label}
                      </Badge>
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">
                    {statusConfig.description}
                  </p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="p-3 rounded-lg bg-gray-50">
                    <div className="text-xs text-gray-500 mb-1">采购状态</div>
                    <div className="flex items-center space-x-2">
                      <Badge
                        className={cn(
                          "text-xs",
                          procurementConfig.color,
                          procurementConfig.textColor
                        )}
                      >
                        {procurementConfig.label}
                      </Badge>
                    </div>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>采购处理状态</p>
                </TooltipContent>
              </Tooltip>
            </div>

            {/* 数量和价值 */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg bg-gray-50">
                <div className="text-xs text-gray-500 mb-1">数量</div>
                <div className="text-sm font-medium">
                  {material.quantity || 0}
                </div>
              </div>
              <div className="p-3 rounded-lg bg-gray-50">
                <div className="text-xs text-gray-500 mb-1">总价值</div>
                <div className="text-sm font-medium text-green-600">
                  {formatCurrency((material.quantity || 0) * (material.unit_price || 0))}
                </div>
              </div>
            </div>

            {/* 交付信息 */}
            {hasSupplierInfo && (
              <div className="p-3 rounded-lg bg-gray-50">
                <div className="flex items-center space-x-2 mb-1">
                  <Truck className="h-4 w-4 text-gray-500" />
                  <span className="text-xs text-gray-500">供应商信息</span>
                </div>
                <div className="text-sm">
                  <div className="font-medium">{material.supplier}</div>
                  <div className="text-xs text-gray-500">
                    预计交付: {formatDate(material.estimated_delivery)}
                  </div>
                  {material.actual_delivery && (
                    <div className="text-xs text-gray-500">
                      实际交付: {formatDate(material.actual_delivery)}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 项目信息 */}
            <div className="p-3 rounded-lg bg-gray-50">
              <div className="flex items-center space-x-2 mb-1">
                <Package2 className="h-4 w-4 text-gray-500" />
                <span className="text-xs text-gray-500">所属项目</span>
              </div>
              <div className="text-sm">
                <div className="font-medium">{material.project_code}</div>
                <div className="text-xs text-gray-500">
                  更新时间: {formatDate(material.updated_at)}
                </div>
              </div>
            </div>
          </div>

          {/* 操作按钮 */}
          {showActions && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onView?.(material);
                  }}
                >
                  <Eye className="h-4 w-4 mr-1" />
                  查看详情
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit?.(material);
                  }}
                >
                  <Edit className="h-4 w-4 mr-1" />
                  编辑
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDownload?.(material);
                  }}
                >
                  <Download className="h-4 w-4 mr-1" />
                  导出
                </Button>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowDetail(!showDetail);
                }}
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>

        {/* 详情对话框 */}
        {showDetail && (
          <Dialog
            open={showDetail}
            onOpenChange={setShowDetail}
          >
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>物料详情</DialogTitle>
              </DialogHeader>
              <DialogBody>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        基本信息
                      </h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">物料编码</span>
                          <span>{material.code}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">物料名称</span>
                          <span>{material.name}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">物料类型</span>
                          <span>{formatMaterialType(material.type)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">规格型号</span>
                          <span>{material.specification || '-'}</span>
                        </div>
                      </div>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        状态信息
                      </h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">准备状态</span>
                          <Badge
                            className={cn(
                              statusConfig.color,
                              statusConfig.textColor
                            )}
                          >
                            {formatReadinessStatus(material.readiness_status)}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">紧急程度</span>
                          <Badge
                            className={cn(
                              urgencyConfig.color,
                              urgencyConfig.textColor
                            )}
                          >
                            {formatUrgency(material.urgency_level)}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">采购状态</span>
                          <Badge
                            className={cn(
                              procurementConfig.color,
                              procurementConfig.textColor
                            )}
                          >
                            {formatProcurementStatus(material.procurement_status)}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">质检状态</span>
                          <Badge
                            className={cn(
                              inspectionConfig.color,
                              inspectionConfig.textColor
                            )}
                          >
                            {formatInspectionStatus(material.inspection_status)}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      数量和价值
                    </h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">需求数量</span>
                        <span>{material.quantity || 0} {material.unit}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">单价</span>
                        <span>{formatCurrency(material.unit_price || 0)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">总价值</span>
                        <span className="font-medium text-green-600">
                          {formatCurrency((material.quantity || 0) * (material.unit_price || 0))}
                        </span>
                      </div>
                    </div>
                  </div>
                  {hasSupplierInfo && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">
                        交付信息
                      </h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">供应商</span>
                          <span>{material.supplier}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">预计交付</span>
                          <span>{formatDate(material.estimated_delivery)}</span>
                        </div>
                        {material.actual_delivery && (
                          <div className="flex justify-between">
                            <span className="text-gray-500">实际交付</span>
                            <span>{formatDate(material.actual_delivery)}</span>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <span className="text-gray-500">交付状态</span>
                          <Badge
                            className={cn(
                              material.actual_delivery
                                ? "bg-green-500 text-green-50"
                                : "bg-orange-500 text-orange-50"
                            )}
                          >
                            {material.actual_delivery ? "已交付" : "待交付"}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  )}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      项目信息
                    </h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">项目编码</span>
                        <span>{material.project_code}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">项目名称</span>
                        <span>{material.project_name || '-'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">创建时间</span>
                        <span>{formatDate(material.created_at)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">更新时间</span>
                        <span>{formatDate(material.updated_at)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </DialogBody>
            </DialogContent>
          </Dialog>
        )}
      </Card>
    </TooltipProvider>
  );
}

export default ReadinessCard;