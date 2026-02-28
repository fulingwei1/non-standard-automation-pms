/**
 * Approval Workflow Component
 * 流程管理组件（简化占位版）
 */

import { Card, List, Space, Tag, Typography } from "antd";
import { Wrench } from "lucide-react";

import { WORKFLOW_STEPS, APPROVAL_RULES } from "@/lib/constants/approval";

const { Text } = Typography;

const ApprovalWorkflow = ({ loading }) => {
  const steps = Object.values(WORKFLOW_STEPS);
  const rules = Object.values(APPROVAL_RULES);

  return (
    <Space orientation="vertical" size={16} style={{ width: "100%" }}>
      <Card
        loading={loading}
        title={
          <Space>
            <Wrench size={16} />
            流程步骤（示例）
          </Space>
        }
      >
        <List
          dataSource={steps}
          renderItem={(step) => (
            <List.Item>
              <Space wrap>
                <Tag color={step.color}>{step.label}</Tag>
                <Text type="secondary">{step.value}</Text>
              </Space>
            </List.Item>
          )}
        />
      </Card>

      <Card loading={loading} title="规则类型（示例）">
        <List
          dataSource={rules}
          renderItem={(rule) => (
            <List.Item>
              <Space orientation="vertical" size={0}>
                <Text strong>{rule.label}</Text>
                <Text type="secondary">{rule.description}</Text>
              </Space>
            </List.Item>
          )}
        />
      </Card>
    </Space>
  );
};

export default ApprovalWorkflow;

