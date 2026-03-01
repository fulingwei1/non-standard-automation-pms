/**
 * 数据质量评分页面
 * 
 * 倒逼销售认真填写：
 * 1. 公开排名
 * 2. 影响预测准确性
 * 3. 与绩效挂钩
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Award,
  Target,
  FileText,
  Phone,
  Users,
  MapPin,
  Star,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
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
  Alert,
} from "../../components/ui";

// 数据质量排名
function QualityRanking() {
  const [rankings, setRankings] = useState([
    {
      rank: 1,
      name: "张三",
      team: "华南大区",
      score: 92,
      trend: "up",
      completeness: 95,
      timeliness: 90,
      decision_chain: 88,
      visit_records: 95,
      healthy_opps: 11,
      total_opps: 12,
      prediction_accuracy: 96.5,
    },
    {
      rank: 2,
      name: "李四",
      team: "华东大区",
      score: 85,
      trend: "stable",
      completeness: 88,
      timeliness: 85,
      decision_chain: 80,
      visit_records: 88,
      healthy_opps: 8,
      total_opps: 10,
      prediction_accuracy: 92.0,
    },
    {
      rank: 3,
      name: "王五",
      team: "华南大区",
      score: 72,
      trend: "down",
      completeness: 75,
      timeliness: 65,
      decision_chain: 70,
      visit_records: 78,
      healthy_opps: 6,
      total_opps: 11,
      prediction_accuracy: 85.0,
      alerts: ["5 个商机超过 14 天未跟进", "3 个商机缺少决策链信息"],
    },
  ]);

  const getScoreColor = (score) => {
    if (score >= 90) return "text-green-500";
    if (score >= 75) return "text-blue-500";
    if (score >= 60) return "text-orange-500";
    return "text-red-500";
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return <Award className="w-5 h-5 text-yellow-500" />;
    if (rank === 2) return <Award className="w-5 h-5 text-slate-400" />;
    if (rank === 3) return <Award className="w-5 h-5 text-orange-500" />;
    return <span className="text-slate-400">{rank}</span>;
  };

  return (
    <div className="space-y-4">
      <Alert className="border-blue-500 bg-blue-500/10">
        <Target className="h-4 w-4" />
        <div>
          <strong>数据质量影响预测准确性</strong>
          <div className="text-sm text-slate-400 mt-1">
            数据质量分每低 10 分，预测准确率下降约 5%，赢单率下降约 10%
          </div>
        </div>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>数据质量排名</CardTitle>
          <CardDescription>
            团队平均分：83 · 公司平均分：78
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>排名</TableHead>
                <TableHead>姓名</TableHead>
                <TableHead>团队</TableHead>
                <TableHead className="text-right">总分</TableHead>
                <TableHead className="text-right">线索完整</TableHead>
                <TableHead className="text-right">跟进及时</TableHead>
                <TableHead className="text-right">决策链</TableHead>
                <TableHead className="text-right">拜访记录</TableHead>
                <TableHead className="text-right">健康商机</TableHead>
                <TableHead className="text-right">预测准确</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rankings.map((rep) => (
                <TableRow key={rep.name} className={rep.score < 75 ? "bg-orange-500/5" : ""}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getRankIcon(rep.rank)}
                      {rep.trend === "up" && <TrendingUp className="w-4 h-4 text-green-500" />}
                      {rep.trend === "down" && <TrendingDown className="w-4 h-4 text-red-500" />}
                    </div>
                  </TableCell>
                  <TableCell className="font-medium">{rep.name}</TableCell>
                  <TableCell>{rep.team}</TableCell>
                  <TableCell className="text-right">
                    <span className={`text-lg font-bold ${getScoreColor(rep.score)}`}>
                      {rep.score}
                    </span>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Progress value={rep.completeness} className="w-16 h-2" />
                      <span className="text-sm w-8">{rep.completeness}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Progress value={rep.timeliness} className="w-16 h-2" />
                      <span className="text-sm w-8">{rep.timeliness}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Progress value={rep.decision_chain} className="w-16 h-2" />
                      <span className="text-sm w-8">{rep.decision_chain}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Progress value={rep.visit_records} className="w-16 h-2" />
                      <span className="text-sm w-8">{rep.visit_records}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <span className="text-sm">{rep.healthy_opps}/{rep.total_opps}</span>
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant={rep.prediction_accuracy >= 95 ? "default" : "secondary"}>
                      {rep.prediction_accuracy}%
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// 评分规则
function ScoringRules() {
  const rules = [
    {
      icon: <FileText className="w-5 h-5" />,
      name: "线索完整度",
      weight: 20,
      criteria: "必填字段填写率 ≥95% 得满分",
      fields: ["客户名称", "联系人", "电话", "预算", "需求描述", "预计成交时间"],
    },
    {
      icon: <Phone className="w-5 h-5" />,
      name: "跟进及时性",
      weight: 25,
      criteria: "无超过 7 天未跟进的商机",
      penalty: "每多 1 个逾期商机扣 5 分",
    },
    {
      icon: <Users className="w-5 h-5" />,
      name: "决策链完整度",
      weight: 25,
      criteria: "EB/TB/PB 信息完整",
      fields: ["最终决策人 (EB)", "技术决策人 (TB)", "采购决策人 (PB)"],
    },
    {
      icon: <MapPin className="w-5 h-5" />,
      name: "拜访记录完整度",
      weight: 15,
      criteria: "拜访打卡 + 照片 + 记录",
      fields: ["GPS 打卡", "现场照片", "拜访内容", "下一步计划"],
    },
    {
      icon: <Star className="w-5 h-5" />,
      name: "赢单/输单原因",
      weight: 15,
      criteria: "关闭商机时详细填写原因",
      penalty: "未填写原因每次扣 3 分",
    },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>数据质量评分规则</CardTitle>
          <CardDescription>
            总分 100 分，5 个维度加权计算
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            {rules.map((rule, idx) => (
              <Card key={idx}>
                <CardContent className="pt-4">
                  <div className="flex items-start gap-4">
                    <div className="p-2 bg-blue-500/10 rounded">
                      {rule.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium">{rule.name}</div>
                        <Badge variant="outline">权重 {rule.weight}%</Badge>
                      </div>
                      <div className="text-sm text-slate-400 mb-2">{rule.criteria}</div>
                      {rule.fields && (
                        <div className="flex flex-wrap gap-2">
                          {rule.fields.map((field, i) => (
                            <Badge key={i} variant="secondary" className="text-xs">{field}</Badge>
                          ))}
                        </div>
                      )}
                      {rule.penalty && (
                        <div className="text-sm text-orange-500 mt-2">
                          <AlertCircle className="w-3 h-3 inline mr-1" />
                          {rule.penalty}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 影响分析
function ImpactAnalysis() {
  const comparisons = [
    {
      category: "高数据质量 (≥90 分)",
      sales: 5,
      accuracy: 96.5,
      winRate: 68,
      cycleDays: 32,
      color: "green",
    },
    {
      category: "中数据质量 (70-90 分)",
      sales: 12,
      accuracy: 88.0,
      winRate: 52,
      cycleDays: 45,
      color: "blue",
    },
    {
      category: "低数据质量 (<70 分)",
      sales: 8,
      accuracy: 75.0,
      winRate: 35,
      cycleDays: 62,
      color: "red",
    },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>数据质量影响分析</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4 mb-6">
            {comparisons.map((comp) => (
              <Card key={comp.category}>
                <CardContent className="pt-4">
                  <div className={`text-lg font-bold mb-2 text-${comp.color}-500`}>
                    {comp.category}
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-400">人数</span>
                      <span>{comp.sales}人</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">预测准确率</span>
                      <span className="font-bold">{comp.accuracy}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">赢单率</span>
                      <span className="font-bold">{comp.winRate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">成交周期</span>
                      <span className="font-bold">{comp.cycleDays}天</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Alert className="border-green-500 bg-green-500/10">
            <CheckCircle className="h-4 w-4" />
            <div>
              <strong>关键发现</strong>
              <ul className="text-sm text-slate-400 mt-2 space-y-1">
                <li>• 数据质量高的销售，预测准确率高 21.5%</li>
                <li>• 数据质量高的销售，赢单率高 33%</li>
                <li>• 数据质量高的销售，成交周期短 48%</li>
              </ul>
            </div>
          </Alert>

          <div className="mt-4 p-4 bg-slate-800 rounded">
            <div className="text-center">
              <div className="text-lg font-bold mb-2">结论</div>
              <div className="text-slate-300">
                认真填写数据不仅提高预测准确性，还直接提升销售业绩
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 主页面
export default function DataQualityDashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="数据质量评分"
          description="公开排名 · 影响预测 · 挂钩绩效"
          icon={<Target className="w-6 h-6 text-purple-500" />}
        />

        <Tabs defaultValue="ranking" className="mt-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[450px]">
            <TabsTrigger value="ranking">
              <Award className="w-4 h-4 mr-2" />
              排名
            </TabsTrigger>
            <TabsTrigger value="rules">
              <FileText className="w-4 h-4 mr-2" />
              规则
            </TabsTrigger>
            <TabsTrigger value="impact">
              <TrendingUp className="w-4 h-4 mr-2" />
              影响
            </TabsTrigger>
          </TabsList>

          <TabsContent value="ranking" className="mt-6">
            <QualityRanking />
          </TabsContent>

          <TabsContent value="rules" className="mt-6">
            <ScoringRules />
          </TabsContent>

          <TabsContent value="impact" className="mt-6">
            <ImpactAnalysis />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
