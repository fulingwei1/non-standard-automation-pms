/**
 * 节点配置面板组件
 * 用于配置选中节点的属性
 */

import { useCallback } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Switch,
  InputNumber,
  Space,
  Typography,
  Divider,
  Tag,
  Empty,
} from 'antd';
import {
  UserCheck,
  Settings,
  Clock,
  Users,
  AlertTriangle,
} from 'lucide-react';

import {
  NODE_TYPES,
  APPROVAL_MODES,
  APPROVER_TYPES,
  TIMEOUT_ACTIONS,
  REJECT_TARGETS,
} from '../constants';

const { Text, Title } = Typography;
const { TextArea } = Input;

// 审批节点配置
function ApprovalNodeConfig({ node, onChange }) {
  const handleChange = useCallback((field, value) => {
    onChange(node.id, {
      data: {
        ...node.data,
        [field]: value,
      },
    });
  }, [node, onChange]);

  return (
    <Space direction="vertical" size={16} className="w-full">
      {/* 基本信息 */}
      <div>
        <Text type="secondary" className="text-xs mb-2 block">基本信息</Text>
        <Form.Item label="节点名称" className="mb-3">
          <Input
            value={node.data.label}
            onChange={(e) => handleChange('label', e.target.value)}
            placeholder="请输入节点名称"
          />
        </Form.Item>
      </div>

      <Divider className="my-2" />

      {/* 审批模式 */}
      <div>
        <Text type="secondary" className="text-xs mb-2 block">
          <Users size={12} className="inline mr-1" />
          审批模式
        </Text>
        <Form.Item className="mb-3">
          <Select
            value={node.data.approvalMode}
            onChange={(value) => handleChange('approvalMode', value)}
            options={Object.values(APPROVAL_MODES).map(m => ({
              value: m.value,
              label: (
                <Space>
                  <span>{m.label}</span>
                  <Text type="secondary" className="text-xs">{m.description}</Text>
                </Space>
              ),
            }))}
          />
        </Form.Item>
      </div>

      {/* 审批人类型 */}
      <div>
        <Text type="secondary" className="text-xs mb-2 block">
          <UserCheck size={12} className="inline mr-1" />
          审批人
        </Text>
        <Form.Item className="mb-3">
          <Select
            value={node.data.approverType}
            onChange={(value) => handleChange('approverType', value)}
            options={Object.values(APPROVER_TYPES).map(t => ({
              value: t.value,
              label: t.label,
            }))}
          />
        </Form.Item>

        {/* 根据审批人类型显示额外配置 */}
        {node.data.approverType === 'ROLE' && (
          <Form.Item label="选择角色" className="mb-3">
            <Select
              mode="multiple"
              placeholder="请选择角色"
              value={node.data.approverConfig?.roles || []}
              onChange={(value) => handleChange('approverConfig', {
                ...node.data.approverConfig,
                roles: value,
              })}
              options={[
                { value: 'SALES_MANAGER', label: '销售经理' },
                { value: 'SALES_DIRECTOR', label: '销售总监' },
                { value: 'FINANCE_MANAGER', label: '财务经理' },
                { value: 'HR_DIRECTOR', label: 'HR总监' },
                { value: 'GM', label: '总经理' },
              ]}
            />
          </Form.Item>
        )}

        {node.data.approverType === 'MULTI_DEPT' && (
          <Form.Item label="选择部门" className="mb-3">
            <Select
              mode="multiple"
              placeholder="请选择评估部门"
              value={node.data.approverConfig?.departments || []}
              onChange={(value) => handleChange('approverConfig', {
                ...node.data.approverConfig,
                departments: value,
              })}
              options={[
                { value: '工程部', label: '工程部' },
                { value: '采购部', label: '采购部' },
                { value: '生产部', label: '生产部' },
                { value: '质量部', label: '质量部' },
                { value: '财务部', label: '财务部' },
              ]}
            />
          </Form.Item>
        )}
      </div>

      <Divider className="my-2" />

      {/* 超时设置 */}
      <div>
        <Text type="secondary" className="text-xs mb-2 block">
          <Clock size={12} className="inline mr-1" />
          超时设置
        </Text>
        <Space className="w-full">
          <Form.Item label="超时时间" className="mb-0 flex-1">
            <InputNumber
              value={node.data.timeoutHours}
              onChange={(value) => handleChange('timeoutHours', value)}
              min={1}
              max={720}
              placeholder="小时"
              className="w-full"
              addonAfter="小时"
            />
          </Form.Item>
          <Form.Item label="超时操作" className="mb-0 flex-1">
            <Select
              value={node.data.timeoutAction}
              onChange={(value) => handleChange('timeoutAction', value)}
              options={Object.values(TIMEOUT_ACTIONS).map(a => ({
                value: a.value,
                label: <Tag color={a.color}>{a.label}</Tag>,
              }))}
            />
          </Form.Item>
        </Space>
      </div>

      <Divider className="my-2" />

      {/* 行为配置 */}
      <div>
        <Text type="secondary" className="text-xs mb-2 block">
          <Settings size={12} className="inline mr-1" />
          行为配置
        </Text>
        <Space direction="vertical" className="w-full">
          <div className="flex justify-between items-center">
            <Text>允许加签</Text>
            <Switch
              size="small"
              checked={node.data.canAddApprover}
              onChange={(checked) => handleChange('canAddApprover', checked)}
            />
          </div>
          <div className="flex justify-between items-center">
            <Text>允许转审</Text>
            <Switch
              size="small"
              checked={node.data.canTransfer}
              onChange={(checked) => handleChange('canTransfer', checked)}
            />
          </div>
          <div className="flex justify-between items-center">
            <Text>允许委托</Text>
            <Switch
              size="small"
              checked={node.data.canDelegate}
              onChange={(checked) => handleChange('canDelegate', checked)}
            />
          </div>
        </Space>
      </div>

      <Divider className="my-2" />

      {/* 驳回设置 */}
      <div>
        <Text type="secondary" className="text-xs mb-2 block">
          <AlertTriangle size={12} className="inline mr-1" />
          驳回设置
        </Text>
        <Form.Item label="驳回目标" className="mb-0">
          <Select
            value={node.data.canRejectTo}
            onChange={(value) => handleChange('canRejectTo', value)}
            options={Object.values(REJECT_TARGETS).map(t => ({
              value: t.value,
              label: t.label,
            }))}
          />
        </Form.Item>
      </div>
    </Space>
  );
}

// 抄送节点配置
function CcNodeConfig({ node, onChange }) {
  const handleChange = useCallback((field, value) => {
    onChange(node.id, {
      data: {
        ...node.data,
        [field]: value,
      },
    });
  }, [node, onChange]);

  return (
    <Space direction="vertical" size={16} className="w-full">
      <Form.Item label="节点名称" className="mb-3">
        <Input
          value={node.data.label}
          onChange={(e) => handleChange('label', e.target.value)}
          placeholder="请输入节点名称"
        />
      </Form.Item>

      <Form.Item label="抄送角色" className="mb-3">
        <Select
          mode="multiple"
          placeholder="选择抄送角色"
          value={node.data.ccRoles || []}
          onChange={(value) => handleChange('ccRoles', value)}
          options={[
            { value: 'PROJECT_MANAGER', label: '项目经理' },
            { value: 'DEPT_HEAD', label: '部门主管' },
            { value: 'FINANCE', label: '财务' },
          ]}
        />
      </Form.Item>
    </Space>
  );
}

// 条件节点配置
function ConditionNodeConfig({ node, onChange }) {
  const handleChange = useCallback((field, value) => {
    onChange(node.id, {
      data: {
        ...node.data,
        [field]: value,
      },
    });
  }, [node, onChange]);

  return (
    <Space direction="vertical" size={16} className="w-full">
      <Form.Item label="节点名称" className="mb-3">
        <Input
          value={node.data.label}
          onChange={(e) => handleChange('label', e.target.value)}
          placeholder="请输入节点名称"
        />
      </Form.Item>

      <div className="bg-yellow-50 p-3 rounded-lg">
        <Text type="secondary" className="text-xs">
          条件配置需要在"路由规则"标签页中设置。
          条件节点会根据表单数据自动选择分支。
        </Text>
      </div>
    </Space>
  );
}

// 基础节点配置（开始/结束）
function BasicNodeConfig({ node, onChange }) {
  const handleChange = useCallback((field, value) => {
    onChange(node.id, {
      data: {
        ...node.data,
        [field]: value,
      },
    });
  }, [node, onChange]);

  return (
    <Space direction="vertical" size={16} className="w-full">
      <Form.Item label="节点名称" className="mb-3">
        <Input
          value={node.data.label}
          onChange={(e) => handleChange('label', e.target.value)}
          placeholder="请输入节点名称"
          disabled={node.type === 'START' || node.type === 'END'}
        />
      </Form.Item>

      <div className="bg-gray-50 p-3 rounded-lg">
        <Text type="secondary" className="text-xs">
          {node.type === 'START' && '开始节点是流程的入口，无需额外配置。'}
          {node.type === 'END' && '结束节点是流程的出口，无需额外配置。'}
        </Text>
      </div>
    </Space>
  );
}

export function NodeConfig({ node, onChange }) {
  if (!node) {
    return (
      <Card title="节点配置" size="small" className="w-72 h-full">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="请选择一个节点进行配置"
        />
      </Card>
    );
  }

  const config = NODE_TYPES[node.type];

  return (
    <Card
      title={
        <Space>
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: config?.color }}
          />
          <span>{config?.label || '节点'}配置</span>
        </Space>
      }
      size="small"
      className="w-72 h-full overflow-auto"
      styles={{ body: { padding: 12 } }}
    >
      {node.type === 'APPROVAL' && (
        <ApprovalNodeConfig node={node} onChange={onChange} />
      )}
      {node.type === 'CC' && (
        <CcNodeConfig node={node} onChange={onChange} />
      )}
      {node.type === 'CONDITION' && (
        <ConditionNodeConfig node={node} onChange={onChange} />
      )}
      {(node.type === 'START' || node.type === 'END' || node.type === 'PARALLEL') && (
        <BasicNodeConfig node={node} onChange={onChange} />
      )}
    </Card>
  );
}

export default NodeConfig;
