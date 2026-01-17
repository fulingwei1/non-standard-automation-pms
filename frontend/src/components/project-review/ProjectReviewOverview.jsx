import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Button } from "../../components/ui/button";
import {
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Users,
  Calendar,
  Target,
  FileText,
  Clock,
  Star,
  BarChart3,
  Activity,
  Award } from
"lucide-react";
import {
  REVIEW_STATUS,
  REVIEW_TYPES,
  EVALUATION_METRICS,
  getReviewStatus,
  getReviewType,
  getEvaluationMetric,
  calculateReviewProgress,
  calculateReviewScore,
  generateReviewRecommendations } from
"./projectReviewConstants";
import { cn } from "../../lib/utils";
import { formatCurrency as _formatCurrency, formatDate } from "../../lib/utils";

/**
 * 📊 项目评审概览组件
 * 展示项目评审的关键信息、统计数据和评分结果
 */
export function ProjectReviewOverview({
  review = {},
  onEdit,
  onPublish,
  onArchive,
  onDelete: _onDelete,
  editable = false
}) {
  const [_expandedSection, _setExpandedSection] = useState(null);

  // 计算关键指标
  const metrics = useMemo(() => {
    const score = calculateReviewScore(review);
    const progress = calculateReviewProgress(review);
    const recommendations = generateReviewRecommendations(review);

    return {
      score,
      progress,
      recommendations,
      lessonsCount: review.lessons?.length || 0,
      practicesCount: review.best_practices?.length || 0,
      actionItemsCount: review.action_items?.length || 0,
      attachmentsCount: review.attachments?.length || 0
    };
  }, [review]);

  // 评估指标详情
  const evaluationDetails = useMemo(() => {
    if (!review.evaluations) return [];

    return review.evaluations.map((evaluation) => {
      const metric = getEvaluationMetric(evaluation.metric);
      return {
        ...evaluation,
        metricInfo: metric,
        weightedScore: evaluation.score * metric.weight,
        maxWeightedScore: 100 * metric.weight
      };
    }).sort((a, b) => b.metricInfo.weight - a.metricInfo.weight);
  }, [review.evaluations]);

  // 状态信息
  const statusInfo = getReviewStatus(review.status);
  const typeInfo = getReviewType(review.review_type);

  // 评分等级
  const getScoreLevel = (score) => {
    if (score >= 90) return { level: 'excellent', label: '优秀', color: 'text-green-400', icon: Award };
    if (score >= 80) return { level: 'good', label: '良好', color: 'text-blue-400', icon: TrendingUp };
    if (score >= 70) return { level: 'satisfactory', label: '合格', color: 'text-amber-400', icon: CheckCircle2 };
    if (score >= 60) return { level: 'needs_improvement', label: '需改进', color: 'text-orange-400', icon: AlertCircle };
    return { level: 'poor', label: '不合格', color: 'text-red-400', icon: AlertCircle };
  };

  const scoreLevel = getScoreLevel(metrics.score);
  const ScoreIcon = scoreLevel.icon;

  // 关键指标卡片
  const MetricCard = ({ title, value, icon: Icon, trend, color, description }) =>
  <motion.div
    whileHover={{ scale: 1.02 }}
    className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6">

      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className={cn("p-2 rounded-lg", color)}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-slate-400">{title}</h3>
              <p className="text-2xl font-bold text-white">{value}</p>
            </div>
          </div>
          {description &&
        <p className="text-xs text-slate-500 mt-2">{description}</p>
        }
        </div>
        {trend &&
      <div className="flex items-center gap-1">
            {trend > 0 ?
        <TrendingUp className="w-4 h-4 text-green-400" /> :

        <TrendingDown className="w-4 h-4 text-red-400" />
        }
            <span className={cn(
          "text-sm font-medium",
          trend > 0 ? 'text-green-400' : 'text-red-400'
        )}>
              {Math.abs(trend)}%
            </span>
          </div>
      }
      </div>
    </motion.div>;


  return (
    <div className="space-y-6">
      {/* 评审基本信息 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-3 text-white">
              <FileText className="w-5 h-5" />
              评审基本信息
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge
                variant="outline"
                className={cn(statusInfo.borderColor, statusInfo.textColor)}>

                {statusInfo.label}
              </Badge>
              <Badge
                variant="outline"
                className={cn("border", typeInfo.color, "text-white")}>

                {typeInfo.label}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-slate-400 mb-1">项目名称</div>
              <div className="text-white font-medium">{review.project_name}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">项目编码</div>
              <div className="text-white font-medium">{review.project_code}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">评审编号</div>
              <div className="text-white font-medium">{review.review_no}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">评审日期</div>
              <div className="text-white font-medium">
                {formatDate(review.review_date)}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">评审负责人</div>
              <div className="text-white font-medium">
                {review.reviewer_name || '未指定'}
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">参与人数</div>
              <div className="text-white font-medium">
                {review.participants?.length || 0} 人
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 关键指标 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="评审评分"
          value={`${metrics.score}分`}
          icon={Star}
          color="bg-amber-500"
          description={scoreLevel.label} />

        <MetricCard
          title="完成进度"
          value={`${metrics.progress}%`}
          icon={Target}
          color="bg-blue-500"
          description="内容完成度" />

        <MetricCard
          title="经验教训"
          value={metrics.lessonsCount}
          icon={FileText}
          color="bg-purple-500"
          description="经验教训数量" />

        <MetricCard
          title="最佳实践"
          value={metrics.practicesCount}
          icon={Award}
          color="bg-green-500"
          description="最佳实践数量" />

      </div>

      {/* 评分详情 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-white">
              <BarChart3 className="w-5 h-5" />
              评分详情
            </CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-white">{metrics.score}</span>
              <span className="text-sm text-slate-400">分</span>
              <ScoreIcon className={cn("w-6 h-6", scoreLevel.color)} />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {evaluationDetails.map((evaluation, index) =>
            <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-white font-medium">
                      {evaluation.metricInfo.label}
                    </span>
                    <span className="text-sm text-slate-400">
                      (权重: {evaluation.metricInfo.weight * 100}%)
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-white font-bold">{evaluation.score}</span>
                    <span className="text-sm text-slate-400 ml-1">
                      / {evaluation.maxWeightedScore.toFixed(1)}
                    </span>
                  </div>
                </div>
                <Progress
                value={evaluation.weightedScore}
                max={evaluation.maxWeightedScore}
                className="h-2" />

              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 项目概述 */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <FileText className="w-5 h-5" />
            项目概述
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-white mb-2">项目总结</h4>
            <p className="text-slate-300 leading-relaxed">
              {review.project_summary || '暂无项目总结'}
            </p>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-white mb-2">关键成果</h4>
            <p className="text-slate-300 leading-relaxed">
              {review.key_achievements || '暂无关键成果'}
            </p>
          </div>

          {review.challenges_faced &&
          <div>
              <h4 className="text-sm font-medium text-white mb-2">面临的挑战</h4>
              <p className="text-slate-300 leading-relaxed">
                {review.challenges_faced}
              </p>
            </div>
          }
        </CardContent>
      </Card>

      {/* 改进建议 */}
      {metrics.recommendations.length > 0 &&
      <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <TrendingUp className="w-5 h-5" />
              改进建议
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {metrics.recommendations.map((recommendation, index) =>
            <div key={index} className="p-4 rounded-lg border border-slate-700/50">
                  <div className="flex items-center gap-2 mb-2">
                    {recommendation.type === 'critical' && <AlertCircle className="w-4 h-4 text-red-400" />}
                    {recommendation.type === 'moderate' && <AlertCircle className="w-4 h-4 text-amber-400" />}
                    {recommendation.type === 'good' && <CheckCircle2 className="w-4 h-4 text-green-400" />}
                    <h4 className="text-white font-medium">{recommendation.title}</h4>
                  </div>
                  <p className="text-slate-300 text-sm mb-2">{recommendation.description}</p>
                  {recommendation.actions &&
              <ul className="text-slate-400 text-sm space-y-1">
                      {recommendation.actions.map((action, actionIndex) =>
                <li key={actionIndex} className="flex items-center gap-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
                          {action}
                        </li>
                )}
                    </ul>
              }
                </div>
            )}
            </div>
          </CardContent>
        </Card>
      }

      {/* 操作按钮 */}
      {editable &&
      <div className="flex items-center justify-end gap-3">
          {review.status === 'DRAFT' &&
        <>
              <Button variant="outline" onClick={onEdit}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                编辑
              </Button>
              <Button onClick={onPublish}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                发布
              </Button>
            </>
        }
          {review.status === 'PUBLISHED' &&
        <Button variant="outline" onClick={onArchive}>
              <Clock className="w-4 h-4 mr-2" />
              归档
            </Button>
        }
        </div>
      }
    </div>);

}

export default ProjectReviewOverview;