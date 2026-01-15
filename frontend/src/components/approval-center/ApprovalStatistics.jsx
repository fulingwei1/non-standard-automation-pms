/**
 * Approval Statistics Component
 * 统计分析组件（简化版）
 */

import { Card, Col, Row, Space, Statistic, Progress, Typography } from "antd";
import { TrendingUp, Clock, AlertCircle } from "lucide-react";

const { Text } = Typography;

const ApprovalStatistics = ({ data, loading }) => {
  const metrics = data?.metrics || {};
  const avgProcessingTime = metrics.avgProcessingTime ?? 0;
  const overdueRate = metrics.overdueRate ?? 0;
  const satisfactionRate = metrics.satisfactionRate ?? 0;

  return (
    <Space direction="vertical" size={16} style={{ width: "100%" }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <Card loading={loading}>
            <Statistic title="平均处理时长" value={avgProcessingTime} suffix="小时" prefix={<Clock size={18} />} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading}>
            <Statistic title="超期率" value={overdueRate} suffix="%" prefix={<AlertCircle size={18} />} />
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card loading={loading}>
            <Statistic title="满意度" value={satisfactionRate} suffix="%" prefix={<TrendingUp size={18} />} />
          </Card>
        </Col>
      </Row>

      <Card loading={loading} title="指标进度">
        <Space direction="vertical" size={12} style={{ width: "100%" }}>
          <div>
            <Text>满意度</Text>
            <Progress percent={Number(satisfactionRate) || 0} status="success" />
          </div>
          <div>
            <Text>超期率（越低越好）</Text>
            <Progress percent={Number(overdueRate) || 0} status={overdueRate > 10 ? "exception" : "active"} />
          </div>
        </Space>
      </Card>
    </Space>
  );
};

export default ApprovalStatistics;

