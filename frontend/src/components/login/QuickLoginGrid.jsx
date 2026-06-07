import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import {
  Shield,
  UserCog,
} from 'lucide-react';

const QUICK_LOGIN_ACCOUNTS = [
  {
    username: 'admin',
    password: 'admin123',
    name: '系统管理员',
    title: '全权限验证',
    icon: UserCog,
    color: 'slate',
  },
  {
    username: 'fulingwei',
    password: 'admin123',
    name: '符凌维',
    title: '副总经理（董秘）',
    icon: Shield,
    color: 'violet',
  },
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

      <div className="mt-4 grid grid-cols-2 gap-2">
        {QUICK_LOGIN_ACCOUNTS.map((account) => {
          const Icon = account.icon;
          return (
            <motion.button
              key={account.username}
              type="button"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(account.username, account.password)}
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
        点击上方按钮自动填充已验证账号，然后点击登录
      </p>
    </div>
  );
}
