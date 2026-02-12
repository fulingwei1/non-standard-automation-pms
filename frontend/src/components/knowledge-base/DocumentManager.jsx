/**
 * Document Manager Component
 * 文档管理组件（占位实现，保证拆分后的导出可用）
 */

import React, { useMemo } from 'react';
import { Card, Table, Tag, Space, Button, Typography } from 'antd';
import { KNOWLEDGE_TYPES, CATEGORIES, STATUS_OPTIONS, ACCESS_LEVELS, TABLE_CONFIG } from '@/lib/constants/knowledge';

const { Text } = Typography;

const DocumentManager = ({ documents = [], loading = false, onView, onEdit, onDelete }) => {
  const columns = useMemo(() => {
    return [
      {
        title: '标题',
        key: 'title',
        render: (_, record) => (
          <div>
            <div style={{ fontWeight: 600 }}>{record.title}</div>
            <div style={{ marginTop: 4, fontSize: 12, color: '#666' }}>
              <Tag>{KNOWLEDGE_TYPES[record.type?.toUpperCase()]?.label || record.type || '-'}</Tag>
              <Tag>{CATEGORIES[record.category?.toUpperCase()]?.label || record.category || '-'}</Tag>
            </div>
          </div>
        )
      },
      {
        title: '状态',
        key: 'status',
        width: 140,
        render: (_, record) => {
          const statusConfig = STATUS_OPTIONS[record.status?.toUpperCase()];
          return <Tag color={statusConfig?.color}>{statusConfig?.label || record.status || '-'}</Tag>;
        }
      },
      {
        title: '权限',
        key: 'accessLevel',
        width: 140,
        render: (_, record) => {
          const accessConfig = ACCESS_LEVELS[record.accessLevel?.toUpperCase()];
          return <Tag color={accessConfig?.color}>{accessConfig?.label || record.accessLevel || '-'}</Tag>;
        }
      },
      {
        title: '作者',
        dataIndex: 'author',
        key: 'author',
        width: 120,
        render: (author) => <Text type="secondary">{author || '-'}</Text>
      },
      {
        title: '操作',
        key: 'actions',
        width: 200,
        render: (_, record) => (
          <Space>
            <Button type="link" onClick={() => onView?.(record)}>
              查看
            </Button>
            <Button type="link" onClick={() => onEdit?.(record)}>
              编辑
            </Button>
            <Button type="link" danger onClick={() => onDelete?.(record)}>
              删除
            </Button>
          </Space>
        )
      }
    ];
  }, [onDelete, onEdit, onView]);

  return (
    <Card title="文档管理">
      <Table
        rowKey="id"
        columns={columns}
        dataSource={documents}
        loading={loading}
        {...TABLE_CONFIG}
      />
    </Card>
  );
};

export default DocumentManager;

