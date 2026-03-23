/**
 * PurchaseAnalysisTab - 购买分析Tab
 * 展示购买偏好和历史统计
 */

import { Typography } from "antd";



const { Title, Text, Paragraph } = Typography;

const PurchaseAnalysisTab = ({ buyingPreferences, customer, loading }) => {
  if (!buyingPreferences && !customer && !loading) {
    return (
      <div style={{ textAlign: "center", padding: "40px" }}>
        <Text type="secondary">暂无购买分析数据</Text>
      </div>
    );
  }

  // 购买偏好数据
  const preferredCategories = buyingPreferences?.preferred_categories || [
    { name: "软件服务", value: 35, color: "#1890ff" },
    { name: "硬件设备", value: 25, color: "#52c41a" },
    { name: "技术咨询", value: 20, color: "#722ed1" },
    { name: "维护服务", value: 15, color: "#faad14" },
    { name: "其他", value: 5, color: "#eb2f96" },
  ];

  const purchaseFrequency = buyingPreferences?.purchase_frequency || "季度";
  const avgOrderValue = buyingPreferences?.avg_order_value || 850000;
  const totalPurchases = buyingPreferences?.total_purchases || 24;
  const lifetimeValue = buyingPreferences?.lifetime_value || 20400000;

  // 模拟历史购买趋势数据
  const purchaseHistory = [
    { month: "2025-07", amount: 650000 },
    { month: "2025-08", amount: 720000 },
    { month: "2025-09", amount: 890000 },
    { month: "2025-10", amount: 950000 },
    { month: "2025-11", amount: 1050000 },
    { month: "2025-12", amount: 980000 },
    { month: "2026-01", amount: 1120000 },
    { month: "2026-02", amount: 1050000 },
  ];

  // 购买决策因素
  const decisionFactors = buyingPreferences?.decision_factors || [
    { factor: "产品质量", importance: "high", score: 9.2 },
    { factor: "价格竞争力", importance: "high", score: 8.5 },
    { factor: "售后服务", importance: "medium", score: 8.8 },
    { factor: "品牌信誉", importance: "medium", score: 8.3 },
    { factor: "交付速度", importance: "low", score: 7.5 },
  ];

  const importanceColors = {
    high: "red",
    medium: "orange",
    low: "blue",
  };

  const importanceLabels = {
    high: "高",
    medium: "中",
    low: "低",
  };

  return (
    <div style={{ padding: "24px" }}>
      {/* 关键指标概览 */}
      <Card loading={loading} style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col xs={12} md={6}>
            <Statistic
              title="客户生命周期价值"
              value={lifetimeValue}
              prefix="¥"
              valueStyle={{ color: "#1890ff" }}
              suffix={<DollarSign size={16} />}
            />
          </Col>
          <Col xs={12} md={6}>
            <Statistic
              title="平均订单金额"
              value={avgOrderValue}
              prefix="¥"
              valueStyle={{ color: "#52c41a" }}
              suffix={<ShoppingCart size={16} />}
            />
          </Col>
          <Col xs={12} md={6}>
            <Statistic
              title="累计购买次数"
              value={totalPurchases}
              prefix={<Package size={20} />}
              valueStyle={{ color: "#722ed1" }}
            />
          </Col>
          <Col xs={12} md={6}>
            <Statistic
              title="购买频率"
              value={purchaseFrequency}
              prefix={<Calendar size={20} />}
              valueStyle={{ color: "#faad14" }}
            />
          </Col>
        </Row>
      </Card>

      <Row gutter={24}>
        {/* 购买偏好分类 */}
        <Col xs={24} lg={12}>
          <Card
            loading={loading}
            title={
              <Space>
                <Award size={16} />
                <span>购买品类分布</span>
              </Space>
            }
            style={{ marginBottom: 24 }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={preferredCategories}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {preferredCategories.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>

            <div style={{ marginTop: 16 }}>
              {preferredCategories.map((category) => (
                <div
                  key={category.name}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 8,
                  }}
                >
                  <Space>
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        borderRadius: "50%",
                        background: category.color,
                      }}
                    />
                    <Text>{category.name}</Text>
                  </Space>
                  <Text strong>{category.value}%</Text>
                </div>
              ))}
            </div>
          </Card>
        </Col>

        {/* 购买决策因素 */}
        <Col xs={24} lg={12}>
          <Card
            loading={loading}
            title={
              <Space>
                <TrendingUp size={16} />
                <span>购买决策因素</span>
              </Space>
            }
            style={{ marginBottom: 24 }}
          >
            <List
              dataSource={decisionFactors}
              renderItem={(item) => (
                <List.Item>
                  <div style={{ width: "100%" }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: 8,
                      }}
                    >
                      <Space>
                        <Text strong>{item.factor}</Text>
                        <Tag color={importanceColors[item.importance]}>
                          重要性: {importanceLabels[item.importance]}
                        </Tag>
                      </Space>
                      <Text strong style={{ color: "#1890ff" }}>
                        {item.score}/10
                      </Text>
                    </div>
                    <div
                      style={{
                        width: "100%",
                        height: 8,
                        background: "#f0f0f0",
                        borderRadius: 4,
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          width: `${(item.score / 10) * 100}%`,
                          height: "100%",
                          background: "#1890ff",
                        }}
                      />
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* 购买历史趋势 */}
      <Card
        loading={loading}
        title={
          <Space>
            <ShoppingCart size={16} />
            <span>购买金额趋势（近8个月）</span>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={purchaseHistory}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip
              formatter={(value) => `¥${value.toLocaleString()}`}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="amount"
              stroke="#1890ff"
              strokeWidth={2}
              name="购买金额"
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* 购买偏好总结 */}
      <Card
        loading={loading}
        title="购买偏好总结"
      >
        <Paragraph>
          <Text strong>采购周期: </Text>
          {buyingPreferences?.purchase_cycle || "该客户通常在每季度初进行采购计划，平均采购周期为3个月。"}
        </Paragraph>
        <Paragraph>
          <Text strong>预算规模: </Text>
          {buyingPreferences?.budget_range || "年度IT预算约在800万-1200万之间，其中软件服务占比最大。"}
        </Paragraph>
        <Paragraph>
          <Text strong>决策流程: </Text>
          {buyingPreferences?.decision_process || "采购决策需要技术部门、财务部门和高管层三方审批，平均决策周期45天。"}
        </Paragraph>
        <Paragraph>
          <Text strong>偏好供应商特征: </Text>
          {buyingPreferences?.preferred_supplier_traits ||
            "倾向于选择有行业经验、提供完整解决方案、售后服务完善的供应商。"}
        </Paragraph>
      </Card>
    </div>
  );
};

export default PurchaseAnalysisTab;
