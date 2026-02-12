/**
 * Delivery Tracking
 * 物流跟踪组件：展示已发货/在途订单的跟踪信息（简化版）
 */

import { Card, Empty, List, Space, Tag, Typography } from "antd";
import { MapPin, Truck, PackageSearch } from "lucide-react";

import { DELIVERY_STATUS, SHIPPING_METHODS } from "@/lib/constants/service";

const { Text } = Typography;

const getConfigByValue = (configs, value, fallbackLabel = "-") => {
  const match = Object.values(configs).find((item) => item.value === value);
  if (match) {return match;}
  return { label: fallbackLabel, color: "#8c8c8c" };
};

const DeliveryTracking = ({ deliveries = [], loading }) => {
  const trackingDeliveries = deliveries.filter(
    (d) => d.status === DELIVERY_STATUS.SHIPPED.value || d.status === DELIVERY_STATUS.IN_TRANSIT.value
  );

  return (
    <Card
      loading={loading}
      title={
        <Space>
          <Truck size={16} />
          物流跟踪
        </Space>
      }
    >
      {trackingDeliveries.length === 0 ? (
        <Empty description="暂无可跟踪的发货单（已发货/在途）" />
      ) : (
        <List
          itemLayout="vertical"
          dataSource={trackingDeliveries}
          renderItem={(item) => {
            const status = getConfigByValue(DELIVERY_STATUS, item.status, item.status);
            const method = getConfigByValue(SHIPPING_METHODS, item.shippingMethod, item.shippingMethod);
            const hasTracking = Boolean(item.trackingNumber);

            return (
              <List.Item
                key={item.id ?? item.orderNumber}
                extra={
                  <Space direction="vertical" align="end">
                    <Tag color={status.color}>{status.label}</Tag>
                    <Tag>{method.label}</Tag>
                  </Space>
                }
              >
                <Space direction="vertical" size={6} style={{ width: "100%" }}>
                  <Text strong>{item.orderNumber}</Text>
                  <Text type="secondary">{item.customerName}</Text>

                  <Space wrap>
                    <Tag icon={<MapPin size={14} />}>{item.deliveryAddress || "地址未知"}</Tag>
                    {item.scheduledDate && <Tag>计划 {item.scheduledDate}</Tag>}
                    {item.actualDate && <Tag>发货 {item.actualDate}</Tag>}
                  </Space>

                  <Space wrap>
                    {hasTracking ? (
                      <Tag icon={<PackageSearch size={14} />} color="blue">
                        运单号：{item.trackingNumber}
                      </Tag>
                    ) : (
                      <Tag color="default">暂无运单号</Tag>
                    )}
                    {item.notes && (
                      <Text type="secondary" style={{ display: "block" }}>
                        备注：{item.notes}
                      </Text>
                    )}
                  </Space>
                </Space>
              </List.Item>
            );
          }}
        />
      )}
    </Card>
  );
};

export default DeliveryTracking;

