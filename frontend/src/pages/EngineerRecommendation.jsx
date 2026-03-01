/**
 * 工程师智能推荐看板
 * 功能：
 * - AI 抽取项目需求
 * - 智能推荐工程师
 * - 匹配度分析
 */

import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Target,
  Users,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  RefreshCw,
  Zap,
  Award,
  Clock,
  MapPin,
  Star,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { staggerContainer } from "../lib/animations";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "../components/ui";
import { requirementExtractionApi } from "../services/api/requirement";

// 匹配度等级
const MATCH_LEVELS = {
  EXCELLENT: { label: "优秀", color: "bg-green-500", range: [90, 100] },
  GOOD: { label: "良好", color: "bg-blue-500", range: [75, 90] },
  FAIR: { label: "一般", color: "bg-yellow-500", range: [60, 75] },
  POOR: { label: "较差", color: "bg-red-500", range: [0, 60] },
};

export default function EngineerRecommendation() {
  const { projectId } = useParams();
  const [loading, setLoading] = useState(true);
  const [requirements, setRequirements] = useState(null);
  const [recommendations, setRecommendations] = useState({});
  const [selectedReq, setSelectedReq] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const loadRequirements = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      // 抽取需求
      const reqRes = await requirementExtractionApi.extractRequirements(projectId);
      setRequirements(reqRes.data || reqRes);

      // 为每个需求推荐工程师
      const recs = {};
      for (const [type, reqList] of Object.entries((reqRes.data || reqRes).requirements || {})) {
        if (reqList.length > 0) {
          // 简化处理，直接存储需求
          recs[type] = reqList.map(req => ({
            ...req,
            recommendations: [], // 实际应该调用推荐 API
          }));
        }
      }
      setRecommendations(recs);
    } catch (error) {
      console.error("加载失败:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadRequirements();
  }, [loadRequirements]);

  const _getMatchLevel = (score) => {
    if (score >= 90) return MATCH_LEVELS.EXCELLENT;
    if (score >= 75) return MATCH_LEVELS.GOOD;
    if (score >= 60) return MATCH_LEVELS.FAIR;
    return MATCH_LEVELS.POOR;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-6 h-6 animate-spin text-blue-500 mr-2" />
        <span className="text-slate-400">AI 分析中...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="space-y-6"
        >
          <PageHeader
            title="工程师智能推荐"
            description="AI 分析项目需求，智能匹配工程师能力"
            actions={
              <Button onClick={loadRequirements} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                重新分析
              </Button>
            }
          />

          {/* 项目概览 */}
          {requirements && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-500" />
                  项目需求分析
                </CardTitle>
                <CardDescription>
                  {requirements.project_name} - 共{requirements.total_requirements}项需求
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(requirements.requirements || {}).map(([type, reqs]) => {
                    const typeNames = {
                      production: "生产需求",
                      service: "售后需求",
                      design: "设计需求",
                      debug: "调试需求",
                    };
                    const typeIcons = {
                      production: Zap,
                      service: Users,
                      design: Award,
                      debug: CheckCircle,
                    };
                    const Icon = typeIcons[type] || Target;

                    return (
                      <div key={type} className="p-4 rounded-lg border bg-slate-800/50">
                        <div className="flex items-center gap-2 mb-2">
                          <Icon className="w-4 h-4 text-blue-400" />
                          <span className="text-sm font-medium">
                            {typeNames[type] || type}
                          </span>
                        </div>
                        <div className="text-2xl font-bold">{reqs.length}项</div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}

          {/* 需求详情与推荐 */}
          {Object.entries(recommendations).map(([type, reqs]) => {
            const typeNames = {
              production: "生产需求",
              service: "售后需求",
              design: "设计需求",
              debug: "调试需求",
            };

            return (
              <Card key={type}>
                <CardHeader>
                  <CardTitle>{typeNames[type] || type}</CardTitle>
                  <CardDescription>
                    共{reqs.length}项需求，点击查看推荐工程师
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {reqs.map((req, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-lg border bg-slate-800/30 hover:bg-slate-800/50 transition-colors cursor-pointer"
                        onClick={() => {
                          setSelectedReq(req);
                          setShowDetail(true);
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <Badge variant="outline">
                              {req.requirement_type}
                            </Badge>
                            {req.production_complexity && (
                              <Badge variant={
                                req.production_complexity === 'EXPERT' ? 'destructive' :
                                req.production_complexity === 'HIGH' ? 'default' : 'secondary'
                              }>
                                {req.production_complexity}
                              </Badge>
                            )}
                          </div>
                          <Button variant="outline" size="sm">
                            查看推荐
                          </Button>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <div className="text-slate-400 mb-1">所需技能</div>
                            <div className="flex flex-wrap gap-1">
                              {(req.required_skills || []).slice(0, 3).map((skill, i) => (
                                <Badge key={i} variant="secondary" className="text-xs">
                                  {skill}
                                </Badge>
                              ))}
                              {(req.required_skills || []).length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{(req.required_skills || []).length - 3}
                                </Badge>
                              )}
                            </div>
                          </div>
                          <div>
                            <div className="text-slate-400 mb-1">预估工时</div>
                            <div className="font-medium">{req.estimated_hours || 0}h</div>
                          </div>
                          <div>
                            <div className="text-slate-400 mb-1">经验要求</div>
                            <div className="font-medium">{req.required_experience_years || 0}年</div>
                          </div>
                          <div>
                            <div className="text-slate-400 mb-1">截止日期</div>
                            <div className="font-medium">{req.deadline || '未设置'}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}

          {/* 推荐详情对话框 */}
          <Dialog open={showDetail} onOpenChange={setShowDetail}>
            <DialogContent className="max-w-4xl">
              <DialogHeader>
                <DialogTitle>
                  {selectedReq?.requirement_type} - 工程师推荐
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                {/* 需求详情 */}
                <div className="p-4 rounded-lg border bg-slate-800/50">
                  <div className="text-sm font-medium mb-3">需求详情</div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-slate-400">技能要求</div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {(selectedReq?.required_skills || []).map((skill, i) => (
                          <Badge key={i} variant="outline">{skill}</Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-400">复杂度</div>
                      <div className="font-medium mt-1">
                        {selectedReq?.production_complexity || '-'}
                      </div>
                    </div>
                    <div>
                      <div className="text-slate-400">经验要求</div>
                      <div className="font-medium mt-1">
                        {selectedReq?.required_experience_years || 0}年
                      </div>
                    </div>
                  </div>
                </div>

                {/* 推荐工程师 */}
                <div>
                  <div className="text-sm font-medium mb-3">推荐工程师</div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>工程师</TableHead>
                        <TableHead>匹配度</TableHead>
                        <TableHead>技能匹配</TableHead>
                        <TableHead>能力匹配</TableHead>
                        <TableHead>可用性</TableHead>
                        <TableHead>操作</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {/* 示例数据 */}
                      <TableRow>
                        <TableCell>
                          <div>
                            <div className="font-medium">张工</div>
                            <div className="text-xs text-slate-400">高级电气工程师</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className="bg-green-500">92.5</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={95} className="w-20 h-2" />
                            <span className="text-xs">95%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={88} className="w-20 h-2" />
                            <span className="text-xs">88%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Progress value={75} className="w-20 h-2" />
                            <span className="text-xs">75%</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Button variant="outline" size="sm">分配</Button>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={() => setShowDetail(false)}>关闭</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </motion.div>
      </div>
    </div>
  );
}
