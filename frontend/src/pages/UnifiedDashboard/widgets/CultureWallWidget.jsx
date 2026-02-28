/**
 * CultureWallWidget - 企业文化墙组件
 * 展示企业价值观、近期公告、荣誉和员工风采
 * 放置于工作台首页高流量位置，确保每位员工都能看到
 */
import { useState, useEffect } from 'react';
import { Award, Megaphone, Users, Heart, Star, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { cn } from '../../../lib/utils';

// 模拟数据（后续可接入真实 API）
const mockCultureData = {
  // 企业核心价值观
  coreValues: [
    { icon: 'star', title: '追求卓越', desc: '精益求精，超越期望' },
    { icon: 'users', title: '团队协作', desc: '携手共进，共创价值' },
    { icon: 'heart', title: '客户至上', desc: '以客户需求为导向' },
    { icon: 'award', title: '创新驱动', desc: '持续创新，引领行业' },
  ],
  // 近期公告
  announcements: [
    { id: 1, title: '2026年春节放假通知', date: '2026-01-18', isNew: true },
    { id: 2, title: '年度优秀员工评选开始', date: '2026-01-15', isNew: true },
    { id: 3, title: '新员工培训计划发布', date: '2026-01-10', isNew: false },
  ],
  // 荣誉展示
  honors: [
    { id: 1, title: '2025年度最佳供应商奖', source: '某知名客户' },
    { id: 2, title: 'ISO9001质量管理体系认证', source: '国际认证机构' },
  ],
  // 员工风采
  employeeHighlights: [
    { id: 1, name: '张工', dept: '工程部', achievement: '本月完成3个项目提前交付' },
    { id: 2, name: '李经理', dept: '销售部', achievement: '季度销售冠军' },
    { id: 3, name: '王工', dept: '生产部', achievement: '工艺改进节省成本15%' },
  ],
};

// 值观图标映射
const valueIcons = {
  star: Star,
  users: Users,
  heart: Heart,
  award: Award,
};

export default function CultureWallWidget() {
  const [cultureData, _setCultureData] = useState(mockCultureData);
  const [currentHighlight, setCurrentHighlight] = useState(0);

  // 员工风采轮播
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentHighlight((prev) =>
        (prev + 1) % cultureData.employeeHighlights?.length
      );
    }, 5000);
    return () => clearInterval(timer);
  }, [cultureData.employeeHighlights?.length]);

  return (
    <Card className="border shadow-sm overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-amber-900/30 to-orange-900/30 border-b border-white/10 pb-3">
        <CardTitle className="text-lg flex items-center gap-2 text-white">
          <Megaphone className="w-5 h-5 text-orange-400" />
          企业文化墙
        </CardTitle>
      </CardHeader>
      <CardContent className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* 左侧：核心价值观 */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-slate-400 flex items-center gap-1">
              <Star className="w-4 h-4 text-amber-400" />
              核心价值观
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {(cultureData.coreValues || []).map((value, index) => {
                const IconComponent = valueIcons[value.icon] || Star;
                return (
                  <div
                    key={index}
                    className="bg-gradient-to-br from-indigo-900/40 to-violet-900/40 rounded-lg p-2 text-center hover:shadow-sm hover:shadow-primary/10 transition-shadow border border-white/5"
                  >
                    <IconComponent className="w-5 h-5 mx-auto text-indigo-400 mb-1" />
                    <div className="text-xs font-medium text-slate-200">{value.title}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{value.desc}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 中间：公告 + 荣誉 */}
          <div className="space-y-3">
            {/* 近期公告 */}
            <div>
              <h4 className="font-medium text-sm text-slate-400 flex items-center gap-1 mb-2">
                <Megaphone className="w-4 h-4 text-orange-400" />
                近期公告
              </h4>
              <div className="space-y-1.5">
                {cultureData.announcements.slice(0, 3).map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between text-sm hover:bg-white/5 rounded px-2 py-1 cursor-pointer group"
                  >
                    <div className="flex items-center gap-2 truncate">
                      {item.isNew && (
                        <span className="bg-red-500/80 text-white text-xs px-1 rounded">NEW</span>
                      )}
                      <span className="truncate text-slate-300 group-hover:text-primary">
                        {item.title}
                      </span>
                    </div>
                    <span className="text-xs text-slate-500 flex-shrink-0">{item.date}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 荣誉展示 */}
            <div>
              <h4 className="font-medium text-sm text-slate-400 flex items-center gap-1 mb-2">
                <Award className="w-4 h-4 text-yellow-400" />
                荣誉展示
              </h4>
              <div className="space-y-1.5">
                {(cultureData.honors || []).map((honor) => (
                  <div
                    key={honor.id}
                    className="bg-gradient-to-r from-yellow-900/20 to-amber-900/20 rounded px-2 py-1.5 border border-white/5"
                  >
                    <div className="text-sm font-medium text-slate-200">{honor.title}</div>
                    <div className="text-xs text-slate-500">{honor.source}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 右侧：员工风采轮播 */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-slate-400 flex items-center gap-1">
              <Users className="w-4 h-4 text-emerald-400" />
              员工风采
            </h4>
            <div className="bg-gradient-to-br from-emerald-900/30 to-green-900/30 rounded-lg p-3 min-h-[120px] relative border border-white/5">
              {(cultureData.employeeHighlights || []).map((employee, index) => (
                <div
                  key={employee.id}
                  className={cn(
                    'absolute inset-0 p-3 transition-opacity duration-500',
                    index === currentHighlight ? 'opacity-100' : 'opacity-0'
                  )}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-10 h-10 bg-emerald-700/50 rounded-full flex items-center justify-center text-emerald-300 font-medium border border-emerald-500/30">
                      {employee.name.charAt(0)}
                    </div>
                    <div>
                      <div className="font-medium text-slate-200">{employee.name}</div>
                      <div className="text-xs text-slate-500">{employee.dept}</div>
                    </div>
                  </div>
                  <div className="text-sm text-slate-300 bg-white/5 rounded p-2 border border-white/5">
                    {employee.achievement}
                  </div>
                </div>
              ))}
              {/* 轮播指示器 */}
              <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                {(cultureData.employeeHighlights || []).map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentHighlight(index)}
                    className={cn(
                      'w-1.5 h-1.5 rounded-full transition-colors',
                      index === currentHighlight ? 'bg-emerald-400' : 'bg-emerald-800'
                    )}
                  />
                ))}
              </div>
            </div>
            <button className="text-xs text-primary hover:text-primary-light flex items-center gap-1 justify-end w-full">
              查看更多员工故事 <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
