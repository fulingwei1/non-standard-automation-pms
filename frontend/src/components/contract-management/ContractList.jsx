/**
 * Contract List Component
 * 合同列表组件（用于拆分后的 ContractManagement 页面）
 */

import { useMemo } from 'react';
import { Card, Table, Tag, Space, Button, Typography } from 'antd';
import {
  CONTRACT_TYPES,
  CONTRACT_STATUS,
  SIGNATURE_STATUS,
  RISK_LEVELS,
  TABLE_CONFIG,
  CHART_COLORS
} from '@/lib/constants/contractManagement';

const { Text } = Typography;

const formatCurrency = (value) => `¥${Number(value || 0).toLocaleString()}`;

const SIGNED_STATUSES = new Set(['signed', 'executing', 'completed']);

const getProjectStatus = (record) => {
  if (record.project_id) {
    return {
      label: '已立项',
      color: 'green',
      detail: `项目 ${record.project_code || record.project_id}`,
    };
  }

  if (record.signatureStatus === 'signed' && SIGNED_STATUSES.has(record.status)) {
    return {
      label: '待立项',
      color: 'orange',
      detail: '签约后需移交 PMO',
    };
  }

  return {
    label: '未签约',
    color: 'default',
    detail: '签约后可立项',
  };
};

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
            {formatCurrency(value)}
          </span>
        )
      },
      {
        title: '履约闭环',
        key: 'operations',
        width: 260,
        render: (_, record) => {
          const projectStatus = getProjectStatus(record);
          const operations = record.operations || {};
          const paymentPlanCount = Number(operations.paymentPlanCount || 0);
          const invoiceCount = Number(operations.invoiceCount || 0);
          const unpaidAmount = Number(operations.unpaidAmount || 0);
          const overdueCount = Number(operations.overdueCount || 0);

          return (
            <Space orientation="vertical" size={4}>
              <Space size={4} wrap>
                <Tag color={projectStatus.color}>{projectStatus.label}</Tag>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {projectStatus.detail}
                </Text>
              </Space>
              <Space size={4} wrap>
                <Tag color={paymentPlanCount > 0 ? 'blue' : 'default'}>
                  收款计划 {paymentPlanCount}期
                </Tag>
                <Tag color={invoiceCount > 0 ? 'cyan' : 'default'}>
                  已开票 {invoiceCount}张
                </Tag>
              </Space>
              <Space size={4} wrap>
                <Text type={unpaidAmount > 0 ? 'warning' : 'secondary'} style={{ fontSize: 12 }}>
                  待收 {formatCurrency(unpaidAmount)}
                </Text>
                {overdueCount > 0 && (
                  <Tag color="red">逾期 {overdueCount}笔</Tag>
                )}
              </Space>
            </Space>
          );
        }
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
        render: (_, record) => {
          const canCreateProject =
            !record.project_id &&
            record.signatureStatus === 'signed' &&
            ['signed', 'executing', 'completed'].includes(record.status);

          return (
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
              {canCreateProject && (
                <Button type="link" onClick={() => onCreateProject?.(record)}>
                  发起立项
                </Button>
              )}
            </Space>
          );
        }
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
