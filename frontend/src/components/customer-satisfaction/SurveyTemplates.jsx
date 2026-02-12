/**
 * Survey Templates Component
 * 问卷模板组件（占位实现，保证页面可运行）
 */

import React, { useMemo } from 'react';
import { Card, List, Button, Tag, Typography } from 'antd';
import { SURVEY_TYPES } from '@/lib/constants/customer';

const { Text } = Typography;

const SurveyTemplates = ({ loading = false, onUseTemplate }) => {
  const templates = useMemo(() => {
    return [
      { id: 'tpl_service', title: '标准服务满意度问卷', type: 'service', description: '适用于服务交付后的满意度回访' },
      { id: 'tpl_product', title: '产品满意度问卷', type: 'product', description: '适用于产品交付后的体验反馈' },
      { id: 'tpl_overall', title: '综合满意度问卷', type: 'overall', description: '适用于周期性客户满意度盘点' }
    ];
  }, []);

  return (
    <Card title="问卷模板" loading={loading}>
      <List
        dataSource={templates}
        renderItem={(item) => (
          <List.Item
            actions={[
              <Button type="primary" onClick={() => onUseTemplate?.(item)} key="use">
                使用模板
              </Button>
            ]}
          >
            <List.Item.Meta
              title={
                <span>
                  {item.title}{' '}
                  <Tag>{SURVEY_TYPES[item.type?.toUpperCase()]?.label || item.type}</Tag>
                </span>
              }
              description={<Text type="secondary">{item.description}</Text>}
            />
          </List.Item>
        )}
      />
    </Card>
  );
};

export default SurveyTemplates;

