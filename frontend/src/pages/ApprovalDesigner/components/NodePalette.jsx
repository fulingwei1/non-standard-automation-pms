/**
 * 节点工具栏组件
 * 提供可拖拽的节点类型
 */

import { Card, Space, Tooltip, Typography } from 'antd';
import { useDraggable } from '@dnd-kit/core';
import {
  Play,
  Square,
  UserCheck,
  Copy,
  GitBranch,
  Split,
} from 'lucide-react';

import { NODE_TYPES } from '../constants';

const { Text } = Typography;

// 图标映射
const iconMap = {
  Play,
  Square,
  UserCheck,
  Copy,
  GitBranch,
  Split,
};

// 可拖拽节点项
function DraggableNode({ type, config }) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `palette-${type}`,
    data: { type, isNew: true },
  });

  const Icon = iconMap[config.icon] || Square;

  return (
    <Tooltip title={config.description} placement="right">
      <div
        ref={setNodeRef}
        {...listeners}
        {...attributes}
        className={`
          flex items-center gap-2 p-3 rounded-lg cursor-grab
          border border-gray-200 bg-white
          hover:border-blue-400 hover:shadow-sm
          transition-all duration-200
          ${isDragging ? 'opacity-50 cursor-grabbing shadow-lg' : ''}
        `}
        style={{
          borderLeftWidth: 4,
          borderLeftColor: config.color,
        }}
      >
        <Icon size={18} color={config.color} />
        <Text className="text-sm">{config.label}</Text>
      </div>
    </Tooltip>
  );
}

// 节点分组
const nodeGroups = [
  {
    title: '流程控制',
    types: ['START', 'END', 'CONDITION', 'PARALLEL'],
  },
  {
    title: '审批节点',
    types: ['APPROVAL', 'CC'],
  },
];

export function NodePalette() {
  return (
    <Card
      title="节点工具箱"
      size="small"
      className="w-56 h-full overflow-auto"
      styles={{ body: { padding: 12 } }}
    >
      <Space orientation="vertical" size={16} className="w-full">
        {(nodeGroups || []).map(group => (
          <div key={group.title}>
            <Text type="secondary" className="text-xs mb-2 block">
              {group.title}
            </Text>
            <Space orientation="vertical" size={8} className="w-full">
              {(group.types || []).map(type => {
                const config = NODE_TYPES[type];
                if (!config) return null;
                return (
                  <DraggableNode
                    key={type}
                    type={type}
                    config={config}
                  />
                );
              })}
            </Space>
          </div>
        ))}
      </Space>
    </Card>
  );
}

export default NodePalette;
