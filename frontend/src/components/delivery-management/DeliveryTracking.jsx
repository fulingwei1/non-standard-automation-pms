/**
 * Delivery Tracking
 * 物流跟踪组件：展示已发货/在途订单的跟踪信息（简化版）
 * Refactored to shadcn/Tailwind Dark Theme
 */

import { Card, CardContent, CardHeader, CardTitle, Badge, EmptyState } from "../ui";
import { MapPin, Truck, PackageSearch } from "lucide-react";

import { DELIVERY_STATUS, SHIPPING_METHODS } from "@/lib/constants/service";

const getConfigByValue = (configs, value, fallbackLabel = "-") => {
  const match = Object.values(configs).find((item) => item.value === value);
  if (match) {return match;}
  return { label: fallbackLabel, color: "#8c8c8c" };
};

const DeliveryTracking = ({ deliveries = [], loading }) => {
  const trackingDeliveries = (deliveries || []).filter(
    (d) => d.status === DELIVERY_STATUS.SHIPPED.value || d.status === DELIVERY_STATUS.IN_TRANSIT.value
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <Card className="bg-surface-100/50">
      <CardHeader className="border-b border-white/10 pb-4">
        <CardTitle className="text-white flex items-center gap-2">
          <Truck size={18} />
          物流跟踪
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        {trackingDeliveries.length === 0 ? (
          <EmptyState 
            icon={Truck}
            title="暂无可跟踪的发货单"
            message="当前没有已发货或在途的订单"
          />
        ) : (
          <div className="space-y-3">
            {trackingDeliveries.map((item) => {
              const status = getConfigByValue(DELIVERY_STATUS, item.status, item.status);
              const method = getConfigByValue(SHIPPING_METHODS, item.shippingMethod, item.shippingMethod);
              const hasTracking = Boolean(item.trackingNumber);

              return (
                <div
                  key={item.id ?? item.orderNumber}
                  className="p-4 bg-surface-100 rounded-lg border border-white/5"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-3">
                      <div>
                        <p className="font-medium text-white">{item.orderNumber}</p>
                        <p className="text-sm text-slate-400">{item.customerName}</p>
                      </div>

                      <div className="flex flex-wrap gap-2">
                        <Badge 
                          variant="outline" 
                          className="flex items-center gap-1 border-slate-500/30 text-slate-400"
                        >
                          <MapPin size={14} />
                          {item.deliveryAddress || "地址未知"}
                        </Badge>
                        {item.scheduledDate && (
                          <Badge variant="outline" className="border-slate-500/30 text-slate-400">
                            计划 {item.scheduledDate}
                          </Badge>
                        )}
                        {item.actualDate && (
                          <Badge variant="outline" className="border-slate-500/30 text-slate-400">
                            发货 {item.actualDate}
                          </Badge>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {hasTracking ? (
                          <Badge 
                            variant="outline" 
                            className="flex items-center gap-1 bg-blue-500/20 text-blue-400 border-blue-500/30"
                          >
                            <PackageSearch size={14} />
                            运单号：{item.trackingNumber}
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="border-slate-500/30 text-slate-400">
                            暂无运单号
                          </Badge>
                        )}
                        {item.notes && (
                          <p className="text-xs text-slate-500 w-full">
                            备注：{item.notes}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1">
                      <Badge 
                        variant="outline"
                        style={{ borderColor: status.color, color: status.color }}
                      >
                        {status.label}
                      </Badge>
                      <Badge variant="outline" className="border-slate-500/30 text-slate-400">
                        {method.label}
                      </Badge>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default DeliveryTracking;
