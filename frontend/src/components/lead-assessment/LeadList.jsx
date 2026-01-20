/**
 * Lead List Component
 * 线索列表组件：用于展示线索列表、操作入口
 */

import { Card, Space, Table, Tag, Typography, Button } from "antd";
import { Eye, Edit, Trash2, Target } from "lucide-react";

import { LEAD_SOURCES, LEAD_STATUS, QUALIFICATION_LEVELS, TABLE_CONFIG } from "./leadAssessmentConstants";

const { Text } = Typography;

const getConfigByValue = (configs, value, fallbackLabel = "-") => {
  const match = Object.values(configs).find((item) => item.value === value);
  if (match) {return match;}
  return { label: fallbackLabel, color: "#8c8c8c" };
};

const LeadList = ({ leads = [], loading, onEdit, onDelete, onAssess, onConvert }) => {
  const columns = [
    {
      title: "公司",
      dataIndex: "companyName",
      key: "companyName",
      width: 220,
      render: (value) => <Text strong>{value}</Text>,
      ellipsis: true
    },
    { title: "联系人", dataIndex: "contactPerson", key: "contactPerson", width: 120, ellipsis: true },
    { title: "职位", dataIndex: "position", key: "position", width: 120, ellipsis: true },
    { title: "电话", dataIndex: "phone", key: "phone", width: 140 },
    {
      title: "来源",
      dataIndex: "source",
      key: "source",
      width: 120,
      render: (value) => {
        const cfg = getConfigByValue(LEAD_SOURCES, value, value);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      }
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 110,
      render: (value) => {
        const cfg = getConfigByValue(LEAD_STATUS, value, value);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      }
    },
    {
      title: "线索等级",
      dataIndex: "qualification",
      key: "qualification",
      width: 110,
      render: (value) => {
        const cfg = getConfigByValue(QUALIFICATION_LEVELS, value, value);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      }
    },
    {
      title: "评分",
      dataIndex: "score",
      key: "score",
      width: 90,
      render: (value) => (value ?? "-")
    },
    { title: "创建日期", dataIndex: "createdAt", key: "createdAt", width: 120 },
    {
      title: "操作",
      key: "actions",
      fixed: "right",
      width: 240,
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<Eye size={16} />} onClick={() => onAssess?.(record)}>
            查看/评估
          </Button>
          <Button type="link" icon={<Edit size={16} />} onClick={() => onEdit?.(record)}>
            编辑
          </Button>
          <Button type="link" icon={<Target size={16} />} onClick={() => onConvert?.(record)}>
            转化
          </Button>
          <Button danger type="link" icon={<Trash2 size={16} />} onClick={() => onDelete?.(record.id)}>
            删除
          </Button>
        </Space>
      )
    }
  ];

  return (
    <Card title="线索列表">
      <Table
        rowKey={(row) => row.id ?? row.companyName}
        loading={loading}
        columns={columns}
        dataSource={leads}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default LeadList;

