import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import {
  Package, MapPin, Clock, Truck, User, Phone, MessageCircle,
  CheckCircle, XCircle, AlertTriangle, MoreVertical,
  Eye, Edit, Trash2, Share } from
'lucide-react';
import { cn } from "../../lib/utils";
import {
  deliveryStatusConfigs as _deliveryStatusConfigs,
  deliveryPriorityConfigs as _deliveryPriorityConfigs,
  deliveryMethodConfigs as _deliveryMethodConfigs,
  deliveryStageConfigs as _deliveryStageConfigs,
  getStatusConfig,
  getPriorityConfig,
  getMethodConfig,
  getStageConfig,
  formatStatus,
  formatPriority,
  formatMethod,
  formatStage as _formatStage } from
'./deliveryConstants';

const fadeIn = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } }
};

const pulse = {
  scale: [1, 1.05, 1],
  transition: { duration: 1.5, repeat: Infinity }
};

/**
 * 配送进度条组件
 */
const DeliveryProgress = ({ stage }) => {
  const _stageConfig = getStageConfig(stage);
  const stages = ['PREPARING', 'READY', 'DISPATCHED', 'LOADING', 'TRANSPORTING', 'UNLOADING', 'COMPLETED'];
  const currentStageIndex = stages.indexOf(stage);
  const progress = (currentStageIndex + 1) / stages.length * 100;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span>配送进度</span>
        <span>{Math.round(progress)}%</span>
      </div>
      <Progress value={progress} className="h-2" />
      <div className="flex justify-between text-xs text-slate-500">
        {stages.map((s, idx) =>
        <div key={s} className="text-center">
            <div className={cn(
            "w-3 h-3 rounded-full mx-auto mb-1",
            idx <= currentStageIndex ? "bg-green-500" : "bg-slate-300"
          )} />
            <span className="text-xs">{getStageConfig(s).label}</span>
        </div>
        )}
      </div>
    </div>);

};

/**
 * 配送位置追踪组件
 */
const LocationTracker = ({ locations = [] }) => {
  if (!locations || locations.length === 0) return null;

  const currentLocation = locations[locations.length - 1];
  const isDelivered = currentLocation.status === 'DELIVERED';

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm">
        <MapPin className={cn("w-4 h-4", isDelivered ? "text-green-500" : "text-orange-500")} />
        <span className={isDelivered ? "text-green-600" : "text-orange-600"}>
          {isDelivered ? "已送达" : "当前位置"}
        </span>
      </div>
      <div className="text-sm font-medium">{currentLocation.address}</div>
      <div className="text-xs text-slate-500">
        更新时间: {new Date(currentLocation.timestamp).toLocaleString()}
      </div>
      {locations.length > 1 &&
      <div className="text-xs text-slate-500">
          已经过 {locations.length} 个节点
      </div>
      }
    </div>);

};

/**
 * 配送任务卡片组件
 *
 * @param {Object} props
 * @param {Object} props.delivery - 配送任务数据
 * @param {boolean} props.selected - 是否选中
 * @param {Function} props.onSelect - 选择回调
 * @param {Function} props.onView - 查看详情回调
 * @param {Function} props.onEdit - 编辑回调
 * @param {Function} props.onCancel - 取消回调
 * @param {Function} props.onTrack - 追踪回调
 * @param {Function} props.onContact - 联系客户回调
 */
export const DeliveryCard = ({
  delivery,
  selected = false,
  onSelect,
  onView,
  onEdit,
  onCancel,
  onTrack,
  onContact,
  className
}) => {
  const statusConfig = getStatusConfig(delivery.status);
  const priorityConfig = getPriorityConfig(delivery.priority);
  const methodConfig = getMethodConfig(delivery.delivery_method);

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className={cn(
        "relative group cursor-pointer transition-all duration-200",
        selected && "ring-2 ring-blue-500",
        className
      )}
      onClick={() => onSelect && onSelect(delivery)}>

      <Card className={cn(
        "hover:shadow-md border-l-4",
        statusConfig.color.replace("bg-", "border-l-")
      )}>
        <CardHeader className="pb-3">
          <div className="flex justify-between items-start">
            <div className="flex items-start gap-3">
              <div className={cn(
                "w-10 h-10 rounded-lg flex items-center justify-center text-white",
                statusConfig.color
              )}>
                {statusConfig.icon}
              </div>
              <div className="flex-1">
                <CardTitle className="text-base flex items-center gap-2">
                  <span>配送单号: {delivery.delivery_no}</span>
                  {delivery.status === 'IN_TRANSIT' &&
                  <motion.span
                    variants={pulse}
                    className="text-red-500">

                      <Truck className="w-4 h-4" />
                  </motion.span>
                  }
                </CardTitle>
                <div className="flex items-center gap-2 mt-1">
                  <Badge className={priorityConfig.color}>
                    {formatPriority(delivery.priority)}
                  </Badge>
                  <Badge className={methodConfig.color}>
                    {formatMethod(delivery.delivery_method)}
                  </Badge>
                  {delivery.is_urgent &&
                  <Badge className="bg-red-500">紧急</Badge>
                  }
                </div>
              </div>
              <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {onView &&
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onView(delivery);
                  }}>

                    <Eye className="w-4 h-4" />
                </Button>
                }
                {onEdit &&
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEdit(delivery);
                  }}>

                    <Edit className="w-4 h-4" />
                </Button>
                }
                {onCancel &&
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-red-500"
                  onClick={(e) => {
                    e.stopPropagation();
                    onCancel(delivery);
                  }}>

                    <Trash2 className="w-4 h-4" />
                </Button>
                }
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 基本信息 */}
            <div className="space-y-3">
              <div>
                <div className="text-sm text-slate-500 mb-1">收货人</div>
                <div className="font-medium flex items-center gap-2">
                  <User className="w-4 h-4 text-slate-500" />
                  {delivery.recipient_name}
                </div>
                <div className="text-sm text-slate-600">
                  {delivery.recipient_phone}
                </div>
              </div>

              <div>
                <div className="text-sm text-slate-500 mb-1">收货地址</div>
                <div className="text-sm font-medium line-clamp-2">
                  {delivery.recipient_address}
                </div>
              </div>

              {delivery.vehicle_info &&
              <div>
                  <div className="text-sm text-slate-500 mb-1">配送车辆</div>
                  <div className="text-sm font-medium flex items-center gap-2">
                    <Truck className="w-4 h-4 text-slate-500" />
                    {delivery.vehicle_info.license_plate}
                  </div>
                  <div className="text-sm text-slate-600">
                    {delivery.vehicle_info.driver_name}
                  </div>
              </div>
              }
            </div>

            {/* 状态信息 */}
            <div className="space-y-3">
              <div>
                <div className="text-sm text-slate-500 mb-1">配送状态</div>
                <div className="flex items-center gap-2">
                  {delivery.status === 'DELIVERED' ?
                  <CheckCircle className="w-5 h-5 text-green-500" /> :
                  delivery.status === 'DELIVER_FAILED' ?
                  <XCircle className="w-5 h-5 text-red-500" /> :
                  delivery.status === 'IN_TRANSIT' ?
                  <AlertTriangle className="w-5 h-5 text-orange-500" /> :
                  null}
                  <span className={cn(
                    "font-medium",
                    delivery.status === 'DELIVERED' ? "text-green-600" :
                    delivery.status === 'DELIVER_FAILED' ? "text-red-600" :
                    "text-slate-600"
                  )}>
                    {formatStatus(delivery.status)}
                  </span>
                </div>
              </div>

              <div>
                <div className="text-sm text-slate-500 mb-1">预计送达时间</div>
                <div className="text-sm font-medium flex items-center gap-2">
                  <Clock className="w-4 h-4 text-slate-500" />
                  {new Date(delivery.planned_delivery_time).toLocaleString()}
                </div>
              </div>

              <DeliveryProgress stage={delivery.stage || 'PREPARING'} />

              <LocationTracker locations={delivery.locations} />
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2 mt-4 pt-4 border-t">
            {onTrack &&
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onTrack(delivery);
              }}
              className="flex-1">

                <MapPin className="w-4 h-4 mr-2" />
                实时追踪
            </Button>
            }
            {onContact &&
            <Button
              variant="outline"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onContact(delivery);
              }}
              className="flex-1">

                <Phone className="w-4 h-4 mr-2" />
                联系客户
            </Button>
            }
          </div>
        </CardContent>
      </Card>
    </motion.div>);

};

export default DeliveryCard;