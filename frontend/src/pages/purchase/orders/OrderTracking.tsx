/**
 * 订单跟踪页
 * @page OrderTracking
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Package, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { useToast } from '../../../hooks/use-toast';
import purchaseService from '../../../services/purchase/purchaseService';
import type { OrderTrackingEvent } from '../../../types/purchase';
import TrackingTimeline from './components/TrackingTimeline';

const OrderTracking: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const { toast } = useToast();
  const [events, setEvents] = useState<OrderTrackingEvent[]>([]);
  const [loading, setLoading] = useState(false);

  const loadTracking = async () => {
    if (!orderId) return;

    setLoading(true);
    try {
      const data = await purchaseService.getOrderTracking(parseInt(orderId));
      setEvents(data);
    } catch (error: any) {
      toast({
        title: '加载失败',
        description: error.response?.data?.detail || '无法加载订单跟踪',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTracking();
  }, [orderId]);

  const handleReceive = async () => {
    if (!orderId) return;

    if (!confirm('确认收货吗？')) return;

    try {
      await purchaseService.receiveOrder(parseInt(orderId), {
        receipt_date: new Date().toISOString().split('T')[0],
        items: [], // 需要实际的订单明细
      });

      toast({
        title: '收货成功',
        description: '订单已确认收货',
      });

      loadTracking();
    } catch (error: any) {
      toast({
        title: '收货失败',
        description: error.response?.data?.detail || '无法确认收货',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl font-bold flex items-center gap-2">
              <Package className="h-6 w-6" />
              订单跟踪
            </CardTitle>
            <div className="flex gap-2">
              <Button onClick={handleReceive} disabled={loading}>
                确认收货
              </Button>
              <Button onClick={loadTracking} disabled={loading} variant="outline">
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {loading && events.length === 0 ? (
            <div className="text-center py-12">
              <RefreshCw className="animate-spin h-8 w-8 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-500">加载中...</p>
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">暂无跟踪记录</p>
            </div>
          ) : (
            <TrackingTimeline events={events} />
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default OrderTracking;
