/**
 * Approval List Component
 * 审批列表组件：用于“我的审批/我提交的”等列表页
 */

import { Typography } from "antd";

import { APPROVAL_TYPES, APPROVAL_STATUS, APPROVAL_PRIORITY, TABLE_CONFIG } from "@/lib/constants/approval";

const { Text } = Typography;

const getConfigByValue = (configs, value, fallbackLabel = "-") => {
  const match = Object.values(configs).find((item) => item.value === value);
  if (match) {return match;}
  return { label: fallbackLabel, color: "#8c8c8c", icon: "📄" };
};

const ApprovalList = ({ approvals = [], loading }) => {
  const columns = [
    {
      title: "标题",
      dataIndex: "title",
      key: "title",
      width: 280,
      render: (value) => <Text strong>{value}</Text>,
      ellipsis: true
    },
    {
      title: "类型",
      dataIndex: "type",
      key: "type",
      width: 140,
      render: (value) => {
        const cfg = getConfigByValue(APPROVAL_TYPES, value, value);
        return (
          <Tag color={cfg.color}>
            {cfg.icon} {cfg.label}
          </Tag>
        );
      }
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (value) => {
        const cfg = getConfigByValue(APPROVAL_STATUS, value, value);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      }
    },
    {
      title: "优先级",
      dataIndex: "priority",
      key: "priority",
      width: 100,
      render: (value) => {
        const cfg = getConfigByValue(APPROVAL_PRIORITY, value, value);
        return <Tag color={cfg.color}>{cfg.label}</Tag>;
      }
    },
    {
      title: "金额",
      dataIndex: "amount",
      key: "amount",
      width: 120,
      render: (value) => (value != null ? `¥${Number(value).toLocaleString()}` : "-")
    },
    { title: "发起人", dataIndex: "initiator", key: "initiator", width: 120, ellipsis: true },
    { title: "审批人", dataIndex: "approver", key: "approver", width: 120, ellipsis: true },
    { title: "创建时间", dataIndex: "createdAt", key: "createdAt", width: 170 },
    { title: "截止时间", dataIndex: "deadline", key: "deadline", width: 170 }
  ];

  return (
    <Card
      title={
        <Space>
          <ClipboardCheck size={16} />
          审批列表
        </Space>
      }
    >
      <Table
        rowKey={(row) => row.id ?? row.title}
        loading={loading}
        columns={columns}
        dataSource={approvals}
        pagination={TABLE_CONFIG.pagination}
        scroll={TABLE_CONFIG.scroll}
        size={TABLE_CONFIG.size}
      />
    </Card>
  );
};

export default ApprovalList;

