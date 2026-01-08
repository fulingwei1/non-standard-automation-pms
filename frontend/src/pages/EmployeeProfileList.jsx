// -*- coding: utf-8 -*-
/**
 * 员工档案列表页面
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Users, Search, Eye, RefreshCw, User, Briefcase, Clock
} from 'lucide-react';
import { PageHeader } from '../components/layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { cn } from '../lib/utils';
import { staffMatchingApi } from '../services/api';

// 模拟数据
const mockProfiles = [
  {
    id: 1, employee_id: 1, employee_name: '张工', employee_code: 'EMP001',
    department: '机械设计部', position: '高级机械工程师',
    skill_score_avg: 88, domain_score_avg: 85, attitude_score_avg: 90,
    quality_score_avg: 92, current_workload_pct: 60, project_count: 5,
    avg_contribution_level: '核心', skill_tags: ['机械设计', 'SolidWorks', 'AutoCAD']
  },
  {
    id: 2, employee_id: 2, employee_name: '李工', employee_code: 'EMP002',
    department: '机械设计部', position: '机械工程师',
    skill_score_avg: 82, domain_score_avg: 78, attitude_score_avg: 85,
    quality_score_avg: 80, current_workload_pct: 85, project_count: 3,
    avg_contribution_level: '骨干', skill_tags: ['机械设计', 'SolidWorks']
  },
  {
    id: 3, employee_id: 3, employee_name: '王工', employee_code: 'EMP003',
    department: '电气设计部', position: '电气工程师',
    skill_score_avg: 85, domain_score_avg: 80, attitude_score_avg: 88,
    quality_score_avg: 85, current_workload_pct: 45, project_count: 4,
    avg_contribution_level: '骨干', skill_tags: ['PLC编程', '电气设计']
  },
  {
    id: 4, employee_id: 4, employee_name: '赵工', employee_code: 'EMP004',
    department: '软件开发部', position: '软件工程师',
    skill_score_avg: 90, domain_score_avg: 88, attitude_score_avg: 92,
    quality_score_avg: 90, current_workload_pct: 100, project_count: 2,
    avg_contribution_level: '核心', skill_tags: ['C#开发', '视觉算法']
  },
];

export default function EmployeeProfileList() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [profiles, setProfiles] = useState(mockProfiles);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('all');

  const loadProfiles = useCallback(async () => {
    setLoading(true);
    try {
      const response = await staffMatchingApi.getProfiles({ page_size: 100 });
      if (response.data?.items) {
        setProfiles(response.data.items);
      }
    } catch (error) {
      console.error('加载员工档案失败:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProfiles();
  }, [loadProfiles]);

  // 过滤
  const filteredProfiles = profiles.filter(p => {
    const matchKeyword = !searchKeyword ||
      p.employee_name.includes(searchKeyword) ||
      p.employee_code.includes(searchKeyword);
    const matchDept = filterDepartment === 'all' || p.department === filterDepartment;
    return matchKeyword && matchDept;
  });

  // 获取部门列表
  const departments = [...new Set(profiles.map(p => p.department).filter(Boolean))];

  // 统计
  const stats = {
    total: profiles.length,
    available: profiles.filter(p => p.current_workload_pct < 80).length,
    busy: profiles.filter(p => p.current_workload_pct >= 80).length,
  };

  const getWorkloadColor = (pct) => {
    if (pct >= 90) return 'text-red-400';
    if (pct >= 70) return 'text-yellow-400';
    return 'text-green-400';
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="员工能力档案"
        description="查看员工技能评估、工作负载和项目绩效"
      />

      {/* 统计卡片 */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-blue-500/10">
                <Users className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-white">{stats.total}</div>
                <div className="text-sm text-slate-400">总员工数</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-green-500/10">
                <User className="h-6 w-6 text-green-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-green-400">{stats.available}</div>
                <div className="text-sm text-slate-400">可用人员 (&lt;80%)</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-lg bg-orange-500/10">
                <Clock className="h-6 w-6 text-orange-400" />
              </div>
              <div>
                <div className="text-2xl font-bold text-orange-400">{stats.busy}</div>
                <div className="text-sm text-slate-400">繁忙人员 (≥80%)</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 搜索和筛选 */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>员工列表</CardTitle>
          <div className="flex items-center gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索姓名/工号..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-9 w-64"
              />
            </div>
            <select
              value={filterDepartment}
              onChange={(e) => setFilterDepartment(e.target.value)}
              className="h-10 px-3 rounded-md border border-white/10 bg-white/5 text-sm"
            >
              <option value="all">全部部门</option>
              {departments.map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            <Button variant="outline" size="icon" onClick={loadProfiles}>
              <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12 text-slate-400">加载中...</div>
          ) : filteredProfiles.length === 0 ? (
            <div className="text-center py-12 text-slate-400">暂无数据</div>
          ) : (
            <div className="space-y-3">
              {filteredProfiles.map(profile => (
                <motion.div
                  key={profile.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white font-semibold">
                        {profile.employee_name.charAt(0)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white">{profile.employee_name}</span>
                          <span className="text-xs text-slate-500">{profile.employee_code}</span>
                          <Badge variant="outline" className="text-xs">
                            {profile.avg_contribution_level}
                          </Badge>
                        </div>
                        <div className="text-sm text-slate-400 mt-1">
                          {profile.department} · {profile.position}
                        </div>
                        <div className="flex gap-1 mt-2">
                          {profile.skill_tags?.slice(0, 4).map(tag => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-8">
                      {/* 能力得分 */}
                      <div className="text-center">
                        <div className="text-xl font-bold text-primary">
                          {Math.round((profile.skill_score_avg + profile.domain_score_avg + profile.attitude_score_avg + profile.quality_score_avg) / 4)}
                        </div>
                        <div className="text-xs text-slate-500">综合评分</div>
                      </div>

                      {/* 工作负载 */}
                      <div className="w-32">
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-slate-400">工作负载</span>
                          <span className={getWorkloadColor(profile.current_workload_pct)}>
                            {profile.current_workload_pct}%
                          </span>
                        </div>
                        <Progress
                          value={profile.current_workload_pct}
                          className="h-2"
                        />
                      </div>

                      {/* 项目数 */}
                      <div className="text-center">
                        <div className="text-lg font-semibold text-white">{profile.project_count}</div>
                        <div className="text-xs text-slate-500">参与项目</div>
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => navigate(`/staff-matching/profiles/${profile.employee_id}`)}
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        详情
                      </Button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
