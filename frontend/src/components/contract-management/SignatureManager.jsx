import { useMemo, useState } from 'react';
import { Card, Table, Tag, Space, Button, message } from 'antd';
import { CONTRACT_STATUS, SIGNATURE_STATUS } from '@/lib/constants/contractManagement';
import { signContract } from '@/services/contractService';

const SignatureManager = ({ contracts = [], loading = false, onRefresh, onSignComplete }) => {
  const [signingId, setSigningId] = useState(null);

  const handleSign = async (contract) => {
    if (!contract?.id) {
      return;
    }

    const today = new Date().toISOString().slice(0, 10);
    setSigningId(contract.id);

    try {
      const response = await signContract(contract.id, {
        signed_date: contract.signing_date || contract.signed_date || today,
        auto_create_project: false,
      });

      message.success(response?.message || '合同已签署，待发起PMO立项');
      onSignComplete?.(contract, response);
      await onRefresh?.();
    } catch (error) {
      const detail =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        error?.message ||
        '未知错误';
      message.error(`签署失败：${detail}`);
    } finally {
      setSigningId(null);
    }
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
              onClick={() => handleSign(record)}
            >
              确认签署
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
