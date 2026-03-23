/**
 * RelationshipMaturityTab - 关系成熟度Tab
 * 展示雷达图、六维度得分、改进建议、历史趋势
 */

import { Typography } from "antd";



const { Title, Text, Paragraph } = Typography;

const RelationshipMaturityTab = ({ healthScore, customerId, loading }) => {
  if (!healthScore && !loading) {
    return (
      <div style={{ textAlign: "center", padding: "40px" }}>
        <Text type="secondary">暂无关系成熟度数据</Text>
      </div>
    );
  }

  // 六个维度的配置
  const dimensions = [
    { key: "trust_score", label: "信任度", color: "#1890ff" },
    { key: "engagement_score", label: "参与度", color: "#52c41a" },
    { key: "satisfaction_score", label: "满意度", color: "#722ed1" },
    { key: "loyalty_score", label: "忠诚度", color: "#eb2f96" },
    { key: "value_alignment_score", label: "价值契合", color: "#faad14" },
    { key: "growth_potential_score", label: "增长潜力", color: "#13c2c2" },
  ];

  // 准备雷达图数据
  const radarData = dimensions.map((dim) => ({
    subject: dim.label,
    score: healthScore?.[dim.key] || 0,
    fullMark: 100,
  }));

  // 模拟历史趋势数据（实际应该从API获取）
  const historyData = [
    { month: "1月", overall: 65 },
    { month: "2月", overall: 68 },
    { month: "3月", overall: 72 },
    { month: "4月", overall: 75 },
    { month: "5月", overall: 78 },
    { month: "6月", overall: healthScore?.overall_score || 80 },
  ];

  // 获取整体评级
  const getOverallRating = (score) => {
    if (score >= 85) return { label: "优秀", color: "success" };
    if (score >= 70) return { label: "良好", color: "processing" };
    if (score >= 50) return { label: "一般", color: "warning" };
    return { label: "需改进", color: "error" };
  };

  const overallScore = healthScore?.overall_score || 0;
  const rating = getOverallRating(overallScore);

  return (
    <div style={{ padding: "24px" }}>
      {/* 整体得分卡片 */}
      <Card loading={loading} style={{ marginBottom: 24 }}>
        <Row gutter={24} align="middle">
          <Col xs={24} md={8} style={{ textAlign: "center" }}>
            <div style={{ fontSize: 64, fontWeight: "bold", color: "#1890ff" }}>
              {overallScore}
            </div>
            <Title level={4}>整体成熟度得分</Title>
            <Tag color={rating.color} style={{ fontSize: 16, padding: "4px 16px" }}>
              {rating.label}
            </Tag>
          </Col>

          <Col xs={24} md={16}>
            <Alert
              message={`关系成熟度评级: ${rating.label}`}
              description={
                healthScore?.evaluation_summary ||
                "该客户关系处于稳定发展阶段，建议继续加强沟通与合作。"
              }
              type={rating.color === "error" ? "warning" : "info"}
              showIcon
              icon={rating.color === "error" ? <AlertCircle /> : <CheckCircle />}
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={24}>
        {/* 雷达图 */}
        <Col xs={24} lg={12}>
          <Card
            loading={loading}
            title={
              <span>
                <Target size={16} style={{ marginRight: 8 }} />
                六维度分析雷达图
              </span>
            }
            style={{ marginBottom: 24 }}
          >
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="得分"
                  dataKey="score"
                  stroke="#1890ff"
                  fill="#1890ff"
                  fillOpacity={0.6}
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* 六维度详细得分 */}
        <Col xs={24} lg={12}>
          <Card
            loading={loading}
            title={
              <span>
                <TrendingUp size={16} style={{ marginRight: 8 }} />
                六维度详细得分
              </span>
            }
            style={{ marginBottom: 24 }}
          >
            <div style={{ padding: "12px 0" }}>
              {dimensions.map((dim) => {
                const score = healthScore?.[dim.key] || 0;
                return (
                  <div key={dim.key} style={{ marginBottom: 24 }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: 8,
                      }}
                    >
                      <Text strong>{dim.label}</Text>
                      <Text strong style={{ color: dim.color }}>
                        {score}
                      </Text>
                    </div>
                    <Progress
                      percent={score}
                      strokeColor={dim.color}
                      showInfo={false}
                    />
                  </div>
                );
              })}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 历史趋势图 */}
      <Card
        loading={loading}
        title="历史趋势"
        style={{ marginBottom: 24 }}
      >
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={historyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="overall"
              stroke="#1890ff"
              strokeWidth={2}
              name="整体成熟度"
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* 改进建议 */}
      <Card
        loading={loading}
        title={
          <span>
            <AlertCircle size={16} style={{ marginRight: 8 }} />
            改进建议
          </span>
        }
      >
        <List
          dataSource={healthScore?.improvement_suggestions || [
            "加强与决策者的定期沟通，提升信任度",
            "组织客户培训活动，提高产品使用满意度",
            "定期收集客户反馈，优化服务流程",
            "建立长期战略合作伙伴关系，提升忠诚度",
          ]}
          renderItem={(item, index) => (
            <List.Item>
              <div style={{ display: "flex", alignItems: "flex-start" }}>
                <div
                  style={{
                    width: 24,
                    height: 24,
                    borderRadius: "50%",
                    background: "#1890ff",
                    color: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginRight: 12,
                    flexShrink: 0,
                  }}
                >
                  {index + 1}
                </div>
                <Paragraph style={{ margin: 0 }}>{item}</Paragraph>
              </div>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default RelationshipMaturityTab;
