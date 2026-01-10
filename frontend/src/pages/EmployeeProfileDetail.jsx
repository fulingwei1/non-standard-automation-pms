// -*- coding: utf-8 -*-
/**
 * 员工档案详情页面
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft, User, Briefcase, Clock, Award, Star, Target,
  Heart, Zap, RefreshCw, TrendingUp
} from 'lucide-react';
import { PageHeader } from '../components/layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { cn } from '../lib/utils';
import { staffMatchingApi } from '../services/api';

// 模拟员工详情数据
// Mock data - 已移除，使用真实API
};

// Mock data - 已移除，使用真实API
// Mock data - 已移除，使用真实API
// 标签类型配置
const TAG_TYPE_CONFIG = {
  SKILL: { label: '技能', color: 'blue', icon: Target },
  DOMAIN: { label: '领域', color: 'green', icon: Briefcase },
  ATTITUDE: { label: '态度', color: 'orange', icon: Heart },
  CHARACTER: { label: '性格', color: 'purple', icon: Star },
  SPECIAL: { label: '特殊', color: 'red', icon: Zap },
};

export default function EmployeeProfileDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState(mockProfile);
  const [evaluations, setEvaluations] = useState(mockEvaluations);
  const [performance, setPerformance] = useState(mockPerformance);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [profileRes, evalRes, perfRes] = await Promise.all([
          staffMatchingApi.getProfile(id),
          staffMatchingApi.getEvaluations({ employee_id: id }),
          staffMatchingApi.getPerformance({ employee_id: id })
        ]);
        if (profileRes.data) setProfile(profileRes.data);
        if (evalRes.data?.items) setEvaluations(evalRes.data.items);
        if (perfRes.data?.items) setPerformance(perfRes.data.items);
      } catch (error) {
        console.error('加载数据失败:', error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  // 按标签类型分组评价
  const groupedEvaluations = evaluations.reduce((acc, eval_) => {
    const type = eval_.tag_type || 'SKILL';
    if (!acc[type]) acc[type] = [];
    acc[type].push(eval_);
    return acc;
  }, {});

  // 6维雷达图数据（简化显示为条形图）
  const dimensions = [
    { key: 'skill', label: '技能匹配', score: profile.skill_score_avg, weight: 30 },
    { key: 'domain', label: '领域经验', score: profile.domain_score_avg, weight: 15 },
    { key: 'attitude', label: '工作态度', score: profile.attitude_score_avg, weight: 20 },
    { key: 'quality', label: '历史质量', score: profile.quality_score_avg, weight: 15 },
    { key: 'workload', label: '工作负载', score: 100 - profile.current_workload_pct, weight: 15 },
    { key: 'special', label: '特殊能力', score: profile.special_score_avg || 75, weight: 5 },
  ];

  const getScoreColor = (score) => {
    if (score >= 85) return 'text-green-400';
    if (score >= 70) return 'text-blue-400';
    if (score >= 55) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getContributionBadge = (level) => {
    const colors = {
      '核心': 'bg-green-500/20 text-green-400 border-green-500/30',
      '骨干': 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      '参与': 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    };
    return colors[level] || colors['参与'];
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="员工档案详情"
        description={`${profile.employee_name} - ${profile.department}`}
        actions={
          <Button variant="outline" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回
          </Button>
        }
      />

      <div className="grid grid-cols-12 gap-6">
        {/* 左侧：基本信息和维度得分 */}
        <div className="col-span-4 space-y-6">
          {/* 基本信息卡片 */}
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white text-2xl font-bold">
                  {profile.employee_name?.charAt(0)}
                </div>
                <h2 className="mt-4 text-xl font-semibold text-white">{profile.employee_name}</h2>
                <p className="text-slate-400">{profile.employee_code}</p>
                <div className="mt-2">
                  <Badge className={getContributionBadge(profile.avg_contribution_level)}>
                    {profile.avg_contribution_level}
                  </Badge>
                </div>
              </div>

              <div className="mt-6 space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">部门</span>
                  <span className="text-white">{profile.department}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">职位</span>
                  <span className="text-white">{profile.position}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">参与项目</span>
                  <span className="text-white">{profile.project_count} 个</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">当前负载</span>
                  <span className={cn(
                    profile.current_workload_pct >= 90 ? 'text-red-400' :
                    profile.current_workload_pct >= 70 ? 'text-yellow-400' : 'text-green-400'
                  )}>
                    {profile.current_workload_pct}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 6维能力雷达 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">六维能力评估</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {dimensions.map(dim => (
                <div key={dim.key}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">{dim.label} ({dim.weight}%)</span>
                    <span className={getScoreColor(dim.score)}>{dim.score}</span>
                  </div>
                  <Progress value={dim.score} className="h-2" />
                </div>
              ))}

              <div className="pt-4 border-t border-white/10">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">加权总分</span>
                  <span className="text-2xl font-bold text-primary">
                    {Math.round(dimensions.reduce((sum, d) => sum + d.score * d.weight / 100, 0))}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 右侧：评价标签和项目绩效 */}
        <div className="col-span-8 space-y-6">
          {/* 标签评价 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">能力标签评价</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {Object.entries(groupedEvaluations).map(([type, evals]) => {
                  const config = TAG_TYPE_CONFIG[type] || TAG_TYPE_CONFIG.SKILL;
                  const Icon = config.icon;

                  return (
                    <div key={type}>
                      <div className="flex items-center gap-2 mb-3">
                        <Icon className="h-4 w-4 text-slate-400" />
                        <span className="text-sm font-medium text-slate-300">{config.label}标签</span>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        {evals.map(eval_ => (
                          <div
                            key={eval_.id}
                            className="p-3 rounded-lg border border-white/10 bg-white/5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-white">{eval_.tag_name}</span>
                              <div className="flex items-center gap-1">
                                {[1, 2, 3, 4, 5].map(i => (
                                  <Star
                                    key={i}
                                    className={cn(
                                      'h-3 w-3',
                                      i <= eval_.score ? 'text-yellow-400 fill-yellow-400' : 'text-slate-600'
                                    )}
                                  />
                                ))}
                              </div>
                            </div>
                            <div className="text-xs text-slate-500 mt-1">
                              {eval_.evaluator_name} · {eval_.evaluated_at}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* 项目绩效历史 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">项目绩效历史</CardTitle>
            </CardHeader>
            <CardContent>
              {performance.length === 0 ? (
                <div className="text-center py-8 text-slate-400">暂无绩效记录</div>
              ) : (
                <div className="space-y-3">
                  {performance.map(perf => (
                    <motion.div
                      key={perf.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-4 rounded-lg border border-white/10 bg-white/5"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-white">{perf.project_name}</div>
                          <div className="text-xs text-slate-500 mt-1">
                            完成时间: {perf.end_date}
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <Badge className={getContributionBadge(perf.contribution_level)}>
                            {perf.contribution_level}
                          </Badge>
                          <div className="text-center">
                            <div className={cn('text-lg font-bold', getScoreColor(perf.quality_score))}>
                              {perf.quality_score}
                            </div>
                            <div className="text-xs text-slate-500">质量评分</div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
