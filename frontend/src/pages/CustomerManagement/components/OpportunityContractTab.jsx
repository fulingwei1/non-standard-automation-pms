/**
 * OpportunityContractTab - 商机合同Tab
 * 展示活跃商机列表和合同管理
 */

import { Card, Table, Tag, Progress, Typography, Space, Button } from "antd";
import { FileText, DollarSign, Calendar, TrendingUp, Eye } from "lucide-react";

const { Text } = Typography;

const OpportunityContractTab = ({ customer, loading }) => {
  if (!customer && !loading) {
    return (
      <div style={{ textAlign: "center", padding: "40px" }}>
        <Text type="secondary">暂无商机合同数据</Text>
      </div>
    );
  }

  // 商机阶段配置
  const stageConfig = {
    lead: { label: "潜在客户", color: "default", percent: 20 },
    qualified: { label: "已验证", color: "processing", percent: 40 },
    proposal: { label: "方案提交", color: "cyan", percent: 60 },
    negotiation: { label: "商务谈判", color: "warning", percent: 80 },
    closed_won: { label: "已成交", color: "success", percent: 100 },
    closed_lost: { label: "已丢失", color: "error", percent: 0 },
  };

  // 合同状态配置
  const contractStatusConfig = {
    draft: { label: "草稿", color: "default" },
    pending: { label: "待审批", color: "processing" },
    active: { label: "执行中", color: "success" },
    completed: { label: "已完成", color: "cyan" },
    terminated: { label: "已终止", color: "error" },
  };

  // 商机列表列定义
  const opportunityColumns = [
    {
      title: "商机名称",
      dataIndex: "name",
      key: "name",
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: "金额",
      dataIndex: "amount",
      key: "amount",
      render: (amount) => (
        <Space>
          <DollarSign size={14} />
          <Text>¥{amount?.toLocaleString() || 0}</Text>
        </Space>
      ),
    },
    {
      title: "阶段",
      dataIndex: "stage",
      key: "stage",
      render: (stage) => {
        const config = stageConfig[stage] || stageConfig.lead;
        return (
          <div>
            <Tag color={config.color}>{config.label}</Tag>
            <Progress
              percent={config.percent}
              size="small"
              showInfo={false}
              strokeColor={
                config.color === "success"
                  ? "#52c41a"
                  : config.color === "error"
                  ? "#ff4d4f"
                  : "#1890ff"
              }
            />
          </div>
        );
      },
    },
    {
      title: "预计成交日期",
      dataIndex: "expected_close_date",
      key: "expected_close_date",
      render: (date) => (
        <Space>
          <Calendar size={14} />
          {date ? new Date(date).toLocaleDateString("zh-CN") : "-"}
        </Space>
      ),
    },
    {
      title: "赢单概率",
      dataIndex: "win_probability",
      key: "win_probability",
      render: (probability) => (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Progress
            type="circle"
            percent={probability || 0}
            width={40}
            strokeColor="#52c41a"
          />
        </div>
      ),
    },
    {
      title: "操作",
      key: "action",
      render: (_, record) => (
        <Button size="small" icon={<Eye size={14} />}>
          查看详情
        </Button>
      ),
    },
  ];

  // 合同列表列定义
  const contractColumns = [
    {
      title: "合同编号",
      dataIndex: "contract_number",
      key: "contract_number",
      render: (text) => <Text code>{text}</Text>,
    },
    {
      title: "合同名称",
      dataIndex: "name",
      key: "name",
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: "合同金额",
      dataIndex: "amount",
      key: "amount",
      render: (amount) => (
        <Space>
          <DollarSign size={14} />
          <Text>¥{amount?.toLocaleString() || 0}</Text>
        </Space>
      ),
    },
    {
      title: "签订日期",
      dataIndex: "signed_date",
      key: "signed_date",
      render: (date) => (date ? new Date(date).toLocaleDateString("zh-CN") : "-"),
    },
    {
      title: "到期日期",
      dataIndex: "end_date",
      key: "end_date",
      render: (date) => (date ? new Date(date).toLocaleDateString("zh-CN") : "-"),
    },
    {
      title: "状态",
      dataIndex: "status",
      key: "status",
      render: (status) => {
        const config = contractStatusConfig[status] || contractStatusConfig.draft;
        return <Tag color={config.color}>{config.label}</Tag>;
      },
    },
    {
      title: "操作",
      key: "action",
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<Eye size={14} />}>
            查看
          </Button>
          <Button size="small" icon={<FileText size={14} />}>
            下载
          </Button>
        </Space>
      ),
    },
  ];

  // 模拟数据（实际应从API获取）
  const opportunities = customer?.opportunities || [
    {
      id: 1,
      name: "智能制造系统升级项目",
      amount: 1500000,
      stage: "proposal",
      expected_close_date: "2026-05-15",
      win_probability: 75,
    },
    {
      id: 2,
      name: "数字化转型咨询服务",
      amount: 800000,
      stage: "negotiation",
      expected_close_date: "2026-04-20",
      win_probability: 85,
    },
  ];

  const contracts = customer?.contracts || [
    {
      id: 1,
      contract_number: "CT-2026-001",
      name: "年度技术服务合同",
      amount: 2000000,
      signed_date: "2026-01-10",
      end_date: "2027-01-10",
      status: "active",
    },
    {
      id: 2,
      contract_number: "CT-2025-089",
      name: "系统集成项目合同",
      amount: 1200000,
      signed_date: "2025-11-15",
      end_date: "2026-03-15",
      status: "completed",
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      {/* 商机概览 */}
      <Card
        loading={loading}
        title={
          <Space>
            <TrendingUp size={18} />
            <span>活跃商机</span>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Table
          columns={opportunityColumns}
          dataSource={opportunities}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 个商机`,
          }}
          locale={{
            emptyText: "暂无商机数据",
          }}
        />
      </Card>

      {/* 合同管理 */}
      <Card
        loading={loading}
        title={
          <Space>
            <FileText size={18} />
            <span>合同管理</span>
          </Space>
        }
      >
        <Table
          columns={contractColumns}
          dataSource={contracts}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 份合同`,
          }}
          locale={{
            emptyText: "暂无合同数据",
          }}
        />
      </Card>
    </div>
  );
};

export default OpportunityContractTab;
