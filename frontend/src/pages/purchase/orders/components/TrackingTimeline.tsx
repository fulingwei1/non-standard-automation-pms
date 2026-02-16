/**
 * 订单跟踪时间轴组件
 * @component TrackingTimeline
 */

import React from 'react';
import { CheckCircle, Clock, Package, Truck, XCircle } from 'lucide-react';
import type { OrderTrackingEvent } from '../../../../types/purchase';

interface TrackingTimelineProps {
  events: OrderTrackingEvent[];
}

const EVENT_ICONS = {
  CREATED: <Clock className="h-5 w-5 text-blue-600" />,
  CONFIRMED: <CheckCircle className="h-5 w-5 text-green-600" />,
  SHIPPED: <Truck className="h-5 w-5 text-purple-600" />,
  RECEIVED: <Package className="h-5 w-5 text-green-600" />,
  CANCELLED: <XCircle className="h-5 w-5 text-red-600" />,
};

const TrackingTimeline: React.FC<TrackingTimelineProps> = ({ events }) => {
  return (
    <div className="space-y-4">
      {events.map((event, index) => (
        <div key={event.id} className="flex gap-4">
          {/* 时间轴线 */}
          <div className="flex flex-col items-center">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gray-100 border-2 border-gray-300">
              {EVENT_ICONS[event.event_type]}
            </div>
            {index < events.length - 1 && (
              <div className="w-0.5 h-full bg-gray-300 my-2" />
            )}
          </div>

          {/* 事件内容 */}
          <div className="flex-1 pb-8">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-medium text-lg">{event.event_description}</h4>
                <p className="text-sm text-gray-500 mt-1">
                  {new Date(event.event_time).toLocaleString('zh-CN')}
                </p>
                {event.operator_name && (
                  <p className="text-sm text-gray-500">
                    操作人: {event.operator_name}
                  </p>
                )}
                {event.tracking_no && (
                  <p className="text-sm text-gray-600 mt-2">
                    物流单号: {event.tracking_no}
                    {event.logistics_company && ` (${event.logistics_company})`}
                  </p>
                )}
                {event.estimated_arrival && (
                  <p className="text-sm text-blue-600 mt-1">
                    预计到达: {event.estimated_arrival}
                  </p>
                )}
              </div>
              <div className="text-sm text-gray-500">
                {event.old_status && event.new_status && (
                  <span>
                    {event.old_status} → {event.new_status}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TrackingTimeline;
