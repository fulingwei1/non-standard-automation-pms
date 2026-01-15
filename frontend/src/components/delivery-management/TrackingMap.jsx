import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  MapPin, Navigation, Truck, Users, Timer, Phone,
  MessageCircle, AlertTriangle, CheckCircle, Eye, RefreshCw,
  ZoomIn, ZoomOut, RotateCcw, Pause, Play
} from 'lucide-react';
import { cn } from "../../lib/utils";
import {
  deliveryStatusConfigs,
  deliveryPriorityConfigs,
  getStatusConfig,
  formatStatus
} from './deliveryConstants';

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
};

// 模拟地图组件
const MapComponent = ({ deliveries, selectedDelivery, onLocationSelect }) => {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // 模拟地图标记点
  const mapMarkers = [
    {
      id: 'depot',
      type: 'depot',
      name: '配送中心',
      coordinates: { x: 50, y: 50 },
      status: 'active'
    },
    ...deliveries.map((delivery, index) => ({
      id: delivery.delivery_no,
      type: 'delivery',
      name: delivery.recipient_name,
      coordinates: {
        x: 20 + (index % 5) * 15,
        y: 20 + Math.floor(index / 5) * 15
      },
      status: delivery.status,
      delivery: delivery
    }))
  ];

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.2, 3));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.2, 0.5));
  };

  const handleReset = () => {
    setZoomLevel(1);
    setIsPlaying(false);
  };

  return (
    <div className="relative bg-slate-100 rounded-lg overflow-hidden" style={{ height: '500px' }}>
      {/* 地图控制按钮 */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-10">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomIn}
          className="bg-white/90"
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleZoomOut}
          className="bg-white/90"
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReset}
          className="bg-white/90"
        >
          <RotateCcw className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsPlaying(!isPlaying)}
          className="bg-white/90"
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
        </Button>
      </div>

      {/* 模拟地图背景 */}
      <div
        className="relative w-full h-full bg-gradient-to-br from-green-100 to-blue-100"
        style={{ transform: `scale(${zoomLevel})`, transformOrigin: 'center' }}
      >
        {/* 道路网格 */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 100">
          <defs>
            <pattern id="road" patternUnits="userSpaceOnUse" width="10" height="10">
              <rect width="10" height="10" fill="none" />
              <rect width="8" height="8" x="1" y="1" fill="#cbd5e1" />
            </pattern>
          </defs>
          <rect width="100" height="100" fill="url(#road)" />
        </svg>

        {/* 地图标记 */}
        {mapMarkers.map((marker) => {
          const isSelected = selectedDelivery?.delivery_no === marker.id;
          const statusConfig = marker.type === 'delivery' ?
            getStatusConfig(marker.status) :
            { color: 'bg-blue-500', textColor: 'text-white' };

          return (
            <motion.div
              key={marker.id}
              className={cn(
                "absolute cursor-pointer transform -translate-x-1/2 -translate-y-1/2",
                isSelected ? "z-20" : "z-10"
              )}
              style={{
                left: `${marker.coordinates.x}%`,
                top: `${marker.coordinates.y}%`
              }}
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              onClick={() => onLocationSelect(marker.delivery || marker)}
            >
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center text-white shadow-lg",
                statusConfig.color,
                isSelected && "ring-4 ring-blue-400"
              )}>
                {marker.type === 'depot' ? (
                  <Truck className="w-4 h-4" />
                ) : (
                  <MapPin className="w-4 h-4" />
                )}
              </div>

              {/* 标签 */}
              {isSelected && (
                <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-white px-3 py-1 rounded-lg shadow-md whitespace-nowrap">
                  <div className="text-sm font-medium">{marker.name}</div>
                  <div className="text-xs text-slate-500">
                    {marker.type === 'delivery' && formatStatus(marker.status)}
                  </div>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* 模拟实时路线 */}
      {deliveries.filter(d => d.status === 'IN_TRANSIT').length > 0 && (
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          <path
            d="M 50 50 Q 70 30, 85 20 T 95 25"
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            strokeDasharray="5,5"
          >
            <animate
              attributeName="stroke-dashoffset"
              values="0;10"
              dur="1s"
              repeatCount="indefinite"
            />
          </path>
        </svg>
      )}
    </div>
  );
};

/**
 * 车辆信息面板
 */
const VehicleInfo = ({ vehicle }) => {
  if (!vehicle) return null;

  return (
    <Card className="border-blue-200 bg-blue-50/30">
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Truck className="w-5 h-5 text-blue-600" />
          车辆信息
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-slate-500">车牌号</div>
            <div className="font-medium">{vehicle.license_plate}</div>
          </div>
          <div>
            <div className="text-sm text-slate-500">车辆类型</div>
            <div className="font-medium">{vehicle.vehicle_type}</div>
          </div>
          <div>
            <div className="text-sm text-slate-500">载重</div>
            <div className="font-medium">{vehicle.capacity} kg</div>
          </div>
          <div>
            <div className="text-sm text-slate-500">状态</div>
            <Badge className={vehicle.status === 'active' ? 'bg-green-500' : 'bg-gray-500'}>
              {vehicle.status === 'active' ? '行驶中' : '空闲'}
            </Badge>
          </div>
        </div>
        <div>
          <div className="text-sm text-slate-500 mb-1">当前位置</div>
          <div className="text-sm font-medium">{vehicle.current_location}</div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * 实时追踪地图组件
 *
 * @param {Object} props
 * @param {Array} props.deliveries - 配送任务列表
 * @param {Object} props.selectedDelivery - 选中的配送任务
 * @param {Function} props.onLocationSelect - 位置选择回调
 * @param {Object} props.vehicle - 当前车辆信息
 * @param {Function} props.onContactDriver - 联系司机回调
 */
export const TrackingMap = ({
  deliveries = [],
  selectedDelivery,
  onLocationSelect,
  vehicle,
  onContactDriver
}) => {
  const [selectedVehicle, setSelectedVehicle] = useState(vehicle);
  const [isRealtime, setIsRealtime] = useState(true);

  // 过滤在途配送
  const inTransitDeliveries = deliveries.filter(d => d.status === 'IN_TRANSIT');
  const allDeliveries = isRealtime ? inTransitDeliveries : deliveries;

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 追踪模式切换 */}
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <Button
            variant={isRealtime ? "default" : "outline"}
            onClick={() => setIsRealtime(true)}
          >
            实时追踪
            {inTransitDeliveries.length > 0 && (
              <Badge className="ml-2 bg-orange-500">
                {inTransitDeliveries.length}
              </Badge>
            )}
          </Button>
          <Button
            variant={!isRealtime ? "default" : "outline"}
            onClick={() => setIsRealtime(false)}
          >
            全部配送
            {deliveries.length > 0 && (
              <Badge className="ml-2 bg-blue-500">
                {deliveries.length}
              </Badge>
            )}
          </Button>
        </div>

        {selectedDelivery && (
          <Button
            variant="outline"
            onClick={() => onContactDriver?.(selectedDelivery)}
          >
            <Phone className="w-4 h-4 mr-2" />
            联系司机
          </Button>
        )}
      </div>

      {/* 地图组件 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Navigation className="w-5 h-5 text-blue-600" />
            配送追踪地图
          </CardTitle>
        </CardHeader>
        <CardContent>
          <MapComponent
            deliveries={allDeliveries}
            selectedDelivery={selectedDelivery}
            onLocationSelect={onLocationSelect}
          />
        </CardContent>
      </Card>

      {/* 车辆信息 */}
      {selectedVehicle && (
        <VehicleInfo vehicle={selectedVehicle} />
      )}

      {/* 追踪提示 */}
      {inTransitDeliveries.length === 0 && deliveries.length > 0 && (
        <Card>
          <CardContent className="py-6 text-center">
            <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
            <p className="text-slate-500 mb-2">暂无在途配送</p>
            <p className="text-sm text-slate-400">
              选择"全部配送"查看所有配送任务
            </p>
          </CardContent>
        </Card>
      )}

      {deliveries.length === 0 && (
        <Card>
          <CardContent className="py-6 text-center">
            <MapPin className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-500 mb-2">暂无配送任务</p>
            <p className="text-sm text-slate-400">
              请先创建配送任务
            </p>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
};

export default TrackingMap;