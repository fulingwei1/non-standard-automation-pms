/**
 * Delivery Overview
 * 交付概览组件：用于展示交付总体统计与关键提醒
 */

import { Card, Col, Row, Space, Statistic, Tag, Typography, Progress, Empty } from "antd";
import { PackageCheck, Truck, Clock, AlertCircle } from "lucide-react";

import { DELIVERY_STATUS, DELIVERY_PRIORITY, SHIPPING_METHODS } from "@/lib/constants/service";

const { Title, Text } = Typography;

const getConfigByValue = (configs, value, fallbackLabel = "-") => {
  const match = Object.values(configs).find((item) => item.value === value);
  if (match) {return match;}
  return { label: fallbackLabel, color: "#8c8c8c" };
};

const countBy = (items, predicate) => (items || []).reduce((acc, item) => acc + (predicate(item) ? 1 : 0), 0);

const DeliveryOverview = ({ data, loading }) => {
  const deliveries = Array.isArray(data) ? data : data?.deliveries || [];

  const total = deliveries?.length;
  const preparingCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.PREPARING.value);
  const pendingCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.PENDING.value);
  const inTransitCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.IN_TRANSIT.value);
  const deliveredCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.DELIVERED.value);
  const cancelledCount = countBy(deliveries, (d) => d.status === DELIVERY_STATUS.CANCELLED.value);

  const urgentCount = countBy(deliveries, (d) => d.priority === DELIVERY_PRIORITY.URGENT.value);
  const highPriorityCount = countBy(deliveries, (d) => d.priority === DELIVERY_PRIORITY.HIGH.value);

  const shippedOrInTransit = (deliveries || []).filter(
    (d) => d.status === DELIVERY_STATUS.SHIPPED.value || d.status === DELIVERY_STATUS.IN_TRANSIT.value
  );

  const completionRate = total > 0 ? Math.round((deliveredCount / total) * 100) : 0;

  return (
    <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="总发货单" value={total} prefix={<PackageCheck size={18} />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="待处理（待发货/准备中）" value={pendingCount + preparingCount} prefix={<Clock size={18} />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="在途/已发货" value={shippedOrInTransit.length} prefix={<Truck size={18} />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic title="已送达" value={deliveredCount} />
          </Card>
        </Col>
      </Row>

      <Card loading={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Title level={5} style={{ marginTop: 0 }}>
              完成率
            </Title>
            <Progress percent={completionRate} status={completionRate >= 80 ? "success" : "active"} />
            <Text type="secondary">
              已送达 {deliveredCount} / {total}（取消 {cancelledCount}）
            </Text>
          </Col>
          <Col xs={24} md={12}>
            <Title level={5} style={{ marginTop: 0 }}>
              风险提醒
            </Title>
            <Space wrap>
              <Tag color={urgentCount > 0 ? "red" : "default"}>
                <AlertCircle size={14} style={{ marginRight: 6 }} />
                紧急 {urgentCount}
              </Tag>
              <Tag color={highPriorityCount > 0 ? "orange" : "default"}>高优先级 {highPriorityCount}</Tag>
              <Tag>在途 {inTransitCount}</Tag>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card loading={loading} title="在途/已发货清单（最近）">
        {shippedOrInTransit.length === 0 ? (
          <Empty description="暂无在途/已发货数据" />
        ) : (
          <Space orientation="vertical" size={8} style={{ width: "100%" }}>
            {shippedOrInTransit.slice(0, 8).map((d) => {
              const status = getConfigByValue(DELIVERY_STATUS, d.status, d.status);
              const method = getConfigByValue(SHIPPING_METHODS, d.shippingMethod, d.shippingMethod);
              const priority = getConfigByValue(DELIVERY_PRIORITY, d.priority, d.priority);

              return (
                <Card key={d.id} size="small" style={{ background: "#fafafa" }}>
                  <Row gutter={[12, 12]} align="middle">
                    <Col xs={24} md={10}>
                      <Text strong>{d.orderNumber}</Text>
                      <div>
                        <Text type="secondary">{d.customerName}</Text>
                      </div>
                    </Col>
                    <Col xs={24} md={14}>
                      <Space wrap>
                        <Tag color={status.color}>{status.label}</Tag>
                        <Tag color={priority.color}>{priority.label}</Tag>
                        <Tag>{method.label}</Tag>
                        {d.scheduledDate && <Tag>计划 {d.scheduledDate}</Tag>}
                        {d.trackingNumber && <Tag>单号 {d.trackingNumber}</Tag>}
                      </Space>
                    </Col>
                  </Row>
                </Card>
              );
            })}
          </Space>
        )}
      </Card>
    </Space>
  );
};

export default DeliveryOverview;
