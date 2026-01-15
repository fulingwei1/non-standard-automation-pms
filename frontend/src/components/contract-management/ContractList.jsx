/**
 * Contract List Component
 * 合同列表组件（用于拆分后的 ContractManagement 页面）
 */

import React, { useMemo } from 'react';
import { Card, Table, Tag, Space, Button, Typography } from 'antd';
import {
  CONTRACT_TYPES,
  CONTRACT_STATUS,
  SIGNATURE_STATUS,
  RISK_LEVELS,
  TABLE_CONFIG,
  CHART_COLORS
} from './contractManagementConstants';

const { Text } = Typography;

const ContractList = ({
  contracts = [],
  loading = false,
  onEdit,
  onDelete,
  onSign,
  onCreateProject
}) => {
  const columns = useMemo(() => {
    return [
      {
        title: '合同信息',
        key: 'info',
        render: (_, record) => {
          const typeConfig = CONTRACT_TYPES[record.type?.toUpperCase()];

          return (
            <div>
              <div style={{ fontWeight: 600 }}>
                {record.title || record.contract_no || `合同-${record.id}`}
              </div>
              <div style={{ marginTop: 4, fontSize: 12, color: '#666' }}>
                <Tag color={typeConfig?.color}>{typeConfig?.label || record.type || '-'}</Tag>
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  {record.clientName || record.client_name || '-'}
                </Text>
              </div>
            </div>
          );
        }
      },
      {
        title: '状态',
        key: 'status',
        width: 160,
        render: (_, record) => {
          const statusConfig = CONTRACT_STATUS[record.status?.toUpperCase()];
          const signatureConfig = SIGNATURE_STATUS[record.signatureStatus?.toUpperCase()];

          return (
            <div>
              <Tag color={statusConfig?.color}>{statusConfig?.label || record.status || '-'}</Tag>
              <div style={{ marginTop: 4 }}>
                <Tag color={signatureConfig?.color}>
                  {signatureConfig?.label || record.signatureStatus || '-'}
                </Tag>
              </div>
            </div>
          );
        }
      },
      {
        title: '金额',
        dataIndex: 'value',
        key: 'value',
        width: 140,
        render: (value) => (
          <span style={{ fontWeight: 600, color: CHART_COLORS.POSITIVE }}>
            ¥{Number(value || 0).toLocaleString()}
          </span>
        )
      },
      {
        title: '风险',
        dataIndex: 'riskLevel',
        key: 'riskLevel',
        width: 120,
        render: (riskLevel) => {
          const config = RISK_LEVELS[riskLevel?.toUpperCase()];
          return <Tag color={config?.color}>{config?.label || riskLevel || '-'}</Tag>;
        }
      },
      {
        title: '操作',
        key: 'actions',
        width: 260,
        render: (_, record) => (
          <Space>
            <Button type="link" onClick={() => onEdit?.(record)}>
              编辑
            </Button>
            <Button type="link" danger onClick={() => onDelete?.(record.id)}>
              删除
            </Button>
            {record.signatureStatus === 'pending' && (
              <Button type="link" onClick={() => onSign?.(record)}>
                签署
              </Button>
            )}
            {record.status === 'signed' && (
              <Button type="link" onClick={() => onCreateProject?.(record)}>
                创建项目
              </Button>
            )}
          </Space>
        )
      }
    ];
  }, [onCreateProject, onDelete, onEdit, onSign]);

  return (
    <Card>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={contracts}
        loading={loading}
        {...TABLE_CONFIG}
      />
    </Card>
  );
};

export default ContractList;

