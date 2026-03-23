/**
 * Follow-up Manager Component
 * 跟进管理组件：展示待跟进/逾期等跟进任务（简化版）
 */

import { Typography } from "antd";

import { FOLLOW_UP_STATUS, TASK_TYPES } from "@/lib/constants/leadAssessment";

const { Text } = Typography;

const getConfigByValue = (configs, value, fallbackLabel = "-") => {
  const match = Object.values(configs).find((item) => item.value === value);
  if (match) {return match;}
  return { label: fallbackLabel, color: "#8c8c8c", icon: "📝" };
};

const FollowUpManager = ({ followUps = [], leads = [], loading, onRefresh }) => {
  const leadMap = new Map((leads || []).map((l) => [l.id, l]));

  return (
    <Card
      loading={loading}
      title="跟进管理"
      extra={
        <Button icon={<RefreshCw size={16} />} onClick={() => onRefresh?.()}>
          刷新
        </Button>
      }
    >
      {followUps.length === 0 ? (
        <Empty description="暂无跟进任务" />
      ) : (
        <List
          dataSource={followUps}
          renderItem={(item) => {
            const status = getConfigByValue(FOLLOW_UP_STATUS, item.status, item.status);
            const taskType = getConfigByValue(TASK_TYPES, item.type, item.type);
            const lead = leadMap.get(item.leadId);

            return (
              <List.Item key={item.id}>
                <Space orientation="vertical" size={4} style={{ width: "100%" }}>
                  <Space wrap>
                    <Text strong>{item.leadCompany || lead?.companyName || "未知客户"}</Text>
                    <Tag color={status.color}>{status.label}</Tag>
                    <Tag>{taskType.icon} {taskType.label}</Tag>
                  </Space>
                  <Text type="secondary">{item.description}</Text>
                  <Text type="secondary">截止日期：{item.dueDate || "-"}</Text>
                </Space>
              </List.Item>
            );
          }}
        />
      )}
    </Card>
  );
};

export default FollowUpManager;

