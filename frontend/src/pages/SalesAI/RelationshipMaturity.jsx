/**
 * 商务关系成熟度评估页面
 * 
 * 评估与客户的关系深度，预测赢单概率
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Users,
  TrendingUp,
  Target,
  Heart,
  MessageSquare,
  Award,
  AlertTriangle,
  CheckCircle,
  ArrowUp,
  ArrowDown,
  Activity,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui";

// 关系成熟度评估
function RelationshipAssessment() {
  const [assessment, _setAssessment] = useState({
    customer_name: "宁德时代",
    overall_score: 78,
    maturity_level: "L4",
    maturity_level_name: "战略级",
    estimated_win_rate: 72,
    dimension_scores: [
      { name: "决策链覆盖", score: 16, max: 20, percentage: 80 },
      { name: "互动频率", score: 12, max: 15, percentage: 80 },
      { name: "关系深度", score: 14, max: 20, percentage: 70 },
      { name: "信息获取", score: 13, max: 15, percentage: 87 },
      { name: "支持度", score: 16, max: 20, percentage: 80 },
      { name: "高层互动", score: 7, max: 10, percentage: 70 },
    ],
  });

  const getLevelColor = (level) => {
    const colors = {
      L1: "text-slate-400 bg-slate-500/10",
      L2: "text-blue-400 bg-blue-500/10",
      L3: "text-green-400 bg-green-500/10",
      L4: "text-blue-500 bg-blue-500/10",
      L5: "text-purple-500 bg-purple-500/10",
    };
    return colors[level] || colors.L2;
  };

  return (
    <div className="space-y-6">
      {/* 总体评估 */}
      <div className="grid md:grid-cols-4 gap-4">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>{assessment.customer_name}</CardTitle>
            <CardDescription>
              关系成熟度评估
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div>
                <div className="text-4xl font-bold text-blue-500">{assessment.overall_score}</div>
                <div className="text-sm text-slate-400">总分 (100)</div>
              </div>
              <div className="flex-1">
                <Progress value={assessment.overall_score} className="h-3" />
              </div>
              <Badge className={getLevelColor(assessment.maturity_level)}>
                {assessment.maturity_level} - {assessment.maturity_level_name}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">预估赢单率</div>
            <div className="text-3xl font-bold text-green-500">{assessment.estimated_win_rate}%</div>
            <div className="text-xs text-slate-400 mt-1">基于关系成熟度</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">趋势</div>
            <div className="flex items-center gap-2">
              <ArrowUp className="w-5 h-5 text-green-500" />
              <span className="text-2xl font-bold">改善中</span>
            </div>
            <div className="text-xs text-slate-400 mt-1">近 30 天 +5 分</div>
          </CardContent>
        </Card>
      </div>

      {/* 六维度雷达数据 */}
      <Card>
        <CardHeader>
          <CardTitle>六维度评估</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {assessment.dimension_scores.map((dim, idx) => (
              <Card key={idx}>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{dim.name}</span>
                    <span className="text-sm text-slate-400">{dim.score}/{dim.max}</span>
                  </div>
                  <Progress value={dim.percentage} className="h-2" />
                  <div className="text-xs text-slate-400 mt-1">{dim.percentage}%</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 改进建议 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            改进建议
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-3 bg-red-500/10 rounded">
              <AlertTriangle className="w-5 h-5 text-red-500 mt-0.5" />
              <div className="flex-1">
                <div className="font-medium">争取 EB 明确支持</div>
                <div className="text-sm text-slate-400">总经理王五尚未明确表态，需安排 CEO 互访</div>
                <div className="flex items-center gap-4 mt-2 text-xs">
                  <span className="text-red-500">+4 分 → 赢单率 +5%</span>
                  <span className="text-slate-400">截止：2 周内</span>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 bg-orange-500/10 rounded">
              <AlertTriangle className="w-5 h-5 text-orange-500 mt-0.5" />
              <div className="flex-1">
                <div className="font-medium">从信任级提升至伙伴级</div>
                <div className="text-sm text-slate-400">签署战略合作协议，邀请参与联合开发</div>
                <div className="flex items-center gap-4 mt-2 text-xs">
                  <span className="text-orange-500">+4 分 → 赢单率 +3%</span>
                  <span className="text-slate-400">截止：1 个月内</span>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 bg-blue-500/10 rounded">
              <CheckCircle className="w-5 h-5 text-blue-500 mt-0.5" />
              <div className="flex-1">
                <div className="font-medium">提升至 CEO 级别互动</div>
                <div className="text-sm text-slate-400">安排双方 CEO 会面，签署合作备忘录</div>
                <div className="flex items-center gap-4 mt-2 text-xs">
                  <span className="text-blue-500">+3 分 → 赢单率 +2%</span>
                  <span className="text-slate-400">截止：1 个月内</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 客户组合分析
function PortfolioAnalysis() {
  const [portfolio, _setPortfolio] = useState({
    total_customers: 45,
    distribution: [
      { level: "L1", name: "初始级", count: 8, percentage: 17.8, win_rate: 15, color: "slate" },
      { level: "L2", name: "发展级", count: 15, percentage: 33.3, win_rate: 35, color: "blue" },
      { level: "L3", name: "成熟级", count: 12, percentage: 26.7, win_rate: 55, color: "green" },
      { level: "L4", name: "战略级", count: 7, percentage: 15.6, win_rate: 75, color: "blue" },
      { level: "L5", name: "伙伴级", count: 3, percentage: 6.7, win_rate: 90, color: "purple" },
    ],
    key_accounts: [
      { name: "宁德时代", level: "L4", score: 78, potential: 50000000, trend: "up" },
      { name: "比亚迪", level: "L4", score: 82, potential: 40000000, trend: "stable" },
      { name: "中创新航", level: "L3", score: 65, potential: 30000000, trend: "up" },
      { name: "亿纬锂能", level: "L4", score: 75, potential: 25000000, trend: "stable" },
      { name: "欣旺达", level: "L2", score: 42, potential: 25000000, trend: "down" },
    ],
  });

  return (
    <div className="space-y-6">
      {/* 分布统计 */}
      <Card>
        <CardHeader>
          <CardTitle>客户成熟度分布</CardTitle>
          <CardDescription>
            总客户数：{portfolio.total_customers} · 健康度（L3+）：48.9%
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-5 gap-4">
            {portfolio.distribution.map((dist) => (
              <Card key={dist.level}>
                <CardContent className="pt-4 text-center">
                  <div className={`text-2xl font-bold text-${dist.color}-500`}>{dist.count}</div>
                  <div className="text-xs text-slate-400">{dist.name}</div>
                  <div className="text-xs text-slate-400">{dist.percentage}%</div>
                  <div className="text-xs text-slate-400 mt-1">赢单率{dist.win_rate}%</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 重点客户 */}
      <Card>
        <CardHeader>
          <CardTitle>重点客户关系</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>客户</TableHead>
                <TableHead>成熟度</TableHead>
                <TableHead>得分</TableHead>
                <TableHead>潜力金额</TableHead>
                <TableHead>预估赢单率</TableHead>
                <TableHead>趋势</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {portfolio.key_accounts.map((account) => (
                <TableRow key={account.name}>
                  <TableCell className="font-medium">{account.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{account.level}</Badge>
                  </TableCell>
                  <TableCell>
                    <span className={account.score >= 70 ? "text-green-500" : account.score >= 50 ? "text-blue-500" : "text-orange-500"}>
                      {account.score}
                    </span>
                  </TableCell>
                  <TableCell>¥{(account.potential / 1000000).toFixed(0)}M</TableCell>
                  <TableCell>
                    <Badge variant={account.score >= 70 ? "default" : "secondary"}>
                      {account.score >= 85 ? 90 : account.score >= 70 ? 75 : account.score >= 50 ? 55 : 35}%
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {account.trend === "up" && <ArrowUp className="w-4 h-4 text-green-500" />}
                    {account.trend === "down" && <ArrowDown className="w-4 h-4 text-red-500" />}
                    {account.trend === "stable" && <Activity className="w-4 h-4 text-slate-400" />}
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

// 主页面
export default function RelationshipMaturity() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="商务关系成熟度"
          description="评估客户关系深度，预测赢单概率"
          icon={<Heart className="w-6 h-6 text-pink-500" />}
        />

        <Tabs defaultValue="assessment" className="mt-6">
          <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
            <TabsTrigger value="assessment">
              <Target className="w-4 h-4 mr-2" />
              客户评估
            </TabsTrigger>
            <TabsTrigger value="portfolio">
              <Users className="w-4 h-4 mr-2" />
              组合分析
            </TabsTrigger>
          </TabsList>

          <TabsContent value="assessment" className="mt-6">
            <RelationshipAssessment />
          </TabsContent>

          <TabsContent value="portfolio" className="mt-6">
            <PortfolioAnalysis />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
