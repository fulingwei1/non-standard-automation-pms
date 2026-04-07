/**
 * Approval Rules Component
 * 审批规则组件（简化版）
 */

import { Typography } from "antd";

import { APPROVAL_RULES } from "@/lib/constants/approval";

const { Text } = Typography;

const ApprovalRules = ({ loading }) => {
  const rules = Object.values(APPROVAL_RULES);

  return (
    <Card
      loading={loading}
      title={
        <Space>
          <Settings size={16} />
          审批规则（示例）
        </Space>
      }
    >
      <List
        dataSource={rules}
        renderItem={(rule) => (
          <List.Item>
            <Space orientation="vertical" size={2} style={{ width: "100%" }}>
              <Space wrap>
                <Text strong>{rule.label}</Text>
                <Tag>{rule.value}</Tag>
              </Space>
              <Text type="secondary">{rule.description}</Text>
            </Space>
          </List.Item>
        )}
      />
    </Card>
  );
};

export default ApprovalRules;

