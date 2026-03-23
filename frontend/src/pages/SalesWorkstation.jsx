/**
 * 销售工作站
 *
 * 整合 P0/P1 核心功能：
 * - 智能跟进提醒
 * - 催款优先级排序
 * - 商机健康度评分
 * - 合同里程碑提醒
 */

import {
  Typography,
} from "antd";


import {
  useSalesWorkstationData,
  useFollowUpReminders,
  useCollectionPriority,
  useOpportunityHealthList,
  useContractMilestones,
} from "../hooks/useSalesWorkstation";

const { Title, Text } = Typography;

// 紧急程度颜色映射
const urgencyColors = {
  overdue: "red",
  urgent: "orange",
  warning: "gold",
  upcoming: "blue",
  normal: "green",
};

// 紧急程度文本映射
const urgencyLabels = {
  overdue: "已过期",
  urgent: "紧急",
  warning: "预警",
  upcoming: "即将到来",
  normal: "正常",
};

// 健康度颜色映射
const healthColors = {
  excellent: "green",
  good: "blue",
  warning: "gold",
  critical: "red",
};

// 健康度文本映射
const healthLabels = {
  excellent: "优秀",
  good: "良好",
  warning: "警告",
  critical: "危险",
};

/**
 * 统计卡片组件
 */
function SummaryCards({ data, loading }) {
  if (loading) {
    return (
      <Row gutter={[16, 16]}>
        {[1, 2, 3, 4].map((i) => (
          <Col xs={24} sm={12} lg={6} key={i}>
            <Card loading={true} />
          </Col>
        ))}
      </Row>
    );
  }

  const { followUpSummary, collectionSummary, healthSummary, milestoneSummary } = data;

  return (
    <Row gutter={[16, 16]}>
      {/* 跟进提醒 */}
      <Col xs={24} sm={12} lg={6}>
        <Card
          hoverable
          style={{ borderTop: "3px solid #1890ff" }}
        >
          <Statistic
            title={
              <Space>
                <BellOutlined style={{ color: "#1890ff" }} />
                <span>待跟进</span>
              </Space>
            }
            value={followUpSummary?.total_count || 0}
            suffix={
              followUpSummary?.by_urgency?.overdue?.count > 0 && (
                <Badge
                  count={followUpSummary.by_urgency.overdue.count}
                  style={{ backgroundColor: "#f5222d" }}
                />
              )
            }
          />
          {followUpSummary?.by_urgency?.overdue?.count > 0 && (
            <Text type="danger" style={{ fontSize: 12 }}>
              {followUpSummary.by_urgency.overdue.count} 项已过期
            </Text>
          )}
        </Card>
      </Col>

      {/* 催款优先级 */}
      <Col xs={24} sm={12} lg={6}>
        <Card
          hoverable
          style={{ borderTop: "3px solid #fa8c16" }}
        >
          <Statistic
            title={
              <Space>
                <DollarOutlined style={{ color: "#fa8c16" }} />
                <span>待催款</span>
              </Space>
            }
            value={collectionSummary?.total_count || 0}
            suffix={
              collectionSummary?.critical_count > 0 && (
                <Badge
                  count={collectionSummary.critical_count}
                  style={{ backgroundColor: "#f5222d" }}
                />
              )
            }
          />
          {collectionSummary?.total_overdue_amount > 0 && (
            <Text type="danger" style={{ fontSize: 12 }}>
              逾期 ¥{(collectionSummary.total_overdue_amount / 10000).toFixed(1)}万
            </Text>
          )}
        </Card>
      </Col>

      {/* 商机健康度 */}
      <Col xs={24} sm={12} lg={6}>
        <Card
          hoverable
          style={{ borderTop: "3px solid #52c41a" }}
        >
          <Statistic
            title={
              <Space>
                <HeartOutlined style={{ color: "#52c41a" }} />
                <span>商机健康</span>
              </Space>
            }
            value={healthSummary?.average_score || 0}
            suffix="分"
            valueStyle={{
              color:
                (healthSummary?.average_score || 0) >= 70
                  ? "#52c41a"
                  : (healthSummary?.average_score || 0) >= 50
                  ? "#faad14"
                  : "#f5222d",
            }}
          />
          {healthSummary?.by_level?.critical?.count > 0 && (
            <Text type="danger" style={{ fontSize: 12 }}>
              {healthSummary.by_level.critical.count} 个需要关注
            </Text>
          )}
        </Card>
      </Col>

      {/* 合同里程碑 */}
      <Col xs={24} sm={12} lg={6}>
        <Card
          hoverable
          style={{ borderTop: "3px solid #722ed1" }}
        >
          <Statistic
            title={
              <Space>
                <CalendarOutlined style={{ color: "#722ed1" }} />
                <span>里程碑</span>
              </Space>
            }
            value={milestoneSummary?.total_count || 0}
            suffix={
              milestoneSummary?.by_urgency?.overdue?.count > 0 && (
                <Badge
                  count={milestoneSummary.by_urgency.overdue.count}
                  style={{ backgroundColor: "#f5222d" }}
                />
              )
            }
          />
          {milestoneSummary?.by_urgency?.urgent?.count > 0 && (
            <Text type="warning" style={{ fontSize: 12 }}>
              {milestoneSummary.by_urgency.urgent.count} 项紧急
            </Text>
          )}
        </Card>
      </Col>
    </Row>
  );
}

/**
 * 跟进提醒列表
 */
function FollowUpList() {
  const { data, loading, error, refetch } = useFollowUpReminders();

  const columns = [
    {
      title: "客户/线索",
      dataIndex: "entity_name",
      key: "entity_name",
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.entity_type === "lead" ? "线索" : "商机"} · {record.entity_code}
          </Text>
        </Space>
      ),
    },
    {
      title: "提醒类型",
      dataIndex: "reminder_type",
      key: "reminder_type",
      render: (type) => {
        const typeMap = {
          overdue: { text: "已过期", color: "red" },
          scheduled: { text: "定期跟进", color: "blue" },
          stage_push: { text: "阶段推进", color: "orange" },
          inactive: { text: "长期未跟进", color: "gold" },
        };
        const config = typeMap[type] || { text: type, color: "default" };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: "紧急程度",
      dataIndex: "urgency",
      key: "urgency",
      render: (urgency) => (
        <Tag color={urgencyColors[urgency]}>{urgencyLabels[urgency]}</Tag>
      ),
    },
    {
      title: "下次跟进",
      dataIndex: "next_follow_date",
      key: "next_follow_date",
      render: (date, record) => (
        <Space direction="vertical" size={0}>
          <Text>{date}</Text>
          <Text type={record.days_overdue > 0 ? "danger" : "secondary"} style={{ fontSize: 12 }}>
            {record.days_overdue > 0
              ? `已逾期 ${record.days_overdue} 天`
              : record.days_until
              ? `还剩 ${record.days_until} 天`
              : ""}
          </Text>
        </Space>
      ),
    },
    {
      title: "建议",
      dataIndex: "suggestion",
      key: "suggestion",
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Text>{text}</Text>
        </Tooltip>
      ),
    },
  ];

  if (error) {
    return <Alert message="加载失败" description={error} type="error" />;
  }

  return (
    <Table
      columns={columns}
      dataSource={data?.items || []}
      loading={loading}
      rowKey={(record) => `${record.entity_type}-${record.entity_id}`}
      pagination={{ pageSize: 10 }}
      size="small"
      locale={{ emptyText: <Empty description="暂无跟进提醒" /> }}
    />
  );
}

/**
 * 催款优先级列表
 */
function CollectionList() {
  const { data, loading, error, refetch } = useCollectionPriority();

  const columns = [
    {
      title: "客户",
      dataIndex: "customer_name",
      key: "customer_name",
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.contract_code}
          </Text>
        </Space>
      ),
    },
    {
      title: "逾期金额",
      dataIndex: "overdue_amount",
      key: "overdue_amount",
      render: (amount) => (
        <Text type="danger">¥{(amount || 0).toLocaleString()}</Text>
      ),
      sorter: (a, b) => (a.overdue_amount || 0) - (b.overdue_amount || 0),
    },
    {
      title: "逾期天数",
      dataIndex: "days_overdue",
      key: "days_overdue",
      render: (days) => (
        <Tag color={days > 30 ? "red" : days > 14 ? "orange" : "gold"}>
          {days} 天
        </Tag>
      ),
      sorter: (a, b) => a.days_overdue - b.days_overdue,
    },
    {
      title: "优先级",
      dataIndex: "priority_level",
      key: "priority_level",
      render: (level) => {
        const levelMap = {
          critical: { text: "紧急", color: "red" },
          high: { text: "高", color: "orange" },
          medium: { text: "中", color: "gold" },
          low: { text: "低", color: "green" },
        };
        const config = levelMap[level] || { text: level, color: "default" };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: "优先级得分",
      dataIndex: "priority_score",
      key: "priority_score",
      render: (score) => (
        <Progress
          percent={score}
          size="small"
          strokeColor={score >= 80 ? "#f5222d" : score >= 60 ? "#fa8c16" : "#52c41a"}
          format={(p) => `${p}`}
        />
      ),
    },
    {
      title: "建议",
      dataIndex: "suggestion",
      key: "suggestion",
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Text>{text}</Text>
        </Tooltip>
      ),
    },
  ];

  if (error) {
    return <Alert message="加载失败" description={error} type="error" />;
  }

  return (
    <Table
      columns={columns}
      dataSource={data?.items || []}
      loading={loading}
      rowKey="invoice_id"
      pagination={{ pageSize: 10 }}
      size="small"
      locale={{ emptyText: <Empty description="暂无待催款项" /> }}
    />
  );
}

/**
 * 商机健康度列表
 */
function HealthList() {
  const { data, loading, error, refetch } = useOpportunityHealthList();

  const columns = [
    {
      title: "商机",
      dataIndex: "opportunity_name",
      key: "opportunity_name",
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.opportunity_code} · {record.customer_name}
          </Text>
        </Space>
      ),
    },
    {
      title: "阶段",
      dataIndex: "stage",
      key: "stage",
    },
    {
      title: "健康度",
      dataIndex: "total_score",
      key: "total_score",
      render: (score, record) => (
        <Space>
          <Progress
            type="circle"
            percent={score}
            width={40}
            strokeColor={healthColors[record.health_level]}
            format={(p) => `${p}`}
          />
          <Tag color={healthColors[record.health_level]}>
            {healthLabels[record.health_level]}
          </Tag>
        </Space>
      ),
      sorter: (a, b) => a.total_score - b.total_score,
    },
    {
      title: "预估金额",
      dataIndex: "est_amount",
      key: "est_amount",
      render: (amount) => <Text>¥{(amount || 0).toLocaleString()}</Text>,
    },
    {
      title: "关键问题",
      dataIndex: "key_issues",
      key: "key_issues",
      render: (issues) =>
        issues && issues.length > 0 ? (
          <Space direction="vertical" size={0}>
            {issues.slice(0, 2).map((issue, idx) => (
              <Text key={idx} type="warning" style={{ fontSize: 12 }}>
                <WarningOutlined /> {issue}
              </Text>
            ))}
          </Space>
        ) : (
          <Text type="success" style={{ fontSize: 12 }}>
            <CheckCircleOutlined /> 暂无问题
          </Text>
        ),
    },
    {
      title: "建议",
      dataIndex: "top_suggestions",
      key: "top_suggestions",
      ellipsis: true,
      render: (suggestions) =>
        suggestions && suggestions.length > 0 ? (
          <Tooltip title={suggestions.join("；")}>
            <Text>{suggestions[0]}</Text>
          </Tooltip>
        ) : null,
    },
  ];

  if (error) {
    return <Alert message="加载失败" description={error} type="error" />;
  }

  return (
    <Table
      columns={columns}
      dataSource={data?.items || []}
      loading={loading}
      rowKey="opportunity_id"
      pagination={{ pageSize: 10 }}
      size="small"
      locale={{ emptyText: <Empty description="暂无商机数据" /> }}
    />
  );
}

/**
 * 合同里程碑列表
 */
function MilestoneList() {
  const { data, loading, error, refetch } = useContractMilestones();

  const columns = [
    {
      title: "合同",
      dataIndex: "contract_name",
      key: "contract_name",
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.contract_code} · {record.customer_name}
          </Text>
        </Space>
      ),
    },
    {
      title: "里程碑",
      dataIndex: "milestone_name",
      key: "milestone_name",
      render: (text, record) => {
        const typeMap = {
          payment: { text: "付款", color: "green" },
          delivery: { text: "交付", color: "blue" },
          warranty: { text: "质保", color: "orange" },
          contract: { text: "合同", color: "purple" },
        };
        const config = typeMap[record.milestone_type] || { text: record.milestone_type, color: "default" };
        return (
          <Space>
            <Tag color={config.color}>{config.text}</Tag>
            <Text>{text}</Text>
          </Space>
        );
      },
    },
    {
      title: "到期日",
      dataIndex: "due_date",
      key: "due_date",
      render: (date, record) => (
        <Space direction="vertical" size={0}>
          <Text>{date}</Text>
          <Text
            type={record.days_until < 0 ? "danger" : record.days_until <= 7 ? "warning" : "secondary"}
            style={{ fontSize: 12 }}
          >
            {record.days_until < 0
              ? `已逾期 ${Math.abs(record.days_until)} 天`
              : `还剩 ${record.days_until} 天`}
          </Text>
        </Space>
      ),
    },
    {
      title: "紧急程度",
      dataIndex: "urgency",
      key: "urgency",
      render: (urgency) => (
        <Tag color={urgencyColors[urgency]}>{urgencyLabels[urgency]}</Tag>
      ),
    },
    {
      title: "金额",
      dataIndex: "amount",
      key: "amount",
      render: (amount) =>
        amount ? <Text>¥{amount.toLocaleString()}</Text> : <Text type="secondary">-</Text>,
    },
    {
      title: "建议",
      dataIndex: "suggestion",
      key: "suggestion",
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Text>{text}</Text>
        </Tooltip>
      ),
    },
  ];

  if (error) {
    return <Alert message="加载失败" description={error} type="error" />;
  }

  return (
    <Table
      columns={columns}
      dataSource={data?.items || []}
      loading={loading}
      rowKey={(record) => `${record.contract_id}-${record.milestone_type}-${record.due_date}`}
      pagination={{ pageSize: 10 }}
      size="small"
      locale={{ emptyText: <Empty description="暂无里程碑提醒" /> }}
    />
  );
}

/**
 * 销售工作站主组件
 */
export default function SalesWorkstation() {
  const { data: summaryData, loading: summaryLoading, refetch } = useSalesWorkstationData();

  const tabItems = [
    {
      key: "follow-up",
      label: (
        <span>
          <BellOutlined />
          跟进提醒
          {summaryData.followUpSummary?.by_urgency?.overdue?.count > 0 && (
            <Badge
              count={summaryData.followUpSummary.by_urgency.overdue.count}
              style={{ marginLeft: 8 }}
            />
          )}
        </span>
      ),
      children: <FollowUpList />,
    },
    {
      key: "collection",
      label: (
        <span>
          <DollarOutlined />
          催款管理
          {summaryData.collectionSummary?.critical_count > 0 && (
            <Badge
              count={summaryData.collectionSummary.critical_count}
              style={{ marginLeft: 8 }}
            />
          )}
        </span>
      ),
      children: <CollectionList />,
    },
    {
      key: "health",
      label: (
        <span>
          <HeartOutlined />
          商机健康
          {summaryData.healthSummary?.by_level?.critical?.count > 0 && (
            <Badge
              count={summaryData.healthSummary.by_level.critical.count}
              style={{ marginLeft: 8 }}
            />
          )}
        </span>
      ),
      children: <HealthList />,
    },
    {
      key: "milestone",
      label: (
        <span>
          <CalendarOutlined />
          合同里程碑
          {summaryData.milestoneSummary?.by_urgency?.overdue?.count > 0 && (
            <Badge
              count={summaryData.milestoneSummary.by_urgency.overdue.count}
              style={{ marginLeft: 8 }}
            />
          )}
        </span>
      ),
      children: <MilestoneList />,
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Title level={4} style={{ margin: 0 }}>
          销售工作站
        </Title>
        <Button icon={<ReloadOutlined />} onClick={refetch}>
          刷新
        </Button>
      </div>

      {/* 统计卡片 */}
      <div style={{ marginBottom: 24 }}>
        <SummaryCards data={summaryData} loading={summaryLoading} />
      </div>

      {/* 详情 Tab */}
      <Card>
        <Tabs items={tabItems} defaultActiveKey="follow-up" />
      </Card>
    </div>
  );
}
