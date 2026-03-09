/**
 * InteractionHistoryTab - 交互历史Tab
 * 展示客户交互时间线和统计分析
 */

import { Card, Row, Col, Statistic, Typography } from "antd";
import { Phone, Mail, Users, FileText, Calendar } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const { Text } = Typography;

const InteractionHistoryTab = ({ timeline, loading }) => {
  if (!timeline && !loading) {
    return (
      <div style={{ textAlign: "center", padding: "40px" }}>
        <Text type="secondary">暂无交互历史数据</Text>
      </div>
    );
  }

  // 统计各类交互次数
  const getInteractionStats = () => {
    const stats = {
      call: 0,
      email: 0,
      meeting: 0,
      visit: 0,
      other: 0,
      total: timeline?.length || 0,
    };

    (timeline || []).forEach((item) => {
      const type = item.interaction_type?.toLowerCase() || "other";
      if (stats[type] !== undefined) {
        stats[type]++;
      } else {
        stats.other++;
      }
    });

    return stats;
  };

  const stats = getInteractionStats();

  // 准备柱状图数据（按月统计）
  const getMonthlyData = () => {
    const monthlyMap = {};
    (timeline || []).forEach((item) => {
      const month = item.interaction_date
        ? new Date(item.interaction_date).toLocaleDateString("zh-CN", {
            year: "numeric",
            month: "2-digit",
          })
        : "未知";
      monthlyMap[month] = (monthlyMap[month] || 0) + 1;
    });

    return Object.entries(monthlyMap)
      .map(([month, count]) => ({ month, count }))
      .sort((a, b) => a.month.localeCompare(b.month))
      .slice(-6); // 最近6个月
  };

  const monthlyData = getMonthlyData();

  // 格式化时间线数据
  const formatTimeline = () => {
    return (timeline || [])
      .sort((a, b) => new Date(b.interaction_date) - new Date(a.interaction_date))
      .map((item) => ({
        ...item,
        formattedDate: item.interaction_date
          ? new Date(item.interaction_date).toLocaleString("zh-CN")
          : "未知时间",
      }));
  };

  const formattedTimeline = formatTimeline();

  // 交互类型图标映射
  const typeIcons = {
    call: <Phone size={16} />,
    email: <Mail size={16} />,
    meeting: <Users size={16} />,
    visit: <FileText size={16} />,
    other: <Calendar size={16} />,
  };

  return (
    <div style={{ padding: "24px" }}>
      {/* 统计概览 */}
      <Card loading={loading} style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col xs={12} md={4}>
            <Statistic
              title="总交互次数"
              value={stats.total}
              prefix={<Calendar size={20} />}
            />
          </Col>
          <Col xs={12} md={4}>
            <Statistic
              title="电话沟通"
              value={stats.call}
              prefix={<Phone size={20} />}
              valueStyle={{ color: "#1890ff" }}
            />
          </Col>
          <Col xs={12} md={4}>
            <Statistic
              title="邮件往来"
              value={stats.email}
              prefix={<Mail size={20} />}
              valueStyle={{ color: "#52c41a" }}
            />
          </Col>
          <Col xs={12} md={4}>
            <Statistic
              title="会议沟通"
              value={stats.meeting}
              prefix={<Users size={20} />}
              valueStyle={{ color: "#722ed1" }}
            />
          </Col>
          <Col xs={12} md={4}>
            <Statistic
              title="现场拜访"
              value={stats.visit}
              prefix={<FileText size={20} />}
              valueStyle={{ color: "#eb2f96" }}
            />
          </Col>
          <Col xs={12} md={4}>
            <Statistic
              title="其他交互"
              value={stats.other}
              prefix={<Calendar size={20} />}
              valueStyle={{ color: "#faad14" }}
            />
          </Col>
        </Row>
      </Card>

      {/* 按月统计柱状图 */}
      <Card loading={loading} title="交互趋势" style={{ marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#1890ff" name="交互次数" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* 交互时间线 */}
      <Card loading={loading} title="交互时间线">
        <div style={{ maxHeight: 600, overflowY: "auto" }}>
          {formattedTimeline.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px" }}>
              <Text type="secondary">暂无交互记录</Text>
            </div>
          ) : (
            <div style={{ position: "relative", paddingLeft: 40 }}>
              {/* 时间轴线 */}
              <div
                style={{
                  position: "absolute",
                  left: 16,
                  top: 0,
                  bottom: 0,
                  width: 2,
                  background: "#e8e8e8",
                }}
              />

              {formattedTimeline.map((item, index) => (
                <div
                  key={item.id || index}
                  style={{
                    position: "relative",
                    marginBottom: 24,
                    paddingBottom: 24,
                    borderBottom: index < formattedTimeline.length - 1 ? "1px solid #f0f0f0" : "none",
                  }}
                >
                  {/* 时间轴节点 */}
                  <div
                    style={{
                      position: "absolute",
                      left: -32,
                      top: 4,
                      width: 12,
                      height: 12,
                      borderRadius: "50%",
                      background: "#1890ff",
                      border: "2px solid white",
                      boxShadow: "0 0 0 2px #1890ff",
                    }}
                  />

                  <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                        {typeIcons[item.interaction_type?.toLowerCase()] || typeIcons.other}
                        <Text strong>{item.interaction_type || "其他"}</Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {item.formattedDate}
                        </Text>
                      </div>
                      <Text>{item.description || "无描述"}</Text>
                      {item.outcome && (
                        <div style={{ marginTop: 8 }}>
                          <Text type="secondary">结果: </Text>
                          <Text>{item.outcome}</Text>
                        </div>
                      )}
                      {item.next_steps && (
                        <div style={{ marginTop: 4 }}>
                          <Text type="secondary">下一步: </Text>
                          <Text>{item.next_steps}</Text>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default InteractionHistoryTab;
