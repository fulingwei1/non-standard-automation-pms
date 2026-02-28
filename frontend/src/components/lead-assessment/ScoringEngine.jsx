/**
 * Scoring Engine Component
 * 评分引擎组件：对线索进行批量重新评分（简化版）
 */

import { Card, Space, Table, Button, Progress, Typography, Alert } from "antd";
import { RefreshCw } from "lucide-react";

const { Text } = Typography;

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

const scoreLead = (lead, criteria) => {
  // 这里做一个可解释的“简化评分”，用于保证页面可运行。
  // 真实项目可以替换为更严谨的评分算法。

  const budgetScoreMap = { low: 8, medium: 15, high: 22, very_high: 25 };
  const authorityScoreMap = { specialist: 5, manager: 10, procurement: 12, cto: 16, ceo: 20, other: 6 };
  const needScoreMap = { urgent: 25, high: 20, normal: 12, low: 6 };
  const timelineScoreMap = { immediate: 15, short_term: 12, mid_term: 8, long_term: 5 };

  const budget = budgetScoreMap[lead.budget] ?? 10;
  const authority = authorityScoreMap[lead.authority] ?? 8;
  const need = needScoreMap[lead.need] ?? 10;
  const timeline = timelineScoreMap[lead.timeline] ?? 8;

  // competition 在 mock 数据中未提供，给一个中性分
  const competition = 10;

  const maxBudget = criteria?.BUDGET?.maxScore ?? 25;
  const maxAuthority = criteria?.AUTHORITY?.maxScore ?? 20;
  const maxNeed = criteria?.NEED?.maxScore ?? 25;
  const maxTimeline = criteria?.TIMELINE?.maxScore ?? 15;
  const maxCompetition = criteria?.COMPETITION?.maxScore ?? 15;

  const total =
    clamp(budget, 0, maxBudget) +
    clamp(authority, 0, maxAuthority) +
    clamp(need, 0, maxNeed) +
    clamp(timeline, 0, maxTimeline) +
    clamp(competition, 0, maxCompetition);

  return clamp(Math.round(total), 0, 100);
};

const ScoringEngine = ({ leads = [], criteria, onReScore }) => {
  const columns = [
    { title: "公司", dataIndex: "companyName", key: "companyName", width: 240 },
    { title: "联系人", dataIndex: "contactPerson", key: "contactPerson", width: 140 },
    {
      title: "评分",
      dataIndex: "score",
      key: "score",
      width: 180,
      render: (value) => <Progress percent={Number(value) || 0} size="small" />
    }
  ];

  const handleRescore = () => {
    const updated = leads.map((lead) => ({ ...lead, score: scoreLead(lead, criteria) }));
    onReScore?.(updated);
  };

  return (
    <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Alert
        type="info"
        showIcon
        message="提示"
        description="这是简化版评分引擎，用于保证页面可运行。你可以在此基础上替换成真实的评分逻辑。"
      />

      <Card
        title="评分引擎"
        extra={
          <Button type="primary" icon={<RefreshCw size={16} />} onClick={handleRescore}>
            重新评分
          </Button>
        }
      >
        <Text type="secondary">当前线索数：{leads.length}</Text>
        <Table
          rowKey={(row) => row.id ?? row.companyName}
          columns={columns}
          dataSource={leads}
          pagination={{ pageSize: 10, showSizeChanger: true }}
          scroll={{ x: 600 }}
        />
      </Card>
    </Space>
  );
};

export default ScoringEngine;

