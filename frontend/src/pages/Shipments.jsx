/**
 * 出货看板 - Shipments Dashboard
 * 展示发货统计数据（给生产总监看）
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Package,
  Truck,
  Clock,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  BarChart3,
  RefreshCw,
  ArrowRight,
} from "lucide-react";
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Space,
  Button,
  Spin,
  Tag,
  Progress,
  message,
  Empty,
  List,
} from "antd";

import { businessSupportApi } from "../services/api";
import { quoteDeliveryApi } from "../services/api/sales";
import { getItemsCompat } from "../utils/apiResponse";

const { Title, Text } = Typography;

const StatCard = ({ title, value, icon, color, suffix, loading }) => (
  <Card loading={loading} hoverable>
    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          background: `${color}15`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {icon}
      </div>
      <Statistic title={title} value={value} suffix={suffix} />
    </div>
  </Card>
);

export default function Shipments() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [upcomingDeliveries, setUpcomingDeliveries] = useState([]);
  const [overdueDeliveries, setOverdueDeliveries] = useState([]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, upcomingRes, overdueRes] = await Promise.allSettled([
        businessSupportApi.deliveryOrders.statistics(),
        quoteDeliveryApi.upcoming({ days: 7 }),
        quoteDeliveryApi.overdue(),
      ]);

      if (statsRes.status === "fulfilled") {
        const data = statsRes.value?.data?.data || statsRes.value?.data || {};
        setStats(data);
      }

      if (upcomingRes.status === "fulfilled") {
        const data = upcomingRes.value?.data?.data || upcomingRes.value?.data || {};
        setUpcomingDeliveries(data.items || []);
      }

      if (overdueRes.status === "fulfilled") {
        const data = overdueRes.value?.data?.data || overdueRes.value?.data || {};
        setOverdueDeliveries(data.items || []);
      }
    } catch (_err) {
      message.error("加载出货数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      style={{ padding: 24, background: "#f5f5f5", minHeight: "100vh" }}
    >
      {/* 页面头部 */}
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            <BarChart3 className="inline-block mr-2" size={28} />
            出货看板
          </Title>
          <Text type="secondary">发货统计总览 — 生产总监视图</Text>
        </div>
        <Space>
          <Button icon={<RefreshCw size={16} />} onClick={loadData} loading={loading}>
            刷新
          </Button>
          <Button type="primary" onClick={() => navigate("/pmc/delivery-orders")}>
            发货管理
            <ArrowRight size={14} />
          </Button>
        </Space>
      </div>

      {/* 核心统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <StatCard
            title="待发货"
            value={stats?.pending_shipments ?? "-"}
            icon={<Clock size={24} color="#fa8c16" />}
            color="#fa8c16"
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard
            title="今日已发"
            value={stats?.shipped_today ?? "-"}
            icon={<Truck size={24} color="#1890ff" />}
            color="#1890ff"
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard
            title="在途订单"
            value={stats?.in_transit ?? "-"}
            icon={<Package size={24} color="#722ed1" />}
            color="#722ed1"
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} md={6}>
          <StatCard
            title="本周已送达"
            value={stats?.delivered_this_week ?? "-"}
            icon={<CheckCircle2 size={24} color="#52c41a" />}
            color="#52c41a"
            loading={loading}
          />
        </Col>
      </Row>

      {/* 效率指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={8}>
          <Card loading={loading} title="准时发货率">
            <div style={{ textAlign: "center" }}>
              <Progress
                type="dashboard"
                percent={stats?.on_time_shipping_rate ? Math.round(stats.on_time_shipping_rate) : 0}
                status={
                  (stats?.on_time_shipping_rate || 0) >= 90
                    ? "success"
                    : (stats?.on_time_shipping_rate || 0) >= 70
                    ? "normal"
                    : "exception"
                }
                format={(percent) => `${percent}%`}
              />
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">计划发货 vs 实际发货</Text>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading} title="平均发货时间">
            <div style={{ textAlign: "center", padding: "20px 0" }}>
              <Statistic
                value={stats?.avg_shipping_time ? stats.avg_shipping_time.toFixed(1) : "-"}
                suffix="天"
                prefix={<TrendingUp size={20} />}
              />
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">从发货到签收平均耗时</Text>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading} title="总订单数">
            <div style={{ textAlign: "center", padding: "20px 0" }}>
              <Statistic value={stats?.total_orders ?? "-"} prefix={<Package size={20} />} />
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">累计发货单总数</Text>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 即将交付 & 逾期交付 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <Clock size={16} />
                7天内即将交付
                {upcomingDeliveries.length > 0 && (
                  <Tag color="blue">{upcomingDeliveries.length}</Tag>
                )}
              </Space>
            }
            loading={loading}
          >
            {upcomingDeliveries.length === 0 ? (
              <Empty description="暂无即将交付的报价" />
            ) : (
              <List
                size="small"
                dataSource={upcomingDeliveries.slice(0, 8)}
                renderItem={(item) => (
                  <List.Item
                    extra={
                      <Tag color={item.days_remaining <= 2 ? "orange" : "blue"}>
                        {item.days_remaining}天后
                      </Tag>
                    }
                  >
                    <List.Item.Meta
                      title={item.quote_no || `报价#${item.quote_id}`}
                      description={
                        <Space size={4}>
                          <Text type="secondary">{item.title}</Text>
                          {item.delivery_date && (
                            <Text type="secondary">| {item.delivery_date}</Text>
                          )}
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card
            title={
              <Space>
                <AlertTriangle size={16} color="#ff4d4f" />
                逾期交付
                {overdueDeliveries.length > 0 && (
                  <Tag color="red">{overdueDeliveries.length}</Tag>
                )}
              </Space>
            }
            loading={loading}
          >
            {overdueDeliveries.length === 0 ? (
              <Empty description="暂无逾期交付" />
            ) : (
              <List
                size="small"
                dataSource={overdueDeliveries.slice(0, 8)}
                renderItem={(item) => (
                  <List.Item
                    extra={
                      <Tag color="red">逾期{item.days_overdue}天</Tag>
                    }
                  >
                    <List.Item.Meta
                      title={item.quote_no || `报价#${item.quote_id}`}
                      description={
                        <Space size={4}>
                          <Text type="secondary">{item.title}</Text>
                          {item.delivery_date && (
                            <Text type="secondary">| {item.delivery_date}</Text>
                          )}
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </Col>
      </Row>
    </motion.div>
  );
}
