import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import {
  Award, Settings, Shield, TrendingUp, DollarSign,
  Briefcase, ShoppingCart, Hammer, Target, GitBranch,
  UserCog, UserCircle, Headphones
} from 'lucide-react';

const DEMO_ACCOUNTS = [
  { username: 'zhengrucai', name: '郑汝才', title: '常务副总', icon: Award, color: 'emerald' },
  { username: 'luoyixing', name: '骆奕兴', title: '副总经理', icon: Settings, color: 'cyan' },
  { username: 'fulingwei', name: '符凌维', title: '副总经理（董秘）', icon: Shield, color: 'violet' },
  { username: 'songkui', name: '宋魁', title: '营销总监', icon: TrendingUp, color: 'rose' },
  { username: 'zhengqin', name: '郑琴', title: '销售经理', icon: DollarSign, color: 'teal' },
  { username: 'yaohong', name: '姚洪', title: '销售工程师', icon: Briefcase, color: 'pink' },
  { username: 'changxiong', name: '常雄', title: 'PMC主管', icon: ShoppingCart, color: 'green' },
  { username: 'gaoyong', name: '高勇', title: '生产部经理', icon: Hammer, color: 'amber' },
  { username: 'chenliang', name: '陈亮', title: '项目管理部总监', icon: Target, color: 'indigo' },
  { username: 'tanzhangbin', name: '谭章斌', title: '项目经理', icon: GitBranch, color: 'blue' },
  { username: 'yuzhenhua', name: '于振华', title: '经理', icon: UserCog, color: 'slate' },
  { username: 'wangjun', name: '王俊', title: '经理', icon: UserCircle, color: 'violet' },
  { username: 'wangzhihong', name: '王志红', title: '客服主管', icon: Headphones, color: 'teal' },
];

export default function QuickLoginGrid({ onSelect }) {
  return (
    <div className="mt-8">
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-200" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-4 bg-white text-gray-500">快捷登录</span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-4 gap-2">
        {DEMO_ACCOUNTS.map((account) => {
          const Icon = account.icon;
          return (
            <motion.button
              key={account.username}
              type="button"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(account.username, '123456')}
              className={cn(
                "flex items-center gap-1.5 p-2.5 rounded-lg",
                `bg-gradient-to-br from-${account.color}-50 to-${account.color}-100`,
                `border border-${account.color}-200 hover:border-${account.color}-300`,
                "transition-all duration-200",
                "group text-xs"
              )}
            >
              <div className={cn(
                "p-1.5 rounded-lg transition-colors flex-shrink-0",
                `bg-${account.color}-100 group-hover:bg-${account.color}-200`
              )}>
                <Icon className={`h-3.5 w-3.5 text-${account.color}-600`} />
              </div>
              <div className="text-left min-w-0">
                <p className="font-medium text-gray-900 truncate">{account.name}</p>
                <p className="text-xs text-gray-500">{account.title}</p>
              </div>
            </motion.button>
          );
        })}
      </div>

      <p className="mt-3 text-xs text-gray-400 text-center">
        点击上方按钮自动填充账号，然后点击登录
      </p>
    </div>
  );
}
