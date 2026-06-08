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
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Progress,
  Tabs,
  Badge,
  Alert,
  Empty,
  Typography,
  Space,
  Button,
  Tooltip,
} from "antd";
import {
  BellOutlined,
  DollarOutlined,
  HeartOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
  ArrowRightOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import {
  useSalesWorkstationData,
  useFollowUpReminders,
  useCollectionPriority,
  useOpportunityHealthList,
  useContractMilestones,
} from "../hooks/useSalesWorkstation";
import {
  buildSalesOpportunityCenterPath,
  buildTechnicalAssessmentPath,
  SALES_LEAD_LIST_PATH,
  SALES_OPPORTUNITY_LIST_PATH,
} from "../lib/salesNavigation";

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

const numberOrZero = (value) => Number(value || 0);
const COLLECTION_DRILLDOWN_PATH =
  "/sales/receivables?source=sales_workstation&view=overdue_receivables&overdue_only=true";

const buildCollectionReceivablePath = (record = {}) => {
  const params = new URLSearchParams({
    source: "sales_workstation",
    view: "collection_risk",
    overdue_only: "true",
  });
  if (record.customer_id) {
    params.set("customer_id", String(record.customer_id));
  }
  if (record.contract_id) {
    params.set("contract_id", String(record.contract_id));
  }
  return `/sales/receivables?${params.toString()}`;
};

const buildFollowUpTargetPath = (record = {}) => {
  const isLead = record.entity_type === "lead";
  if (record.entity_id) {
    return isLead
      ? `/sales/leads/${record.entity_id}`
      : `/sales/opportunities/${record.entity_id}`;
  }
  return isLead ? SALES_LEAD_LIST_PATH : SALES_OPPORTUNITY_LIST_PATH;
};

const buildFollowUpAssessmentPath = (record = {}) => {
  const isLead = record.entity_type === "lead";
  return buildTechnicalAssessmentPath(
    isLead ? "lead" : "opportunity",
    record.entity_id,
    {
      assessmentId: record.assessment_id,
      presaleTicketId:
        record.presale_ticket_id ||
        record.ticket_id ||
        record.presaleTicketId ||
        record.ticketId,
      leadId: record.lead_id || record.leadId,
      projectId: record.project_id || record.projectId,
    }
  );
};

const buildOpportunityHealthPath = (record = {}) =>
  record.opportunity_id
    ? `/sales/opportunities/${record.opportunity_id}`
    : SALES_OPPORTUNITY_LIST_PATH;

const buildContractMilestonePath = (record = {}) =>
  record.contract_id ? `/sales/contracts/${record.contract_id}` : "/sales/contracts";

/**
 * 今日行动和销售闭环阶段
 */
function ActionBoard({ data }) {
  const navigate = useNavigate();
  const followUpCount = numberOrZero(data.followUpSummary?.total_count);
  const overdueFollowUpCount = numberOrZero(
    data.followUpSummary?.by_urgency?.overdue?.count
  );
  const quoteRiskCount = numberOrZero(
    data.healthSummary?.by_level?.critical?.count
  );
  const contractUrgentCount = numberOrZero(
    data.milestoneSummary?.by_urgency?.urgent?.count
  ) + numberOrZero(data.milestoneSummary?.by_urgency?.overdue?.count);
  const collectionCount = numberOrZero(data.collectionSummary?.total_count);
  const funnelSummary = data.salesFunnelSummary || {};
  const initiationCount = numberOrZero(
    data.initiationSummary?.unique_count ?? data.initiationSummary?.total_count
  );

  const actionItems = [
    {
      title: "待跟进",
      count: followUpCount,
      emphasis: overdueFollowUpCount > 0 ? `${overdueFollowUpCount} 项逾期` : "按计划推进",
      button: "处理待跟进",
      path: SALES_LEAD_LIST_PATH,
      color: "#1890ff",
    },
    {
      title: "待报价",
      count: quoteRiskCount,
      emphasis: "商机风险优先处理",
      button: "推进报价",
      path: "/sales/quotes",
      color: "#52c41a",
    },
    {
      title: "待签约/立项",
      count: contractUrgentCount,
      emphasis: "合同节点和立项动作",
      button: "跟进合同",
      path: "/sales/contracts",
      color: "#722ed1",
    },
    {
      title: "待回款",
      count: collectionCount,
      emphasis:
        data.collectionSummary?.critical_count > 0
          ? `${data.collectionSummary.critical_count} 项紧急`
          : "按账期跟进",
      button: "催收回款",
      path: COLLECTION_DRILLDOWN_PATH,
      color: "#fa8c16",
    },
  ];

  const pipelineStages = [
    { title: "线索", count: numberOrZero(funnelSummary.leads), path: SALES_LEAD_LIST_PATH },
    {
      title: "商机",
      count: numberOrZero(funnelSummary.opportunities),
      path: buildSalesOpportunityCenterPath("opportunities"),
    },
    { title: "报价", count: numberOrZero(funnelSummary.quotes), path: "/sales/quotes" },
    { title: "合同", count: numberOrZero(funnelSummary.contracts), path: "/sales/contracts" },
    { title: "项目立项", count: initiationCount, path: "/pmo/initiations" },
  ];

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} xl={15}>
        <Card
          title="今日销售动作"
          extra={
            <Space size={8}>
              <Button type="link" onClick={() => navigate("/presales/workbench")}>
                售前工作台
              </Button>
              <Button type="link" onClick={() => navigate("/sales/funnel")}>
                销售数据看板
              </Button>
            </Space>
          }
        >
          <Row gutter={[12, 12]}>
            {actionItems.map((item) => (
              <Col xs={24} sm={12} lg={6} key={item.title}>
                <div
                  style={{
                    height: "100%",
                    minHeight: 132,
                    border: "1px solid #f0f0f0",
                    borderRadius: 8,
                    padding: 14,
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    borderTop: `3px solid ${item.color}`,
                  }}
                >
                  <Space orientation="vertical" size={2}>
                    <Text type="secondary">{item.title}</Text>
                    <Title level={3} style={{ margin: 0 }}>
                      {item.count}
                    </Title>
                    <Text type={item.count > 0 ? "warning" : "secondary"} style={{ fontSize: 12 }}>
                      {item.emphasis}
                    </Text>
                  </Space>
                  <Button block onClick={() => navigate(item.path)}>
                    {item.button}
                  </Button>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      </Col>
      <Col xs={24} xl={9}>
        <Card title="销售闭环" extra={<Text type="secondary">本月真实数据</Text>}>
          <Space orientation="vertical" size={12} style={{ width: "100%" }}>
            {pipelineStages.map((stage, index) => (
              <div
                key={stage.title}
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr auto auto",
                  alignItems: "center",
                  gap: 8,
                  minHeight: 42,
                }}
              >
                <Button type="text" onClick={() => navigate(stage.path)} style={{ textAlign: "left" }}>
                  {stage.title}
                </Button>
                <Tag
                  aria-label={`${stage.title}数量 ${stage.count}`}
                  color={stage.count > 0 ? "blue" : "default"}
                >
                  {stage.count}
                </Tag>
                {index < pipelineStages.length - 1 ? (
                  <ArrowRightOutlined style={{ color: "#8c8c8c" }} />
                ) : (
                  <CheckCircleOutlined style={{ color: "#52c41a" }} />
                )}
              </div>
            ))}
          </Space>
        </Card>
      </Col>
    </Row>
  );
}

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
            styles={{
              content: {
                color:
                  (healthSummary?.average_score || 0) >= 70
                    ? "#52c41a"
                    : (healthSummary?.average_score || 0) >= 50
                    ? "#faad14"
                    : "#f5222d",
              },
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
  const navigate = useNavigate();
  const { data, loading, error } = useFollowUpReminders();

  const columns = [
    {
      title: "客户/线索",
      dataIndex: "entity_name",
      key: "entity_name",
      render: (text, record) => (
        <Space orientation="vertical" size={0}>
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
        <Space orientation="vertical" size={0}>
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
    {
      title: "动作",
      key: "action",
      render: (_, record) => {
        const actionLabel = record.entity_type === "lead" ? "查看线索" : "查看商机";
        const actionName = `${actionLabel} ${record.entity_name || ""}`.trim();
        const assessmentName = `技术评估 ${record.entity_name || ""}`.trim();
        return (
          <Space size={4}>
            <Button
              type="link"
              size="small"
              aria-label={actionName}
              onClick={() => navigate(buildFollowUpTargetPath(record))}
            >
              {actionLabel}
            </Button>
            <Button
              type="link"
              size="small"
              aria-label={assessmentName}
              onClick={() => navigate(buildFollowUpAssessmentPath(record))}
            >
              技术评估
            </Button>
          </Space>
        );
      },
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
  const navigate = useNavigate();
  const { data, loading, error } = useCollectionPriority();

  const columns = [
    {
      title: "客户",
      dataIndex: "customer_name",
      key: "customer_name",
      render: (text, record) => (
        <Space orientation="vertical" size={0}>
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
    {
      title: "动作",
      key: "action",
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          onClick={() => navigate(buildCollectionReceivablePath(record))}
        >
          查看应收
        </Button>
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
  const navigate = useNavigate();
  const { data, loading, error } = useOpportunityHealthList();

  const columns = [
    {
      title: "商机",
      dataIndex: "opportunity_name",
      key: "opportunity_name",
      render: (text, record) => (
        <Space orientation="vertical" size={0}>
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
            size={40}
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
          <Space orientation="vertical" size={0}>
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
    {
      title: "动作",
      key: "action",
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          aria-label={`查看商机 ${record.opportunity_name || ""}`.trim()}
          onClick={() => navigate(buildOpportunityHealthPath(record))}
        >
          查看商机
        </Button>
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
  const navigate = useNavigate();
  const { data, loading, error } = useContractMilestones();

  const columns = [
    {
      title: "合同",
      dataIndex: "contract_name",
      key: "contract_name",
      render: (text, record) => (
        <Space orientation="vertical" size={0}>
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
        <Space orientation="vertical" size={0}>
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
    {
      title: "动作",
      key: "action",
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          aria-label={`查看合同 ${record.contract_name || ""}`.trim()}
          onClick={() => navigate(buildContractMilestonePath(record))}
        >
          查看合同
        </Button>
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

      <div style={{ marginBottom: 24 }}>
        <ActionBoard data={summaryData} />
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
