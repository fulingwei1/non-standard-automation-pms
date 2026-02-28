/**
 * Delivery Plan
 * 交付计划组件：以表格形式展示待发货/准备中等计划类任务
 */

import { Card, Space, Table, Tag, Typography } from "antd";
import { Calendar, Package, Truck } from "lucide-react";

import { DELIVERY_STATUS, DELIVERY_PRIORITY, SHIPPING_METHODS, PACKAGE_TYPES } from "@/lib/constants/service";

const { Text } = Typography;

const getConfigByValue = (configs, value, fallbackLabel = "-") => {
  const match = Object.values(configs).find((item) => item.value === value);
  if (match) {return match;}
  return { label: fallbackLabel, color: "#8c8c8c" };
};

const DeliveryPlan = ({ deliveries = [], loading }) => {
  const columns = [
    {
      title: "订单号",
      dataIndex: "orderNumber",
      key: "orderNumber",
      width: 160,
      render: (value) => <Text strong>{value}</Text>
    },
    {
      title: "客户",
      dataIndex: "customerName",
      key: "customerName",
      width: 220,
      ellipsis: true
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (value) => {
        const cfg = getConfigByValue(DELIVERY_STATUS, value, value);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      }
    },
    {
      title: "优先级",
      dataIndex: "priority",
      key: "priority",
      width: 100,
      render: (value) => {
        const cfg = getConfigByValue(DELIVERY_PRIORITY, value, value);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      }
    },
    {
      title: "运输方式",
      dataIndex: "shippingMethod",
      key: "shippingMethod",
      width: 130,
      render: (value) => {
        const cfg = getConfigByValue(SHIPPING_METHODS, value, value);
        return <span>{cfg.label}</span>;
      }
    },
    {
      title: "包装类型",
      dataIndex: "packageType",
      key: "packageType",
      width: 130,
      render: (value) => {
        const cfg = getConfigByValue(PACKAGE_TYPES, value, value);
        return <span>{cfg.label}</span>;
      }
    },
    {
      title: "计划日期",
      dataIndex: "scheduledDate",
      key: "scheduledDate",
      width: 120,
      render: (value) => value || "-"
    },
    {
      title: "件数",
      dataIndex: "itemCount",
      key: "itemCount",
      width: 80,
      render: (value) => (value ?? "-")
    },
    {
      title: "重量(kg)",
      dataIndex: "totalWeight",
      key: "totalWeight",
      width: 100,
      render: (value) => (value ?? "-")
    }
  ];

  return (
    <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Card
        title={
          <Space>
            <Calendar size={16} />
            交付计划
          </Space>
        }
        extra={
          <Space>
            <Tag icon={<Package size={14} />} color="gold">
              待发货/准备中：{deliveries.length}
            </Tag>
            <Tag icon={<Truck size={14} />} color="cyan">
              已发货/在途：{deliveries.filter((d) => d.status === "shipped" || d.status === "in_transit").length}
            </Tag>
          </Space>
        }
      >
        <Table
          rowKey={(row) => row.id ?? row.orderNumber}
          loading={loading}
          columns={columns}
          dataSource={deliveries}
          pagination={{ pageSize: 10, showSizeChanger: true }}
          scroll={{ x: 1100 }}
        />
      </Card>
    </Space>
  );
};

export default DeliveryPlan;

