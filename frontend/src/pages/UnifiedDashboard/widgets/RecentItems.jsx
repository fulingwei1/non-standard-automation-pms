/**
 * 最近访问组件 (Recent Items)
 *
 * 显示用户最近访问的项目/文档
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  History,
  Briefcase,
  FileText,
  Users,
  Package,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { cn } from '../../../lib/utils';

// 类型图标映射
const typeIcons = {
  project: Briefcase,
  document: FileText,
  customer: Users,
  order: Package,
  default: FileText,
};

// 默认最近访问数据
const defaultItems = [
  { id: 1, type: 'project', title: 'PJ250101-001 智能检测设备', time: '5分钟前', path: '/projects/PJ250101-001' },
  { id: 2, type: 'document', title: '技术方案v2.0.docx', time: '30分钟前', path: '/documents/123' },
  { id: 3, type: 'customer', title: '华为技术有限公司', time: '1小时前', path: '/customers/456' },
  { id: 4, type: 'project', title: 'PJ250101-002 自动组装线', time: '2小时前', path: '/projects/PJ250101-002' },
  { id: 5, type: 'order', title: 'PO250101001 采购订单', time: '昨天', path: '/purchases/PO250101001' },
];

/**
 * 单个最近访问项
 */
function RecentItem({ item, index, onClick }) {
  const Icon = typeIcons[item.type] || typeIcons.default;

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      onClick={() => onClick?.(item)}
      className={cn(
        'flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors',
        'hover:bg-white/5'
      )}
    >
      <div className="p-2 rounded-md bg-white/5">
        <Icon className="h-4 w-4 text-slate-400" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{item.title}</p>
        <p className="text-xs text-muted-foreground">{item.time}</p>
      </div>
      <ChevronRight className="h-4 w-4 text-slate-500" />
    </motion.div>
  );
}

/**
 * 最近访问主组件
 */
export default function RecentItems({ type, limit = 5, data }) {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadItems = async () => {
      setLoading(true);
      try {
        if (data?.items) {
          setItems(data.items.slice(0, limit));
          return;
        }

        // 从 localStorage 获取最近访问记录
        const stored = localStorage.getItem('recent_items');
        if (stored) {
          const parsed = JSON.parse(stored);
          const filtered = type ? parsed.filter(i => i.type === type) : parsed;
          setItems(filtered.slice(0, limit));
          return;
        }

        setItems(defaultItems.slice(0, limit));
      } finally {
        setLoading(false);
      }
    };

    loadItems();
  }, [type, limit, data]);

  const handleItemClick = (item) => {
    if (item.path) {
      navigate(item.path);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <History className="h-4 w-4" />
          最近访问
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {[...Array(limit)].map((_, i) => (
              <div key={i} className="h-12 bg-white/5 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
            <History className="h-8 w-8 mb-2" />
            <p className="text-sm">暂无访问记录</p>
          </div>
        ) : (
          <div className="space-y-1">
            {items.map((item, index) => (
              <RecentItem
                key={item.id}
                item={item}
                index={index}
                onClick={handleItemClick}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
