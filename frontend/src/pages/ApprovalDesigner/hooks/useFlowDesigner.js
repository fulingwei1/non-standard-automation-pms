/**
 * 审批流程设计器 Hook
 * 管理流程设计器的状态和操作
 */

import { useCallback, useState } from 'react';
import { message } from 'antd';
import { NODE_TYPES } from '../constants';

// 生成唯一ID
const generateId = () => `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// 初始流程状态
const createInitialFlow = () => ({
  id: null,
  name: '',
  description: '',
  templateId: null,
  version: 1,
  nodes: [
    {
      id: 'start',
      type: 'START',
      position: { x: 400, y: 50 },
      data: { label: '开始' },
    },
    {
      id: 'end',
      type: 'END',
      position: { x: 400, y: 400 },
      data: { label: '结束' },
    },
  ],
  edges: [],
  routingRules: [],
});

export function useFlowDesigner() {
  // 流程数据
  const [flow, setFlow] = useState(createInitialFlow);

  // 选中的节点/边
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState(null);

  // UI状态
  const [zoom, setZoom] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // 历史记录（用于撤销/重做）
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // 保存到历史
  const saveToHistory = useCallback((newFlow) => {
    setHistory(prev => {
      const newHistory = prev.slice(0, historyIndex + 1);
      newHistory.push(JSON.stringify(newFlow));
      return newHistory.slice(-50); // 最多保留50条历史
    });
    setHistoryIndex(prev => Math.min(prev + 1, 49));
  }, [historyIndex]);

  // 添加节点
  const addNode = useCallback((type, position) => {
    const nodeConfig = NODE_TYPES[type];
    if (!nodeConfig) {
      message.error(`未知节点类型: ${type}`);
      return null;
    }

    // 检查节点数量限制
    if (nodeConfig.maxCount) {
      const existingCount = flow.nodes.filter(n => n.type === type).length;
      if (existingCount >= nodeConfig.maxCount) {
        message.warning(`${nodeConfig.label}节点最多只能有${nodeConfig.maxCount}个`);
        return null;
      }
    }

    const newNode = {
      id: generateId(),
      type,
      position,
      data: {
        label: nodeConfig.label,
        // 审批节点默认配置
        ...(type === 'APPROVAL' && {
          approvalMode: 'SINGLE',
          approverType: 'DIRECT_MANAGER',
          approverConfig: {},
          canAddApprover: true,
          canTransfer: true,
          canDelegate: true,
          canRejectTo: 'START',
          timeoutHours: null,
          timeoutAction: 'REMIND',
        }),
        // 条件节点默认配置
        ...(type === 'CONDITION' && {
          conditions: { operator: 'AND', items: [] },
          branches: [],
        }),
        // 抄送节点默认配置
        ...(type === 'CC' && {
          ccUsers: [],
          ccRoles: [],
        }),
      },
    };

    setFlow(prev => {
      const newFlow = {
        ...prev,
        nodes: [...prev.nodes, newNode],
      };
      saveToHistory(newFlow);
      return newFlow;
    });

    setSelectedNodeId(newNode.id);
    return newNode;
  }, [flow.nodes, saveToHistory]);

  // 更新节点
  const updateNode = useCallback((nodeId, updates) => {
    setFlow(prev => {
      const newFlow = {
        ...prev,
        nodes: prev.nodes.map(node =>
          node.id === nodeId
            ? { ...node, ...updates, data: { ...node.data, ...updates.data } }
            : node
        ),
      };
      saveToHistory(newFlow);
      return newFlow;
    });
  }, [saveToHistory]);

  // 删除节点
  const deleteNode = useCallback((nodeId) => {
    const node = flow.nodes.find(n => n.id === nodeId);
    if (!node) return;

    // 不允许删除开始和结束节点
    if (node.type === 'START' || node.type === 'END') {
      message.warning('不能删除开始或结束节点');
      return;
    }

    setFlow(prev => {
      const newFlow = {
        ...prev,
        nodes: prev.nodes.filter(n => n.id !== nodeId),
        edges: prev.edges.filter(e => e.source !== nodeId && e.target !== nodeId),
      };
      saveToHistory(newFlow);
      return newFlow;
    });

    if (selectedNodeId === nodeId) {
      setSelectedNodeId(null);
    }
  }, [flow.nodes, selectedNodeId, saveToHistory]);

  // 移动节点
  const moveNode = useCallback((nodeId, position) => {
    setFlow(prev => ({
      ...prev,
      nodes: prev.nodes.map(node =>
        node.id === nodeId ? { ...node, position } : node
      ),
    }));
  }, []);

  // 添加连线
  const addEdge = useCallback((source, target, label = '') => {
    // 检查是否已存在相同连线
    const exists = flow.edges.some(e => e.source === source && e.target === target);
    if (exists) {
      message.warning('连线已存在');
      return null;
    }

    // 不允许自连接
    if (source === target) {
      message.warning('不能连接到自身');
      return null;
    }

    const newEdge = {
      id: `edge_${source}_${target}`,
      source,
      target,
      label,
    };

    setFlow(prev => {
      const newFlow = {
        ...prev,
        edges: [...prev.edges, newEdge],
      };
      saveToHistory(newFlow);
      return newFlow;
    });

    return newEdge;
  }, [flow.edges, saveToHistory]);

  // 删除连线
  const deleteEdge = useCallback((edgeId) => {
    setFlow(prev => {
      const newFlow = {
        ...prev,
        edges: prev.edges.filter(e => e.id !== edgeId),
      };
      saveToHistory(newFlow);
      return newFlow;
    });

    if (selectedEdgeId === edgeId) {
      setSelectedEdgeId(null);
    }
  }, [selectedEdgeId, saveToHistory]);

  // 更新路由规则
  const updateRoutingRules = useCallback((rules) => {
    setFlow(prev => {
      const newFlow = {
        ...prev,
        routingRules: rules,
      };
      saveToHistory(newFlow);
      return newFlow;
    });
  }, [saveToHistory]);

  // 撤销
  const undo = useCallback(() => {
    if (historyIndex > 0) {
      setHistoryIndex(prev => prev - 1);
      setFlow(JSON.parse(history[historyIndex - 1]));
    }
  }, [history, historyIndex]);

  // 重做
  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(prev => prev + 1);
      setFlow(JSON.parse(history[historyIndex + 1]));
    }
  }, [history, historyIndex]);

  // 加载流程
  const loadFlow = useCallback((flowData) => {
    setFlow(flowData);
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
    setHistory([JSON.stringify(flowData)]);
    setHistoryIndex(0);
  }, []);

  // 重置流程
  const resetFlow = useCallback(() => {
    const initial = createInitialFlow();
    setFlow(initial);
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
    setHistory([JSON.stringify(initial)]);
    setHistoryIndex(0);
  }, []);

  // 验证流程
  const validateFlow = useCallback(() => {
    const errors = [];
    const warnings = [];

    // 检查是否有开始节点
    const startNode = flow.nodes.find(n => n.type === 'START');
    if (!startNode) {
      errors.push('流程缺少开始节点');
    }

    // 检查是否有结束节点
    const endNode = flow.nodes.find(n => n.type === 'END');
    if (!endNode) {
      errors.push('流程缺少结束节点');
    }

    // 检查是否有审批节点
    const approvalNodes = flow.nodes.filter(n => n.type === 'APPROVAL');
    if (approvalNodes.length === 0) {
      warnings.push('流程没有审批节点');
    }

    // 检查节点是否都有连线
    flow.nodes.forEach(node => {
      if (node.type === 'START') {
        const hasOutgoing = flow.edges.some(e => e.source === node.id);
        if (!hasOutgoing) {
          errors.push('开始节点没有连接到任何节点');
        }
      } else if (node.type === 'END') {
        const hasIncoming = flow.edges.some(e => e.target === node.id);
        if (!hasIncoming) {
          errors.push('结束节点没有接收任何连线');
        }
      } else {
        const hasIncoming = flow.edges.some(e => e.target === node.id);
        const hasOutgoing = flow.edges.some(e => e.source === node.id);
        if (!hasIncoming) {
          warnings.push(`节点"${node.data.label}"没有接收连线`);
        }
        if (!hasOutgoing) {
          warnings.push(`节点"${node.data.label}"没有输出连线`);
        }
      }
    });

    // 检查审批节点配置
    approvalNodes.forEach(node => {
      if (!node.data.approverType) {
        errors.push(`审批节点"${node.data.label}"未配置审批人`);
      }
    });

    return { errors, warnings, isValid: errors.length === 0 };
  }, [flow]);

  // 导出为JSON
  const exportToJSON = useCallback(() => {
    return {
      ...flow,
      exportedAt: new Date().toISOString(),
    };
  }, [flow]);

  // 获取选中的节点
  const selectedNode = flow.nodes.find(n => n.id === selectedNodeId) || null;
  const selectedEdge = flow.edges.find(e => e.id === selectedEdgeId) || null;

  return {
    // 数据
    flow,
    selectedNode,
    selectedEdge,
    selectedNodeId,
    selectedEdgeId,

    // UI状态
    zoom,
    isDragging,
    isEditing,
    isSaving,
    canUndo: historyIndex > 0,
    canRedo: historyIndex < history.length - 1,

    // 节点操作
    addNode,
    updateNode,
    deleteNode,
    moveNode,

    // 连线操作
    addEdge,
    deleteEdge,

    // 选择操作
    setSelectedNodeId,
    setSelectedEdgeId,

    // UI操作
    setZoom,
    setIsDragging,
    setIsEditing,
    setIsSaving,

    // 路由规则
    updateRoutingRules,

    // 历史操作
    undo,
    redo,

    // 流程操作
    loadFlow,
    resetFlow,
    validateFlow,
    exportToJSON,
    setFlow,
  };
}

export default useFlowDesigner;
