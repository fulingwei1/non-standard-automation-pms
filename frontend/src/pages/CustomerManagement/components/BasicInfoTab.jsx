/**
 * BasicInfoTab - 基本信息Tab
 * 展示客户基本信息和决策链联系人列表
 */

import { Typography } from "antd";



const { Title, Text } = Typography;

const BasicInfoTab = ({ customer, decisionChain, loading }) => {
  if (!customer && !loading) {
    return (
      <div style={{ textAlign: "center", padding: "40px" }}>
        <Text type="secondary">暂无客户数据</Text>
      </div>
    );
  }

  // 决策角色配置
  const roleConfig = {
    decision_maker: { label: "决策者", color: "red", icon: <Crown size={14} /> },
    influencer: { label: "影响者", color: "orange", icon: <Star size={14} /> },
    user: { label: "使用者", color: "blue", icon: <User size={14} /> },
    gatekeeper: { label: "守门人", color: "green", icon: <Award size={14} /> },
  };

  // 联系人表格列定义
  const contactColumns = [
    {
      title: "姓名",
      dataIndex: "name",
      key: "name",
      render: (text) => <Text strong>{text}</Text>,
    },
    {
      title: "职位",
      dataIndex: "title",
      key: "title",
    },
    {
      title: "决策角色",
      dataIndex: "decision_role",
      key: "decision_role",
      render: (role) => {
        const config = roleConfig[role] || { label: role, color: "default", icon: null };
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.label}
          </Tag>
        );
      },
    },
    {
      title: "邮箱",
      dataIndex: "email",
      key: "email",
      render: (email) => (
        <Space>
          <Mail size={14} />
          {email}
        </Space>
      ),
    },
    {
      title: "电话",
      dataIndex: "phone",
      key: "phone",
      render: (phone) => (
        <Space>
          <Phone size={14} />
          {phone}
        </Space>
      ),
    },
    {
      title: "影响力",
      dataIndex: "influence_level",
      key: "influence_level",
      render: (level) => {
        const colors = { high: "red", medium: "orange", low: "blue" };
        const labels = { high: "高", medium: "中", low: "低" };
        return (
          <Badge
            status={colors[level] === "red" ? "error" : colors[level] === "orange" ? "warning" : "processing"}
            text={labels[level] || level}
          />
        );
      },
    },
  ];

  return (
    <div style={{ padding: "24px" }}>
      {/* 客户基本信息卡片 */}
      <Card loading={loading} title="客户基本信息" style={{ marginBottom: 24 }}>
        <Row gutter={[24, 16]}>
          <Col xs={24} md={12}>
            <Space direction="vertical" size={12} style={{ width: "100%" }}>
              <div>
                <Text type="secondary">
                  <Building2 size={14} style={{ marginRight: 8 }} />
                  公司名称:
                </Text>
                <Text strong style={{ marginLeft: 8 }}>
                  {customer?.customer_name || "-"}
                </Text>
              </div>

              <div>
                <Text type="secondary">
                  <Mail size={14} style={{ marginRight: 8 }} />
                  主要邮箱:
                </Text>
                <Text style={{ marginLeft: 8 }}>{customer?.email || "-"}</Text>
              </div>

              <div>
                <Text type="secondary">
                  <Phone size={14} style={{ marginRight: 8 }} />
                  联系电话:
                </Text>
                <Text style={{ marginLeft: 8 }}>{customer?.phone || "-"}</Text>
              </div>

              <div>
                <Text type="secondary">
                  <MapPin size={14} style={{ marginRight: 8 }} />
                  公司地址:
                </Text>
                <Text style={{ marginLeft: 8 }}>{customer?.address || "-"}</Text>
              </div>
            </Space>
          </Col>

          <Col xs={24} md={12}>
            <Space direction="vertical" size={12} style={{ width: "100%" }}>
              <div>
                <Text type="secondary">
                  <Building2 size={14} style={{ marginRight: 8 }} />
                  所属行业:
                </Text>
                <Text style={{ marginLeft: 8 }}>{customer?.industry || "-"}</Text>
              </div>

              <div>
                <Text type="secondary">客户类型:</Text>
                <Tag color="blue" style={{ marginLeft: 8 }}>
                  {customer?.customer_type || "-"}
                </Tag>
              </div>

              <div>
                <Text type="secondary">
                  <Calendar size={14} style={{ marginRight: 8 }} />
                  创建时间:
                </Text>
                <Text style={{ marginLeft: 8 }}>
                  {customer?.created_at
                    ? new Date(customer.created_at).toLocaleDateString("zh-CN")
                    : "-"}
                </Text>
              </div>

              <div>
                <Text type="secondary">最后更新:</Text>
                <Text style={{ marginLeft: 8 }}>
                  {customer?.updated_at
                    ? new Date(customer.updated_at).toLocaleDateString("zh-CN")
                    : "-"}
                </Text>
              </div>
            </Space>
          </Col>
        </Row>

        {customer?.notes && (
          <>
            <Divider />
            <div>
              <Text type="secondary">备注:</Text>
              <div
                style={{
                  marginTop: 8,
                  padding: 12,
                  background: "#f5f5f5",
                  borderRadius: 6,
                }}
              >
                <Text>{customer.notes}</Text>
              </div>
            </div>
          </>
        )}
      </Card>

      {/* 决策链联系人列表 */}
      <Card
        loading={loading}
        title={
          <Space>
            <User size={18} />
            <span>决策链联系人</span>
            <Badge count={decisionChain?.length || 0} showZero />
          </Space>
        }
      >
        <Table
          columns={contactColumns}
          dataSource={decisionChain || []}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showTotal: (total) => `共 ${total} 位联系人`,
          }}
          locale={{
            emptyText: "暂无联系人数据",
          }}
        />
      </Card>
    </div>
  );
};

export default BasicInfoTab;
