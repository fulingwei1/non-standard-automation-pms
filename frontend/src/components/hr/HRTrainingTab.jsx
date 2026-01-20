/**
 * HR Training Tab Component - 培训管理标签页
 * 
 * 核心功能:
 * 1. 培训计划统计
 * 2. 培训课程列表
 * 3. 培训进度跟踪
 * 4. 培训效果评估
 * 5. 快速操作
 */

import React from 'react';
import { motion } from 'framer-motion';
import {
  GraduationCap,
  Calendar,
  Users,
  CheckCircle2,
  Clock,
  Target,
  TrendingUp,
  Plus,
  FileText,
  BarChart3,
  BookOpen,
  Award,
  ChevronRight
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
  toast
} from '../ui';
import { cn } from '../../lib/utils';
import { fadeIn } from '../../lib/animations';

const HRTrainingTab = ({
  stats = {},
  courses = [],
  onCreateTraining,
  onViewCourse,
  onViewReport,
  formatDate = (date) => date
}) => {
  // 计算统计数据
  const {
    totalTrainings = 0,
    ongoingTrainings = 0,
    completedTrainings = 0,
    totalParticipants = 0,
    avgCompletionRate = 0,
    avgSatisfactionScore = 0
  } = stats;

  // 培训类型配置
  const trainingTypes = {
    orientation: { label: '入职培训', color: 'text-blue-400', bg: 'bg-blue-500/20' },
    technical: { label: '技术培训', color: 'text-purple-400', bg: 'bg-purple-500/20' },
    management: { label: '管理培训', color: 'text-amber-400', bg: 'bg-amber-500/20' },
    compliance: { label: '合规培训', color: 'text-red-400', bg: 'bg-red-500/20' },
    skill: { label: '技能提升', color: 'text-emerald-400', bg: 'bg-emerald-500/20' }
  };

  // 培训状态配置
  const statusConfig = {
    planned: { label: '计划中', color: 'text-slate-400', bg: 'bg-slate-500/20' },
    ongoing: { label: '进行中', color: 'text-blue-400', bg: 'bg-blue-500/20' },
    completed: { label: '已完成', color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
    cancelled: { label: '已取消', color: 'text-red-400', bg: 'bg-red-500/20' }
  };

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">进行中培训</p>
                  <p className="text-2xl font-bold text-white">{ongoingTrainings}</p>
                  <p className="text-xs text-slate-500 mt-1">共{totalTrainings}个计划</p>
                </div>
                <div className="p-3 bg-blue-500/20 rounded-lg">
                  <Clock className="w-6 h-6 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">已完成培训</p>
                  <p className="text-2xl font-bold text-white">{completedTrainings}</p>
                  <p className="text-xs text-emerald-400 mt-1 flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    完成率 {avgCompletionRate}%
                  </p>
                </div>
                <div className="p-3 bg-emerald-500/20 rounded-lg">
                  <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">参训人次</p>
                  <p className="text-2xl font-bold text-white">{totalParticipants}</p>
                  <p className="text-xs text-slate-500 mt-1">本月累计</p>
                </div>
                <div className="p-3 bg-purple-500/20 rounded-lg">
                  <Users className="w-6 h-6 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">满意度评分</p>
                  <p className="text-2xl font-bold text-white">{avgSatisfactionScore}</p>
                  <p className="text-xs text-amber-400 mt-1 flex items-center gap-1">
                    <Award className="w-3 h-3" />
                    5分制评价
                  </p>
                </div>
                <div className="p-3 bg-amber-500/20 rounded-lg">
                  <Target className="w-6 h-6 text-amber-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 培训课程列表 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <BookOpen className="h-5 w-5 text-blue-400" />
                培训课程
              </CardTitle>
              <Button
                size="sm"
                onClick={onCreateTraining}
                className="gap-2"
              >
                <Plus className="w-4 h-4" />
                创建培训
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {courses.length === 0 ? (
                <div className="py-8 text-center text-slate-400">
                  <GraduationCap className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>暂无培训课程</p>
                  <p className="text-xs text-slate-500 mt-1">点击"创建培训"添加新的培训计划</p>
                </div>
              ) : (
                courses.map((course, index) => {
                  const typeConfig = trainingTypes[course.type] || trainingTypes.skill;
                  const statusCfg = statusConfig[course.status] || statusConfig.planned;
                  const completionRate = course.completion_rate || 0;

                  return (
                    <div
                      key={course.id || index}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-all cursor-pointer"
                      onClick={() => onViewCourse && onViewCourse(course)}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-medium text-white">{course.name}</h3>
                            <Badge className={cn("text-xs", typeConfig.bg, typeConfig.color)}>
                              {typeConfig.label}
                            </Badge>
                            <Badge className={cn("text-xs", statusCfg.bg, statusCfg.color)}>
                              {statusCfg.label}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-xs text-slate-400">
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {formatDate(course.start_date)} - {formatDate(course.end_date)}
                            </span>
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {course.participants_count || 0}人参与
                            </span>
                            {course.instructor && (
                              <span className="flex items-center gap-1">
                                <GraduationCap className="w-3 h-3" />
                                {course.instructor}
                              </span>
                            )}
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-500" />
                      </div>

                      {/* 进度条 (仅进行中的培训) */}
                      {course.status === 'ongoing' && (
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400">完成进度</span>
                            <span className="text-blue-400 font-medium">{completionRate}%</span>
                          </div>
                          <Progress value={completionRate} className="h-1.5" />
                        </div>
                      )}

                      {/* 满意度评分 (已完成的培训) */}
                      {course.status === 'completed' && course.satisfaction_score && (
                        <div className="flex items-center gap-2 mt-2 text-xs">
                          <Award className="w-3 h-3 text-amber-400" />
                          <span className="text-slate-400">满意度:</span>
                          <span className="text-amber-400 font-medium">{course.satisfaction_score}/5.0</span>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 快速操作 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="h-5 w-5 text-cyan-400" />
              快速操作
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Button
                variant="outline"
                className="justify-start gap-2 h-auto py-3 hover:bg-blue-500/10 hover:border-blue-500/30"
                onClick={onCreateTraining}
              >
                <Plus className="w-4 h-4 text-blue-400" />
                <span>创建培训计划</span>
              </Button>
              <Button
                variant="outline"
                className="justify-start gap-2 h-auto py-3 hover:bg-purple-500/10 hover:border-purple-500/30"
                onClick={onViewReport}
              >
                <FileText className="w-4 h-4 text-purple-400" />
                <span>培训报告</span>
              </Button>
              <Button
                variant="outline"
                className="justify-start gap-2 h-auto py-3 hover:bg-amber-500/10 hover:border-amber-500/30"
                onClick={() => toast.info("培训分析功能待接入")}
              >
                <BarChart3 className="w-4 h-4 text-amber-400" />
                <span>培训分析</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export { HRTrainingTab };
