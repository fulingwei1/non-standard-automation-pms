/**
 * 快捷操作组件 (Quick Actions)
 *
 * 提供常用操作的快捷入口
 */

import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Plus,
  FileText,
  Clock,
  Search,
  Settings,
  Briefcase,
  Users,
  Package,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { cn } from '../../../lib/utils';

// 默认快捷操作
const defaultActions = [
  { id: 'new-project', icon: Briefcase, label: '新建项目', path: '/projects/new', color: 'bg-blue-500' },
  { id: 'timesheet', icon: Clock, label: '填报工时', path: '/timesheet', color: 'bg-green-500' },
  { id: 'new-task', icon: Plus, label: '创建任务', path: '/progress-tracking/tasks/new', color: 'bg-purple-500' },
  { id: 'search', icon: Search, label: '全局搜索', path: '/search', color: 'bg-orange-500' },
];

// 角色对应的快捷操作
const roleActions = {
  sales: [
    { id: 'new-lead', icon: Users, label: '新建线索', path: '/leads/new', color: 'bg-blue-500' },
    { id: 'new-quote', icon: FileText, label: '创建报价', path: '/quotes/new', color: 'bg-green-500' },
    { id: 'timesheet', icon: Clock, label: '填报工时', path: '/timesheet', color: 'bg-purple-500' },
    { id: 'customers', icon: Users, label: '客户管理', path: '/customers', color: 'bg-orange-500' },
  ],
  engineer: [
    { id: 'timesheet', icon: Clock, label: '填报工时', path: '/timesheet', color: 'bg-blue-500' },
    { id: 'my-tasks', icon: FileText, label: '我的任务', path: '/progress-tracking/tasks', color: 'bg-green-500' },
    { id: 'ecn', icon: FileText, label: 'ECN变更', path: '/ecn', color: 'bg-purple-500' },
    { id: 'knowledge', icon: Search, label: '知识库', path: '/knowledge-base', color: 'bg-orange-500' },
  ],
  procurement: [
    { id: 'new-order', icon: Package, label: '新建采购单', path: '/purchases/new', color: 'bg-blue-500' },
    { id: 'suppliers', icon: Users, label: '供应商管理', path: '/suppliers', color: 'bg-green-500' },
    { id: 'materials', icon: Package, label: '物料查询', path: '/materials', color: 'bg-purple-500' },
    { id: 'arrivals', icon: Package, label: '到货跟踪', path: '/arrivals', color: 'bg-orange-500' },
  ],
  production: [
    { id: 'work-orders', icon: FileText, label: '工单管理', path: '/work-orders', color: 'bg-blue-500' },
    { id: 'kit-check', icon: Package, label: '齐套检查', path: '/kit-check', color: 'bg-green-500' },
    { id: 'board', icon: Briefcase, label: '生产看板', path: '/production-board', color: 'bg-purple-500' },
    { id: 'schedule', icon: Clock, label: '排期计划', path: '/progress-tracking/schedule', color: 'bg-orange-500' },
  ],
  admin: [
    { id: 'users', icon: Users, label: '用户管理', path: '/users', color: 'bg-blue-500' },
    { id: 'roles', icon: Settings, label: '角色管理', path: '/roles', color: 'bg-green-500' },
    { id: 'permissions', icon: Settings, label: '权限配置', path: '/permissions', color: 'bg-purple-500' },
    { id: 'settings', icon: Settings, label: '系统设置', path: '/settings', color: 'bg-orange-500' },
  ],
};

/**
 * 快捷操作按钮
 */
function ActionButton({ action, index, onClick }) {
  const Icon = action.icon;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05 }}
    >
      <Button
        variant="outline"
        className="flex flex-col items-center justify-center h-20 w-full gap-2 hover:bg-muted/50"
        onClick={() => onClick(action)}
      >
        <div className={cn('p-2 rounded-md', action.color)}>
          <Icon className="h-4 w-4 text-white" />
        </div>
        <span className="text-xs">{action.label}</span>
      </Button>
    </motion.div>
  );
}

/**
 * 快捷操作主组件
 *
 * @param {Object} props
 * @param {string} props.type - 角色类型
 * @param {Array} props.actions - 自定义操作列表
 * @param {Object} props.data - 预加载的数据
 */
export default function QuickActions({ type, actions, data }) {
  const navigate = useNavigate();

  // 获取操作列表
  const actionList = actions || roleActions[type] || data?.actions || defaultActions;

  const handleAction = (action) => {
    if (action.path) {
      navigate(action.path);
    } else if (action.onClick) {
      action.onClick();
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">快捷操作</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          {actionList.map((action, index) => (
            <ActionButton
              key={action.id}
              action={action}
              index={index}
              onClick={handleAction}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
