/**
 * Signature Manager Component
 * 合同签署管理组件（占位实现，保证页面可运行）
 */

import React, { useMemo, useState } from 'react';
import { Card, Table, Tag, Space, Button, message } from 'antd';
import { CONTRACT_STATUS, SIGNATURE_STATUS } from './contractManagementConstants';

const SignatureManager = ({ contracts = [], loading = false, onRefresh, onSignComplete }) => {
  const [signingId, setSigningId] = useState(null);

  const handleMockSign = (contract) => {
    setSigningId(contract?.id ?? null);
    setTimeout(() => {
      message.success('已模拟签署完成');
      setSigningId(null);
      onSignComplete?.(contract);
      onRefresh?.();
    }, 600);
  };

  const columns = useMemo(() => {
    return [
      {
        title: '合同',
        key: 'title',
        render: (_, record) => record.title || record.contract_no || `合同-${record.id}`
      },
      {
        title: '状态',
        key: 'status',
        render: (_, record) => {
          const statusConfig = CONTRACT_STATUS[record.status?.toUpperCase()];
          const signatureConfig = SIGNATURE_STATUS[record.signatureStatus?.toUpperCase()];

          return (
            <Space>
              <Tag color={statusConfig?.color}>{statusConfig?.label || record.status || '-'}</Tag>
              <Tag color={signatureConfig?.color}>
                {signatureConfig?.label || record.signatureStatus || '-'}
              </Tag>
            </Space>
          );
        }
      },
      {
        title: '操作',
        key: 'actions',
        render: (_, record) => (
          <Space>
            <Button
              type="primary"
              size="small"
              loading={signingId === record.id}
              onClick={() => handleMockSign(record)}
            >
              模拟签署
            </Button>
          </Space>
        )
      }
    ];
  }, [signingId]);

  return (
    <Card
      title="签署任务"
      extra={
        <Space>
          <Button onClick={() => onRefresh?.()} disabled={loading}>
            刷新
          </Button>
        </Space>
      }
    >
      <Table
        rowKey="id"
        dataSource={contracts}
        columns={columns}
        loading={loading}
        pagination={false}
      />
    </Card>
  );
};

export default SignatureManager;

