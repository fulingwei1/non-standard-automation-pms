/**
 * 条件构建器组件
 * 用于配置审批流程的路由规则
 */

import { useState } from 'react';
import {
  Card,
  Button,
  Select,
  Input,
  InputNumber,
  Space,
  Typography,
  Tag,
  List,
  Popconfirm,
  Empty,
  Collapse,
  Form,
} from 'antd';
import {
  Plus,
  Trash2,
  GitBranch,
  ChevronRight,
  Edit2,
  Copy,
} from 'lucide-react';

import { CONDITION_OPERATORS } from '../constants';

const { Text, Title } = Typography;

// 可用的条件字段
const CONDITION_FIELDS = {
  // 表单字段
  'form.amount': { label: '金额', type: 'number', group: '表单字段' },
  'form.leave_days': { label: '请假天数', type: 'number', group: '表单字段' },
  'form.urgency': { label: '紧急程度', type: 'select', options: ['NORMAL', 'URGENT', 'CRITICAL'], group: '表单字段' },

  // 业务实体字段
  'entity.gross_margin': { label: '毛利率(%)', type: 'number', group: '业务数据' },
  'entity.total_price': { label: '总价', type: 'number', group: '业务数据' },
  'entity.contract_amount': { label: '合同金额', type: 'number', group: '业务数据' },
  'entity.cost_impact': { label: '成本影响', type: 'number', group: '业务数据' },
  'entity.schedule_impact_days': { label: '工期影响(天)', type: 'number', group: '业务数据' },
  'entity.ecn_type': { label: 'ECN类型', type: 'select', options: ['DESIGN', 'MATERIAL', 'PROCESS', 'SPEC'], group: '业务数据' },
  'entity.priority': { label: '优先级', type: 'select', options: ['LOW', 'NORMAL', 'HIGH', 'URGENT'], group: '业务数据' },

  // 发起人属性
  'initiator.dept_id': { label: '发起人部门', type: 'select', options: [], group: '发起人' },
  'initiator.position_level': { label: '发起人职级', type: 'number', group: '发起人' },
};

// 单个条件项编辑
function ConditionItem({ item, index, onUpdate, onDelete }) {
  const fieldConfig = CONDITION_FIELDS[item.field];

  const renderValueInput = () => {
    const operator = item.op;

    if (operator === 'is_null') {
      return (
        <Select
          value={item.value}
          onChange={(v) => onUpdate(index, { ...item, value: v })}
          style={{ width: 100 }}
          options={[
            { value: true, label: '是' },
            { value: false, label: '否' },
          ]}
        />
      );
    }

    if (operator === 'between') {
      return (
        <Space>
          <InputNumber
            value={item.value?.[0]}
            onChange={(v) => onUpdate(index, { ...item, value: [v, item.value?.[1]] })}
            style={{ width: 80 }}
            placeholder="最小"
          />
          <Text type="secondary">至</Text>
          <InputNumber
            value={item.value?.[1]}
            onChange={(v) => onUpdate(index, { ...item, value: [item.value?.[0], v] })}
            style={{ width: 80 }}
            placeholder="最大"
          />
        </Space>
      );
    }

    if (operator === 'in' || operator === 'not_in') {
      if (fieldConfig?.type === 'select') {
        return (
          <Select
            mode="multiple"
            value={item.value || []}
            onChange={(v) => onUpdate(index, { ...item, value: v })}
            style={{ width: 200 }}
            options={fieldConfig.options?.map(o => ({ value: o, label: o }))}
          />
        );
      }
      return (
        <Input
          value={Array.isArray(item.value) ? item.value.join(',') : item.value}
          onChange={(e) => onUpdate(index, { ...item, value: e.target.value.split(',') })}
          style={{ width: 200 }}
          placeholder="多个值用逗号分隔"
        />
      );
    }

    if (fieldConfig?.type === 'number') {
      return (
        <InputNumber
          value={item.value}
          onChange={(v) => onUpdate(index, { ...item, value: v })}
          style={{ width: 120 }}
        />
      );
    }

    if (fieldConfig?.type === 'select') {
      return (
        <Select
          value={item.value}
          onChange={(v) => onUpdate(index, { ...item, value: v })}
          style={{ width: 150 }}
          options={fieldConfig.options?.map(o => ({ value: o, label: o }))}
        />
      );
    }

    return (
      <Input
        value={item.value}
        onChange={(e) => onUpdate(index, { ...item, value: e.target.value })}
        style={{ width: 150 }}
      />
    );
  };

  return (
    <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg mb-2">
      <Select
        value={item.field}
        onChange={(v) => onUpdate(index, { ...item, field: v })}
        style={{ width: 150 }}
        placeholder="选择字段"
        options={Object.entries(CONDITION_FIELDS).map(([key, config]) => ({
          value: key,
          label: config.label,
        }))}
      />
      <Select
        value={item.op}
        onChange={(v) => onUpdate(index, { ...item, op: v })}
        style={{ width: 120 }}
        options={Object.values(CONDITION_OPERATORS).map(o => ({
          value: o.value,
          label: o.label,
        }))}
      />
      {renderValueInput()}
      <Button
        type="text"
        danger
        size="small"
        icon={<Trash2 size={14} />}
        onClick={() => onDelete(index)}
      />
    </div>
  );
}

// 条件组编辑
function ConditionGroup({ conditions, onChange }) {
  const handleOperatorChange = (operator) => {
    onChange({ ...conditions, operator });
  };

  const handleItemUpdate = (index, item) => {
    const newItems = [...(conditions.items || [])];
    newItems[index] = item;
    onChange({ ...conditions, items: newItems });
  };

  const handleItemDelete = (index) => {
    const newItems = (conditions.items || []).filter((_, i) => i !== index);
    onChange({ ...conditions, items: newItems });
  };

  const handleAddItem = () => {
    const newItems = [...(conditions.items || []), { field: '', op: '==', value: '' }];
    onChange({ ...conditions, items: newItems });
  };

  return (
    <div className="border rounded-lg p-3">
      <div className="flex items-center gap-2 mb-3">
        <Text strong>条件组合:</Text>
        <Select
          value={conditions.operator || 'AND'}
          onChange={handleOperatorChange}
          style={{ width: 120 }}
          options={[
            { value: 'AND', label: '全部满足 (AND)' },
            { value: 'OR', label: '任一满足 (OR)' },
          ]}
        />
      </div>

      {(conditions.items || []).map((item, index) => (
        <ConditionItem
          key={index}
          item={item}
          index={index}
          onUpdate={handleItemUpdate}
          onDelete={handleItemDelete}
        />
      ))}

      <Button
        type="dashed"
        size="small"
        icon={<Plus size={14} />}
        onClick={handleAddItem}
        className="w-full mt-2"
      >
        添加条件
      </Button>
    </div>
  );
}

// 单条路由规则
function RoutingRule({ rule, index, flows, onUpdate, onDelete, onDuplicate }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card
      size="small"
      className="mb-3"
      title={
        <Space className="cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
          <ChevronRight
            size={16}
            className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}
          />
          <Text strong>{rule.name || `规则 ${index + 1}`}</Text>
          <Tag color="blue">优先级: {rule.order}</Tag>
        </Space>
      }
      extra={
        <Space>
          <Button
            type="text"
            size="small"
            icon={<Copy size={14} />}
            onClick={() => onDuplicate(index)}
          />
          <Popconfirm
            title="确定删除此规则？"
            onConfirm={() => onDelete(index)}
          >
            <Button
              type="text"
              danger
              size="small"
              icon={<Trash2 size={14} />}
            />
          </Popconfirm>
        </Space>
      }
    >
      {isExpanded && (
        <Space orientation="vertical" className="w-full" size={12}>
          <Form.Item label="规则名称" className="mb-0">
            <Input
              value={rule.name}
              onChange={(e) => onUpdate(index, { ...rule, name: e.target.value })}
              placeholder="请输入规则名称"
            />
          </Form.Item>

          <Form.Item label="优先级" className="mb-0">
            <InputNumber
              value={rule.order}
              onChange={(v) => onUpdate(index, { ...rule, order: v })}
              min={1}
              max={100}
              style={{ width: 100 }}
            />
          </Form.Item>

          <Form.Item label="匹配条件" className="mb-0">
            <ConditionGroup
              conditions={rule.conditions || { operator: 'AND', items: [] }}
              onChange={(conditions) => onUpdate(index, { ...rule, conditions })}
            />
          </Form.Item>

          <Form.Item label="匹配后使用流程" className="mb-0">
            <Select
              value={rule.flowId}
              onChange={(v) => onUpdate(index, { ...rule, flowId: v })}
              placeholder="选择目标流程"
              options={flows.map(f => ({
                value: f.id,
                label: f.name,
              }))}
            />
          </Form.Item>
        </Space>
      )}
    </Card>
  );
}

export function ConditionBuilder({ rules = [], flows = [], onChange }) {
  const handleAddRule = () => {
    const newRule = {
      id: `rule_${Date.now()}`,
      name: `规则 ${rules.length + 1}`,
      order: rules.length + 1,
      conditions: { operator: 'AND', items: [] },
      flowId: null,
      isActive: true,
    };
    onChange([...rules, newRule]);
  };

  const handleUpdateRule = (index, rule) => {
    const newRules = [...rules];
    newRules[index] = rule;
    onChange(newRules);
  };

  const handleDeleteRule = (index) => {
    onChange(rules.filter((_, i) => i !== index));
  };

  const handleDuplicateRule = (index) => {
    const rule = rules[index];
    const newRule = {
      ...rule,
      id: `rule_${Date.now()}`,
      name: `${rule.name} (副本)`,
      order: rules.length + 1,
    };
    onChange([...rules, newRule]);
  };

  return (
    <Card
      title={
        <Space>
          <GitBranch size={16} />
          路由规则配置
        </Space>
      }
      extra={
        <Button
          type="primary"
          size="small"
          icon={<Plus size={14} />}
          onClick={handleAddRule}
        >
          添加规则
        </Button>
      }
    >
      <div className="mb-4 p-3 bg-blue-50 rounded-lg">
        <Text type="secondary" className="text-sm">
          路由规则按优先级从小到大匹配。当表单数据满足某条规则的条件时，
          将使用该规则指定的审批流程。如果没有规则匹配，将使用默认流程。
        </Text>
      </div>

      {rules.length === 0 ? (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无路由规则，点击上方按钮添加"
        />
      ) : (
        <div>
          {rules
            .sort((a, b) => a.order - b.order)
            .map((rule, index) => (
              <RoutingRule
                key={rule.id}
                rule={rule}
                index={index}
                flows={flows}
                onUpdate={handleUpdateRule}
                onDelete={handleDeleteRule}
                onDuplicate={handleDuplicateRule}
              />
            ))}
        </div>
      )}
    </Card>
  );
}

export default ConditionBuilder;
