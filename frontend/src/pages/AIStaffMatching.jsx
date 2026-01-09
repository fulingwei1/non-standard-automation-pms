// -*- coding: utf-8 -*-
/**
 * AI智能匹配页面
 * 执行AI匹配算法，展示候选人推荐结果，支持采纳/拒绝操作
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, Users, Target, Check, X, RefreshCw, Clock, User, Award,
  TrendingUp, AlertCircle, ChevronRight, Rocket, History, Star
} from 'lucide-react';
import { PageHeader } from '../components/layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { cn } from '../lib/utils';
import { staffMatchingApi } from '../services/api';

// 推荐类型配置
const RECOMMENDATION_CONFIG = {
  STRONG: { color: 'green', text: '强烈推荐', icon: Star },
  RECOMMENDED: { color: 'blue', text: '推荐', icon: TrendingUp },
  ACCEPTABLE: { color: 'yellow', text: '可接受', icon: Check },
  WEAK: { color: 'red', text: '较弱匹配', icon: AlertCircle },
};

// 优先级配置
const PRIORITY_CONFIG = {
  P1: { color: 'red', text: 'P1-紧急', threshold: 85 },
  P2: { color: 'orange', text: 'P2-高', threshold: 75 },
  P3: { color: 'blue', text: 'P3-中', threshold: 65 },
  P4: { color: 'green', text: 'P4-低', threshold: 55 },
  P5: { color: 'slate', text: 'P5-最低', threshold: 50 },
};

// 模拟人员需求数据
const mockStaffingNeeds = [
  {
    id: 1, project_id: 1, project_name: '汽车零部件自动化产线',
    role_code: 'MECH_ENG', role_name: '机械工程师', headcount: 2,
    priority: 'P1', status: 'OPEN', start_date: '2026-01-15', end_date: '2026-06-30',
    allocation_pct: 100, filled_count: 0,
    required_skills: [
      { tag_id: 1, tag_name: '机械设计', min_score: 4 },
      { tag_id: 2, tag_name: 'SolidWorks', min_score: 3 }
    ]
  },
  {
    id: 2, project_id: 2, project_name: '3C电子装配线',
    role_code: 'ELEC_ENG', role_name: '电气工程师', headcount: 1,
    priority: 'P2', status: 'MATCHING', start_date: '2026-02-01', end_date: '2026-08-31',
    allocation_pct: 80, filled_count: 0,
    required_skills: [
      { tag_id: 6, tag_name: 'PLC编程', min_score: 4 },
      { tag_id: 7, tag_name: '电气设计', min_score: 3 }
    ]
  },
  {
    id: 3, project_id: 3, project_name: '医疗器械检测设备',
    role_code: 'SW_ENG', role_name: '软件工程师', headcount: 1,
    priority: 'P3', status: 'OPEN', start_date: '2026-01-20', end_date: '2026-05-31',
    allocation_pct: 100, filled_count: 0,
    required_skills: [
      { tag_id: 10, tag_name: 'C#开发', min_score: 4 },
      { tag_id: 11, tag_name: '视觉算法', min_score: 3 }
    ]
  }
];

// 模拟匹配结果
const mockMatchingResult = {
  request_id: 'REQ-20260108-001',
  staffing_need_id: 1,
  project_id: 1,
  project_name: '汽车零部件自动化产线',
  role_code: 'MECH_ENG',
  role_name: '机械工程师',
  priority: 'P1',
  priority_threshold: 85,
  total_candidates: 5,
  qualified_count: 3,
  matching_time: new Date().toISOString(),
  candidates: [
    {
      employee_id: 1, employee_name: '张工', employee_code: 'EMP001',
      department: '机械设计部', total_score: 92.5, rank: 1,
      recommendation_type: 'STRONG', current_workload_pct: 60, available_hours: 64,
      matched_skills: ['机械设计', 'SolidWorks', 'AutoCAD'], missing_skills: [],
      dimension_scores: { skill: 95, domain: 90, attitude: 92, quality: 88, workload: 95, special: 85 }
    },
    {
      employee_id: 2, employee_name: '李工', employee_code: 'EMP002',
      department: '机械设计部', total_score: 86.8, rank: 2,
      recommendation_type: 'STRONG', current_workload_pct: 75, available_hours: 40,
      matched_skills: ['机械设计', 'SolidWorks'], missing_skills: ['AutoCAD'],
      dimension_scores: { skill: 88, domain: 85, attitude: 90, quality: 82, workload: 85, special: 80 }
    },
    {
      employee_id: 3, employee_name: '王工', employee_code: 'EMP003',
      department: '研发部', total_score: 78.2, rank: 3,
      recommendation_type: 'RECOMMENDED', current_workload_pct: 50, available_hours: 80,
      matched_skills: ['机械设计'], missing_skills: ['SolidWorks'],
      dimension_scores: { skill: 75, domain: 80, attitude: 85, quality: 78, workload: 100, special: 70 }
    },
    {
      employee_id: 4, employee_name: '赵工', employee_code: 'EMP004',
      department: '工艺部', total_score: 68.5, rank: 4,
      recommendation_type: 'ACCEPTABLE', current_workload_pct: 90, available_hours: 16,
      matched_skills: ['SolidWorks'], missing_skills: ['机械设计'],
      dimension_scores: { skill: 70, domain: 65, attitude: 75, quality: 70, workload: 50, special: 65 }
    },
    {
      employee_id: 5, employee_name: '孙工', employee_code: 'EMP005',
      department: '技术支持部', total_score: 55.0, rank: 5,
      recommendation_type: 'WEAK', current_workload_pct: 100, available_hours: 0,
      matched_skills: [], missing_skills: ['机械设计', 'SolidWorks'],
      dimension_scores: { skill: 50, domain: 55, attitude: 70, quality: 60, workload: 0, special: 50 }
    }
  ]
};

// 模拟匹配历史
const mockMatchingHistory = [
  {
    id: 1, request_id: 'REQ-20260107-001', project_name: '新能源电池产线',
    role_name: '机械工程师', employee_name: '张工', total_score: 88.5,
    is_accepted: true, accept_time: '2026-01-07 15:30:00', acceptor_name: '项目经理A',
    matching_time: '2026-01-07 14:00:00'
  },
  {
    id: 2, request_id: 'REQ-20260106-002', project_name: '半导体封装设备',
    role_name: '电气工程师', employee_name: '李工', total_score: 82.3,
    is_accepted: false, reject_reason: '工作负载过高', matching_time: '2026-01-06 10:00:00'
  },
  {
    id: 3, request_id: 'REQ-20260105-001', project_name: '视觉检测系统',
    role_name: '软件工程师', employee_name: '王工', total_score: 90.1,
    is_accepted: true, accept_time: '2026-01-05 16:45:00', acceptor_name: '项目经理B',
    matching_time: '2026-01-05 16:00:00'
  }
];

export default function AIStaffMatching() {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState('matching');
  const [staffingNeeds, setStaffingNeeds] = useState(mockStaffingNeeds);
  const [selectedNeedId, setSelectedNeedId] = useState(null);
  const [matchingResult, setMatchingResult] = useState(null);
  const [matchingHistory, setMatchingHistory] = useState(mockMatchingHistory);
  const [loading, setLoading] = useState(false);
  const [matching, setMatching] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  // 从URL参数获取需求ID
  useEffect(() => {
    const needId = searchParams.get('need_id');
    if (needId) {
      setSelectedNeedId(parseInt(needId));
    }
  }, [searchParams]);

  const selectedNeed = staffingNeeds.find(n => n.id === selectedNeedId);

  // 加载人员需求
  const loadStaffingNeeds = useCallback(async () => {
    setLoading(true);
    try {
      const response = await staffMatchingApi.getStaffingNeeds({
        status: 'OPEN,MATCHING',
        page_size: 100
      });
      if (response.data?.items) {
        setStaffingNeeds(response.data.items);
      }
    } catch (error) {
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载匹配历史
  const loadMatchingHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const response = await staffMatchingApi.getMatchingHistory({ page_size: 50 });
      if (response.data?.items) {
        setMatchingHistory(response.data.items);
      }
    } catch (error) {
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStaffingNeeds();
    loadMatchingHistory();
  }, [loadStaffingNeeds, loadMatchingHistory]);

  // 执行AI匹配
  const handleExecuteMatching = async () => {
    if (!selectedNeed) return;

    setMatching(true);
    try {
      const response = await staffMatchingApi.executeMatching(selectedNeed.id, { top_n: 10 });
      if (response.data) {
        setMatchingResult(response.data);
      } else {
        // 使用模拟数据
        setMatchingResult({
          ...mockMatchingResult,
          staffing_need_id: selectedNeed.id,
          project_name: selectedNeed.project_name,
          role_name: selectedNeed.role_name,
          priority: selectedNeed.priority,
          priority_threshold: PRIORITY_CONFIG[selectedNeed.priority]?.threshold || 65
        });
      }
    } catch (error) {
      // 使用模拟数据
      setMatchingResult({
        ...mockMatchingResult,
        staffing_need_id: selectedNeed.id,
        project_name: selectedNeed.project_name,
        role_name: selectedNeed.role_name,
        priority: selectedNeed.priority,
        priority_threshold: PRIORITY_CONFIG[selectedNeed.priority]?.threshold || 65
      });
    } finally {
      setMatching(false);
    }
  };

  // 采纳候选人
  const handleAccept = async (candidate) => {
    if (!window.confirm(`确定要采纳 ${candidate.employee_name} 作为该职位的候选人吗？`)) return;

    try {
      await staffMatchingApi.acceptCandidate({
        matching_log_id: candidate.matching_log_id || 1,
        staffing_need_id: matchingResult.staffing_need_id,
        employee_id: candidate.employee_id
      });
      loadStaffingNeeds();
      loadMatchingHistory();
      setMatchingResult(prev => ({
        ...prev,
        candidates: prev.candidates.filter(c => c.employee_id !== candidate.employee_id)
      }));
    } catch (error) {
      // 演示模式下也移除候选人
      setMatchingResult(prev => ({
        ...prev,
        candidates: prev.candidates.filter(c => c.employee_id !== candidate.employee_id)
      }));
    }
  };

  // 拒绝候选人
  const handleReject = (candidate) => {
    setSelectedCandidate(candidate);
    setRejectReason('');
    setShowRejectDialog(true);
  };

  const confirmReject = async () => {
    if (!rejectReason.trim()) return;

    try {
      await staffMatchingApi.rejectCandidate({
        matching_log_id: selectedCandidate.matching_log_id || 1,
        reject_reason: rejectReason
      });
      loadMatchingHistory();
    } catch (error) {
    }
    setShowRejectDialog(false);
  };

  // 获取得分颜色
  const getScoreColor = (score) => {
    if (score >= 85) return 'text-green-400';
    if (score >= 70) return 'text-blue-400';
    if (score >= 55) return 'text-yellow-400';
    return 'text-red-400';
  };

  // 获取推荐类型徽章
  const getRecommendationBadge = (type) => {
    const config = RECOMMENDATION_CONFIG[type] || RECOMMENDATION_CONFIG.WEAK;
    const colors = {
      green: 'bg-green-500/20 text-green-400 border-green-500/30',
      blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
      yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
      red: 'bg-red-500/20 text-red-400 border-red-500/30',
    };
    return colors[config.color] || colors.red;
  };

  // 维度配置
  const dimensions = [
    { key: 'skill', label: '技能匹配', weight: 30 },
    { key: 'domain', label: '领域经验', weight: 15 },
    { key: 'attitude', label: '工作态度', weight: 20 },
    { key: 'quality', label: '历史质量', weight: 15 },
    { key: 'workload', label: '工作负载', weight: 15 },
    { key: 'special', label: '特殊能力', weight: 5 },
  ];

  // 统计数据
  const stats = {
    openNeeds: staffingNeeds.filter(n => n.status === 'OPEN').length,
    matchingNeeds: staffingNeeds.filter(n => n.status === 'MATCHING').length,
    acceptedCount: matchingHistory.filter(h => h.is_accepted === true).length,
    totalMatches: matchingHistory.length,
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI智能人员匹配"
        description="基于6维加权评分算法，智能推荐最优候选人"
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-blue-500/10">
                <Target className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-400">{stats.openNeeds}</div>
                <div className="text-sm text-slate-400">待匹配需求</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-yellow-500/10">
                <Zap className="h-6 w-6 text-yellow-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-yellow-400">{stats.matchingNeeds}</div>
                <div className="text-sm text-slate-400">匹配中</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-green-500/10">
                <Check className="h-6 w-6 text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-green-400">{stats.acceptedCount}</div>
                <div className="text-sm text-slate-400">已采纳</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-violet-500/10">
                <History className="h-6 w-6 text-violet-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-violet-400">{stats.totalMatches}</div>
                <div className="text-sm text-slate-400">总匹配次数</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tab 切换 */}
      <Card>
        <CardHeader className="border-b border-white/10 pb-0">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('matching')}
              className={cn(
                'flex items-center gap-2 px-4 py-3 border-b-2 transition-colors',
                activeTab === 'matching'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              )}
            >
              <Rocket className="h-4 w-4" />
              执行匹配
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={cn(
                'flex items-center gap-2 px-4 py-3 border-b-2 transition-colors',
                activeTab === 'history'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              )}
            >
              <History className="h-4 w-4" />
              匹配历史
            </button>
          </div>
        </CardHeader>

        <CardContent className="pt-6">
          <AnimatePresence mode="wait">
            {activeTab === 'matching' ? (
              <motion.div
                key="matching"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                <div className="grid grid-cols-12 gap-6">
                  {/* 左侧：需求选择 */}
                  <div className="col-span-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-300">选择人员需求</span>
                      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={loadStaffingNeeds}>
                        <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                      </Button>
                    </div>

                    <select
                      value={selectedNeedId || ''}
                      onChange={(e) => {
                        setSelectedNeedId(e.target.value ? parseInt(e.target.value) : null);
                        setMatchingResult(null);
                      }}
                      className="w-full h-10 px-3 rounded-md border border-white/10 bg-white/5 text-sm"
                    >
                      <option value="">选择需求...</option>
                      {staffingNeeds.map(need => (
                        <option key={need.id} value={need.id}>
                          {need.project_name} - {need.role_name} ({need.priority})
                        </option>
                      ))}
                    </select>

                    {selectedNeed && (
                      <Card className="border-white/10">
                        <CardContent className="pt-4 space-y-3 text-sm">
                          <div className="flex justify-between">
                            <span className="text-slate-400">项目</span>
                            <span className="text-white">{selectedNeed.project_name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">角色</span>
                            <span className="text-white">{selectedNeed.role_name}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">需求人数</span>
                            <span className="text-white">{selectedNeed.headcount} 人</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">已满足</span>
                            <span className="text-white">{selectedNeed.filled_count || 0} 人</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">优先级</span>
                            <Badge className={cn(
                              PRIORITY_CONFIG[selectedNeed.priority]?.color === 'red' && 'bg-red-500/20 text-red-400',
                              PRIORITY_CONFIG[selectedNeed.priority]?.color === 'orange' && 'bg-orange-500/20 text-orange-400',
                              PRIORITY_CONFIG[selectedNeed.priority]?.color === 'blue' && 'bg-blue-500/20 text-blue-400',
                              PRIORITY_CONFIG[selectedNeed.priority]?.color === 'green' && 'bg-green-500/20 text-green-400',
                            )}>
                              {PRIORITY_CONFIG[selectedNeed.priority]?.text}
                            </Badge>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">最低分要求</span>
                            <span className="text-primary font-medium">
                              {PRIORITY_CONFIG[selectedNeed.priority]?.threshold} 分
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">投入比例</span>
                            <span className="text-white">{selectedNeed.allocation_pct}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-400">时间范围</span>
                            <span className="text-white text-xs">
                              {selectedNeed.start_date} ~ {selectedNeed.end_date}
                            </span>
                          </div>
                          {selectedNeed.required_skills?.length > 0 && (
                            <div>
                              <span className="text-slate-400">技能要求</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {selectedNeed.required_skills.map((skill, idx) => (
                                  <Badge key={idx} variant="secondary" className="text-xs">
                                    {skill.tag_name} ≥{skill.min_score}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    )}

                    <Button
                      className="w-full"
                      size="lg"
                      onClick={handleExecuteMatching}
                      disabled={!selectedNeed || matching}
                    >
                      {matching ? (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                          正在匹配...
                        </>
                      ) : (
                        <>
                          <Rocket className="h-4 w-4 mr-2" />
                          执行AI智能匹配
                        </>
                      )}
                    </Button>
                  </div>

                  {/* 右侧：匹配结果 */}
                  <div className="col-span-8">
                    <div className="flex items-center justify-between mb-4">
                      <span className="text-sm font-medium text-slate-300">匹配结果</span>
                      {matchingResult && (
                        <div className="flex gap-2">
                          <Badge variant="secondary">候选人: {matchingResult.total_candidates}</Badge>
                          <Badge className="bg-green-500/20 text-green-400">达标: {matchingResult.qualified_count}</Badge>
                        </div>
                      )}
                    </div>

                    {matching ? (
                      <div className="flex flex-col items-center justify-center py-20">
                        <RefreshCw className="h-12 w-12 text-primary animate-spin mb-4" />
                        <p className="text-slate-400">AI正在分析员工档案，计算匹配得分...</p>
                      </div>
                    ) : matchingResult ? (
                      <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                        {/* 提示信息 */}
                        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm text-blue-400">
                          匹配请求: {matchingResult.request_id} | 优先级: {matchingResult.priority} | 最低分阈值: {matchingResult.priority_threshold}分
                        </div>

                        {/* 候选人卡片列表 */}
                        {matchingResult.candidates?.length > 0 ? (
                          matchingResult.candidates.map((candidate, index) => {
                            const config = RECOMMENDATION_CONFIG[candidate.recommendation_type] || RECOMMENDATION_CONFIG.WEAK;
                            const isQualified = candidate.total_score >= (matchingResult.priority_threshold || 65);

                            return (
                              <motion.div
                                key={candidate.employee_id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.1 }}
                                className={cn(
                                  'p-4 rounded-lg border',
                                  isQualified
                                    ? 'border-green-500/30 bg-green-500/5'
                                    : 'border-white/10 bg-white/5'
                                )}
                              >
                                <div className="flex gap-6">
                                  {/* 左：基本信息 */}
                                  <div className="w-48 flex-shrink-0">
                                    <div className="flex items-center gap-3 mb-3">
                                      <div className="relative">
                                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white font-semibold">
                                          {candidate.employee_name?.charAt(0)}
                                        </div>
                                        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-yellow-500 text-black text-xs font-bold flex items-center justify-center">
                                          {candidate.rank}
                                        </div>
                                      </div>
                                      <div>
                                        <div className="font-medium text-white">{candidate.employee_name}</div>
                                        <div className="text-xs text-slate-500">{candidate.employee_code}</div>
                                        <div className="text-xs text-slate-500">{candidate.department}</div>
                                      </div>
                                    </div>

                                    <div className="flex gap-1 mb-3">
                                      <Badge className={getRecommendationBadge(candidate.recommendation_type)}>
                                        {config.text}
                                      </Badge>
                                      {isQualified && (
                                        <Badge className="bg-green-500/20 text-green-400">达标</Badge>
                                      )}
                                    </div>

                                    <div className="text-center">
                                      <div className={cn("text-3xl font-bold", getScoreColor(candidate.total_score))}>
                                        {candidate.total_score.toFixed(1)}
                                      </div>
                                      <div className="text-xs text-slate-500">匹配总分</div>
                                    </div>
                                  </div>

                                  {/* 中：维度得分 */}
                                  <div className="flex-1">
                                    <div className="text-xs text-slate-400 mb-2">维度得分</div>
                                    <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                                      {dimensions.map(dim => (
                                        <div key={dim.key}>
                                          <div className="flex justify-between text-xs mb-1">
                                            <span className="text-slate-500">{dim.label} ({dim.weight}%)</span>
                                            <span className={getScoreColor(candidate.dimension_scores[dim.key])}>
                                              {candidate.dimension_scores[dim.key]}
                                            </span>
                                          </div>
                                          <Progress value={candidate.dimension_scores[dim.key]} className="h-1.5" />
                                        </div>
                                      ))}
                                    </div>
                                  </div>

                                  {/* 右：技能和操作 */}
                                  <div className="w-40 flex-shrink-0 space-y-3">
                                    <div>
                                      <div className="text-xs text-slate-400 mb-1">当前负载</div>
                                      <div className="flex items-center gap-2">
                                        <Progress value={candidate.current_workload_pct} className="h-2 flex-1" />
                                        <span className={cn(
                                          "text-xs font-medium",
                                          candidate.current_workload_pct >= 90 ? 'text-red-400' :
                                          candidate.current_workload_pct >= 70 ? 'text-yellow-400' : 'text-green-400'
                                        )}>
                                          {candidate.current_workload_pct}%
                                        </span>
                                      </div>
                                      <div className="text-xs text-slate-500">
                                        可用: {candidate.available_hours}小时/周
                                      </div>
                                    </div>

                                    <div>
                                      <div className="text-xs text-slate-400 mb-1">匹配技能</div>
                                      <div className="flex flex-wrap gap-1">
                                        {candidate.matched_skills?.map(skill => (
                                          <Badge key={skill} className="text-xs bg-green-500/20 text-green-400">
                                            {skill}
                                          </Badge>
                                        ))}
                                      </div>
                                    </div>

                                    {candidate.missing_skills?.length > 0 && (
                                      <div>
                                        <div className="text-xs text-slate-400 mb-1">缺失技能</div>
                                        <div className="flex flex-wrap gap-1">
                                          {candidate.missing_skills.map(skill => (
                                            <Badge key={skill} className="text-xs bg-red-500/20 text-red-400">
                                              {skill}
                                            </Badge>
                                          ))}
                                        </div>
                                      </div>
                                    )}

                                    <div className="flex gap-2 pt-2">
                                      <Button size="sm" className="flex-1" onClick={() => handleAccept(candidate)}>
                                        <Check className="h-3 w-3 mr-1" />
                                        采纳
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        className="flex-1 text-red-400 border-red-500/30 hover:bg-red-500/10"
                                        onClick={() => handleReject(candidate)}
                                      >
                                        <X className="h-3 w-3 mr-1" />
                                        拒绝
                                      </Button>
                                    </div>
                                  </div>
                                </div>
                              </motion.div>
                            );
                          })
                        ) : (
                          <div className="text-center py-12 text-slate-400">暂无匹配的候选人</div>
                        )}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                        <Users className="h-12 w-12 mb-4 opacity-50" />
                        <p>请选择人员需求并执行AI匹配</p>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="history"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-medium text-slate-300">匹配历史记录</span>
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={loadMatchingHistory}>
                    <RefreshCw className={cn("h-4 w-4", historyLoading && "animate-spin")} />
                  </Button>
                </div>

                {historyLoading ? (
                  <div className="text-center py-12 text-slate-400">加载中...</div>
                ) : matchingHistory.length === 0 ? (
                  <div className="text-center py-12 text-slate-400">暂无历史记录</div>
                ) : (
                  <div className="space-y-3">
                    {matchingHistory.map(history => (
                      <motion.div
                        key={history.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-4 rounded-lg border border-white/10 bg-white/5"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3">
                              <span className="font-medium text-white">{history.project_name}</span>
                              <ChevronRight className="h-4 w-4 text-slate-500" />
                              <span className="text-slate-300">{history.role_name}</span>
                              <ChevronRight className="h-4 w-4 text-slate-500" />
                              <span className="text-white">{history.employee_name}</span>
                            </div>
                            <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
                              <span className="flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                匹配时间: {history.matching_time}
                              </span>
                              {history.accept_time && (
                                <span className="flex items-center gap-1">
                                  <Check className="h-3 w-3" />
                                  采纳时间: {history.accept_time}
                                </span>
                              )}
                              {history.acceptor_name && (
                                <span>处理人: {history.acceptor_name}</span>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-4">
                            <div className="text-center">
                              <div className={cn("text-lg font-bold", getScoreColor(history.total_score))}>
                                {history.total_score?.toFixed(1)}
                              </div>
                              <div className="text-xs text-slate-500">匹配得分</div>
                            </div>
                            {history.is_accepted === true ? (
                              <Badge className="bg-green-500/20 text-green-400">
                                <Check className="h-3 w-3 mr-1" />
                                已采纳
                              </Badge>
                            ) : history.is_accepted === false ? (
                              <Badge className="bg-red-500/20 text-red-400" title={history.reject_reason}>
                                <X className="h-3 w-3 mr-1" />
                                已拒绝
                              </Badge>
                            ) : (
                              <Badge variant="secondary">待处理</Badge>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* 拒绝原因对话框 */}
      <Dialog open={showRejectDialog} onOpenChange={setShowRejectDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>拒绝候选人</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm text-slate-400 mb-4">
              请填写拒绝 <span className="text-white font-medium">{selectedCandidate?.employee_name}</span> 的原因：
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="请输入拒绝原因，如：工作负载过高、技能不匹配等"
              className="w-full h-24 px-3 py-2 rounded-md border border-white/10 bg-white/5 text-sm resize-none"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRejectDialog(false)}>
              取消
            </Button>
            <Button
              variant="destructive"
              onClick={confirmReject}
              disabled={!rejectReason.trim()}
            >
              确认拒绝
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
