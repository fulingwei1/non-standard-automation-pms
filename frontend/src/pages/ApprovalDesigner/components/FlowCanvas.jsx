/**
 * 流程画布组件
 * 显示和编辑审批流程
 */

import { useCallback, useRef, useState } from 'react';
import { useDroppable } from '@dnd-kit/core';
import {
  Play,
  Square,
  UserCheck,
  Copy,
  GitBranch,
  Split,
  Trash2,
} from 'lucide-react';
import { Button, Tooltip } from 'antd';

import { NODE_TYPES, CANVAS_CONFIG } from '../constants';

// 图标映射
const iconMap = {
  Play,
  Square,
  UserCheck,
  Copy,
  GitBranch,
  Split,
};

// 单个节点组件
function FlowNode({
  node,
  isSelected,
  onSelect,
  onDelete,
  onStartConnect,
  onEndConnect,
  isConnecting,
  connectingFrom,
}) {
  const config = NODE_TYPES[node.type];
  const Icon = iconMap[config?.icon] || Square;

  const handleClick = (e) => {
    e.stopPropagation();
    if (isConnecting && connectingFrom !== node.id) {
      onEndConnect(node.id);
    } else {
      onSelect(node.id);
    }
  };

  const handleConnectStart = (e) => {
    e.stopPropagation();
    onStartConnect(node.id);
  };

  return (
    <div
      className={`
        absolute cursor-pointer select-none
        transition-all duration-200
        ${isSelected ? 'z-10' : 'z-0'}
      `}
      style={{
        left: node.position.x,
        top: node.position.y,
        width: CANVAS_CONFIG.nodeWidth,
      }}
      onClick={handleClick}
    >
      {/* 节点主体 */}
      <div
        className={`
          relative flex items-center gap-3 p-4 rounded-xl
          bg-white border-2 shadow-sm
          hover:shadow-md
          ${isSelected ? 'border-blue-500 shadow-md ring-2 ring-blue-200' : 'border-gray-200'}
          ${isConnecting && connectingFrom !== node.id ? 'border-dashed border-green-500' : ''}
        `}
        style={{
          minHeight: CANVAS_CONFIG.nodeHeight,
          borderLeftWidth: 4,
          borderLeftColor: config?.color || '#8c8c8c',
        }}
      >
        {/* 图标 */}
        <div
          className="flex items-center justify-center w-10 h-10 rounded-lg"
          style={{ backgroundColor: `${config?.color}20` }}
        >
          <Icon size={20} color={config?.color} />
        </div>

        {/* 内容 */}
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 truncate">
            {node.data.label}
          </div>
          {node.type === 'APPROVAL' && node.data.approverType && (
            <div className="text-xs text-gray-500 mt-0.5">
              {node.data.approvalMode === 'AND_SIGN' && '会签 · '}
              {node.data.approvalMode === 'OR_SIGN' && '或签 · '}
              {node.data.approverType === 'DIRECT_MANAGER' && '直属上级'}
              {node.data.approverType === 'DEPARTMENT_HEAD' && '部门主管'}
              {node.data.approverType === 'ROLE' && '指定角色'}
              {node.data.approverType === 'FIXED_USER' && '指定用户'}
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        {isSelected && node.type !== 'START' && node.type !== 'END' && (
          <div className="absolute -top-2 -right-2 flex gap-1">
            <Tooltip title="删除">
              <Button
                type="primary"
                danger
                size="small"
                icon={<Trash2 size={12} />}
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(node.id);
                }}
                className="!w-6 !h-6 !min-w-0 !p-0"
              />
            </Tooltip>
          </div>
        )}

        {/* 连接点 - 输入 */}
        {node.type !== 'START' && (
          <div
            className={`
              absolute -top-2 left-1/2 -translate-x-1/2
              w-4 h-4 rounded-full border-2 bg-white
              ${isConnecting ? 'border-green-500 bg-green-100' : 'border-gray-300'}
              hover:border-blue-500 hover:bg-blue-100
              cursor-pointer
            `}
            onClick={handleClick}
          />
        )}

        {/* 连接点 - 输出 */}
        {node.type !== 'END' && (
          <div
            className={`
              absolute -bottom-2 left-1/2 -translate-x-1/2
              w-4 h-4 rounded-full border-2 bg-white
              ${connectingFrom === node.id ? 'border-blue-500 bg-blue-500' : 'border-gray-300'}
              hover:border-blue-500 hover:bg-blue-100
              cursor-pointer
            `}
            onClick={handleConnectStart}
          />
        )}
      </div>
    </div>
  );
}

// 连线组件
function FlowEdge({ edge, nodes, isSelected, onSelect, onDelete }) {
  const sourceNode = nodes.find(n => n.id === edge.source);
  const targetNode = nodes.find(n => n.id === edge.target);

  if (!sourceNode || !targetNode) return null;

  // 计算连线坐标
  const sourceX = sourceNode.position.x + CANVAS_CONFIG.nodeWidth / 2;
  const sourceY = sourceNode.position.y + CANVAS_CONFIG.nodeHeight;
  const targetX = targetNode.position.x + CANVAS_CONFIG.nodeWidth / 2;
  const targetY = targetNode.position.y;

  // 使用贝塞尔曲线
  const midY = (sourceY + targetY) / 2;
  const path = `M ${sourceX} ${sourceY} C ${sourceX} ${midY}, ${targetX} ${midY}, ${targetX} ${targetY}`;

  return (
    <g className="cursor-pointer" onClick={() => onSelect(edge.id)}>
      {/* 点击区域（更宽） */}
      <path
        d={path}
        fill="none"
        stroke="transparent"
        strokeWidth={20}
      />
      {/* 可见线条 */}
      <path
        d={path}
        fill="none"
        stroke={isSelected ? '#1677ff' : '#d9d9d9'}
        strokeWidth={isSelected ? 3 : 2}
        className="transition-all duration-200"
      />
      {/* 箭头 */}
      <polygon
        points={`${targetX},${targetY - 2} ${targetX - 6},${targetY - 10} ${targetX + 6},${targetY - 10}`}
        fill={isSelected ? '#1677ff' : '#d9d9d9'}
      />
      {/* 标签 */}
      {edge.label && (
        <text
          x={(sourceX + targetX) / 2}
          y={midY - 10}
          textAnchor="middle"
          className="text-xs fill-gray-500"
        >
          {edge.label}
        </text>
      )}
      {/* 删除按钮 */}
      {isSelected && (
        <g
          transform={`translate(${(sourceX + targetX) / 2 - 10}, ${midY - 10})`}
          onClick={(e) => {
            e.stopPropagation();
            onDelete(edge.id);
          }}
        >
          <circle r={10} fill="#ff4d4f" className="cursor-pointer" />
          <text
            textAnchor="middle"
            dominantBaseline="middle"
            fill="white"
            className="text-xs"
          >
            ×
          </text>
        </g>
      )}
    </g>
  );
}

// 正在绘制的连线
function DrawingEdge({ fromNode, mousePosition }) {
  if (!fromNode) return null;

  const sourceX = fromNode.position.x + CANVAS_CONFIG.nodeWidth / 2;
  const sourceY = fromNode.position.y + CANVAS_CONFIG.nodeHeight;
  const targetX = mousePosition.x;
  const targetY = mousePosition.y;

  const midY = (sourceY + targetY) / 2;
  const path = `M ${sourceX} ${sourceY} C ${sourceX} ${midY}, ${targetX} ${midY}, ${targetX} ${targetY}`;

  return (
    <path
      d={path}
      fill="none"
      stroke="#1677ff"
      strokeWidth={2}
      strokeDasharray="5,5"
      className="pointer-events-none"
    />
  );
}

export function FlowCanvas({
  flow,
  selectedNodeId,
  selectedEdgeId,
  onSelectNode,
  onSelectEdge,
  onAddNode: _onAddNode,
  onDeleteNode,
  onDeleteEdge,
  onAddEdge,
  onMoveNode,
  zoom = 1,
}) {
  const canvasRef = useRef(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectingFrom, setConnectingFrom] = useState(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [dragOffset, _setDragOffset] = useState({ x: 0, y: 0 });
  const [draggingNodeId, setDraggingNodeId] = useState(null);

  // 设置为可放置区域
  const { setNodeRef, isOver } = useDroppable({
    id: 'flow-canvas',
  });

  // 处理画布点击（取消选择）
  const handleCanvasClick = useCallback(() => {
    onSelectNode(null);
    onSelectEdge(null);
    if (isConnecting) {
      setIsConnecting(false);
      setConnectingFrom(null);
    }
  }, [onSelectNode, onSelectEdge, isConnecting]);

  // 开始连接
  const handleStartConnect = useCallback((nodeId) => {
    setIsConnecting(true);
    setConnectingFrom(nodeId);
  }, []);

  // 结束连接
  const handleEndConnect = useCallback((targetNodeId) => {
    if (connectingFrom && targetNodeId !== connectingFrom) {
      onAddEdge(connectingFrom, targetNodeId);
    }
    setIsConnecting(false);
    setConnectingFrom(null);
  }, [connectingFrom, onAddEdge]);

  // 鼠标移动
  const handleMouseMove = useCallback((e) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / zoom;
    const y = (e.clientY - rect.top) / zoom;
    setMousePosition({ x, y });

    // 处理节点拖拽
    if (draggingNodeId) {
      onMoveNode(draggingNodeId, {
        x: x - dragOffset.x,
        y: y - dragOffset.y,
      });
    }
  }, [zoom, draggingNodeId, dragOffset, onMoveNode]);

  // 结束拖拽节点
  const handleMouseUp = useCallback(() => {
    setDraggingNodeId(null);
  }, []);

  const connectingFromNode = connectingFrom
    ? flow.nodes.find(n => n.id === connectingFrom)
    : null;

  return (
    <div
      ref={(node) => {
        canvasRef.current = node;
        setNodeRef(node);
      }}
      className={`
        relative w-full h-full overflow-auto
        bg-gray-50 bg-[length:20px_20px]
        ${isOver ? 'bg-blue-50' : ''}
      `}
      style={{
        backgroundImage: `
          linear-gradient(to right, #e5e7eb 1px, transparent 1px),
          linear-gradient(to bottom, #e5e7eb 1px, transparent 1px)
        `,
        minHeight: 600,
      }}
      onClick={handleCanvasClick}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* 缩放容器 */}
      <div
        style={{
          transform: `scale(${zoom})`,
          transformOrigin: 'top left',
          minWidth: 1200,
          minHeight: 800,
        }}
      >
        {/* SVG层 - 绘制连线 */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          style={{ minWidth: 1200, minHeight: 800 }}
        >
          <g className="pointer-events-auto">
            {/* 已有连线 */}
            {flow.edges.map(edge => (
              <FlowEdge
                key={edge.id}
                edge={edge}
                nodes={flow.nodes}
                isSelected={edge.id === selectedEdgeId}
                onSelect={onSelectEdge}
                onDelete={onDeleteEdge}
              />
            ))}
            {/* 正在绘制的连线 */}
            {isConnecting && (
              <DrawingEdge
                fromNode={connectingFromNode}
                mousePosition={mousePosition}
              />
            )}
          </g>
        </svg>

        {/* 节点层 */}
        {flow.nodes.map(node => (
          <FlowNode
            key={node.id}
            node={node}
            isSelected={node.id === selectedNodeId}
            onSelect={onSelectNode}
            onDelete={onDeleteNode}
            onStartConnect={handleStartConnect}
            onEndConnect={handleEndConnect}
            isConnecting={isConnecting}
            connectingFrom={connectingFrom}
          />
        ))}
      </div>
    </div>
  );
}

export default FlowCanvas;
