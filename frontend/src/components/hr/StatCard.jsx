/**
 * HR统计卡片组件
 * 用途：展示各类统计数据（员工、招聘、绩效等）
 */
import React from 'react';
import { motion } from 'framer-motion';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '../../lib/utils';
import { fadeIn } from '../../lib/animations';

export const StatCard = ({ 
  title, 
  value, 
  subtitle, 
  trend, 
  icon: Icon, 
  color = 'text-white',
  bg = 'bg-slate-800' 
}) => {
  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn('text-2xl font-bold mb-1', color)}>{value}</p>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
          {trend !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}%</span>
                </>
              ) : trend < 0 ? (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}%</span>
                </>
              ) : null}
              {trend !== 0 && (
                <span className="text-xs text-slate-500 ml-1">vs 上月</span>
              )}
            </div>
          )}
        </div>
        {Icon && (
          <div className={cn('rounded-lg p-3 bg-opacity-20', bg)}>
            <Icon className={cn('h-6 w-6', color)} />
          </div>
        )}
      </div>
      <div className="absolute right-0 bottom-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl opacity-30" />
    </motion.div>
  );
};

export default StatCard;
