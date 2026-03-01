/**
 * 综合赢单率预测页面
 * 
 * 4 大因素：商务关系 + 技术方案 + 价格竞争力 + 其他因素
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Heart,
  Cpu,
  DollarSign,
  Award,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Target,
  ArrowUp,
  ArrowDown,
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

// 单商机赢单率评估
function OpportunityAssessment() {
  const [assessment, _setAssessment] = useState({
    opportunity_name: "宁德时代 FCT 测试线项目",
    customer: "宁德时代",
    amount: 3500000,
    close_date: "2026-03-31",
    
    // 4 大因素得分
    factors: [
      { 
        name: "商务关系", 
        icon: <Heart className="w-5 h-5" />,
        score: 78, 
        weight: 35, 
        contribution: 27.3,
        color: "pink",
        level: "L4 战略级",
      },
      { 
        name: "技术方案", 
        icon: <Cpu className="w-5 h-5" />,
        score: 81, 
        weight: 30, 
        contribution: 24.3,
        color: "blue",
        level: "优秀",
      },
      { 
        name: "价格竞争力", 
        icon: <DollarSign className="w-5 h-5" />,
        score: 66, 
        weight: 25, 
        contribution: 16.5,
        color: "green",
        level: "中等",
      },
      { 
        name: "其他因素", 
        icon: <Award className="w-5 h-5" />,
        score: 72, 
        weight: 10, 
        contribution: 7.2,
        color: "purple",
        level: "良好",
      },
    ],
    
    // 综合赢单率
    total_win_rate: 75,
    confidence: 85,
    
    // 短板
    weaknesses: [
      {
        factor: "价格竞争力",
        score: 66,
        issue: "报价比竞品 A 高 8%",
        impact: "影响赢单率约 3.75%",
      },
      {
        factor: "商务关系",
        score: 78,
        issue: "总经理（EB）态度中立",
        impact: "决策阶段可能生变",
      },
    ],
  });

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-500";
    if (score >= 60) return "text-blue-500";
    if (score >= 40) return "text-orange-500";
    return "text-red-500";
  };

  return (
    <div className="space-y-6">
      {/* 基本信息 */}
      <Card>
        <CardHeader>
          <CardTitle>{assessment.opportunity_name}</CardTitle>
          <CardDescription className="flex items-center gap-4">
            <span>客户：{assessment.customer}</span>
            <span>金额：¥{(assessment.amount / 1000000).toFixed(1)}M</span>
            <span>预计成交：{assessment.close_date}</span>
          </CardDescription>
        </CardHeader>
      </Card>

      {/* 综合赢单率 */}
      <div className="grid md:grid-cols-2 gap-4">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>综合赢单率预测</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-6">
              <div>
                <div className={`text-6xl font-bold ${getScoreColor(assessment.total_win_rate)}`}>
                  {assessment.total_win_rate}%
                </div>
                <div className="text-sm text-slate-400 mt-1">
                  置信度 {assessment.confidence}%
                </div>
              </div>
              <div className="flex-1">
                <Progress value={assessment.total_win_rate} className="h-4" />
                <div className="flex justify-between text-xs text-slate-400 mt-2">
                  <span>0%</span>
                  <span className="text-blue-500">60-79% 重点跟进</span>
                  <span>100%</span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-slate-400">预期收入</div>
                <div className="text-2xl font-bold">¥{(assessment.amount * assessment.total_win_rate / 100 / 10000).toFixed(0)}万</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 4 大因素 */}
      <Card>
        <CardHeader>
          <CardTitle>4 大因素评估</CardTitle>
          <CardDescription>
            公式：商务关系×35% + 技术方案×30% + 价格×25% + 其他×10%
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {assessment.factors.map((factor, idx) => (
              <Card key={idx}>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`p-2 bg-${factor.color}-500/10 rounded`}>
                      {factor.icon}
                    </div>
                    <span className="text-sm font-medium">{factor.name}</span>
                  </div>
                  <div className="text-3xl font-bold mb-1">
                    <span className={getScoreColor(factor.score)}>{factor.score}</span>
                    <span className="text-sm text-slate-400">/100</span>
                  </div>
                  <Progress value={factor.score} className="h-2 mb-2" />
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">权重 {factor.weight}%</span>
                    <span className="text-slate-400">贡献 {factor.contribution}%</span>
                  </div>
                  <Badge variant="outline" className="mt-2 text-xs">
                    {factor.level}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 短板分析 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            短板分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {assessment.weaknesses.map((weakness, idx) => (
              <div key={idx} className="p-3 bg-orange-500/10 rounded">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">{weakness.factor}</div>
                    <div className="text-sm text-slate-400">{weakness.issue}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-slate-400">当前得分</div>
                    <div className="text-lg font-bold text-orange-500">{weakness.score}</div>
                    <div className="text-xs text-slate-400">{weakness.impact}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 改进建议 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-500" />
            改进建议（按优先级）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 border border-red-500/30 rounded">
              <div className="flex items-center gap-2 mb-2">
                <Badge className="bg-red-500">优先级 1</Badge>
                <span className="font-medium">提升价格竞争力</span>
                <span className="text-sm text-slate-400 ml-auto">预期赢单率 +2.25%</span>
              </div>
              <ul className="text-sm text-slate-400 space-y-1">
                <li>• 准备价值导向的价格分解（1 周内）</li>
                <li>• 提供 TCO 对比分析，强调 3 年节省电费 42 万（1 周内）</li>
                <li>• 提供分期付款方案：30%+40%+30%（3 天内）</li>
              </ul>
            </div>

            <div className="p-4 border border-orange-500/30 rounded">
              <div className="flex items-center gap-2 mb-2">
                <Badge className="bg-orange-500">优先级 2</Badge>
                <span className="font-medium">深化商务关系</span>
                <span className="text-sm text-slate-400 ml-auto">预期赢单率 +2.45%</span>
              </div>
              <ul className="text-sm text-slate-400 space-y-1">
                <li>• 安排 CEO 互访，争取总经理支持（2 周内）</li>
                <li>• 邀请参观比亚迪标杆项目（2 周内）</li>
              </ul>
            </div>

            <div className="p-4 border border-blue-500/30 rounded">
              <div className="flex items-center gap-2 mb-2">
                <Badge className="bg-blue-500">优先级 3</Badge>
                <span className="font-medium">强化其他因素</span>
                <span className="text-sm text-slate-400 ml-auto">预期赢单率 +0.6%</span>
              </div>
              <ul className="text-sm text-slate-400 space-y-1">
                <li>• 提供快速响应承诺：2 小时响应，24 小时到场（1 周内）</li>
              </ul>
            </div>
          </div>

          <div className="mt-4 p-3 bg-green-500/10 rounded">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="font-medium">改进后预期</span>
              </div>
              <div className="text-right">
                <span className="text-sm text-slate-400">当前赢单率 </span>
                <span className="font-bold">{assessment.total_win_rate}%</span>
                <span className="text-slate-400 mx-2">→</span>
                <span className="text-sm text-slate-400">改进后 </span>
                <span className="font-bold text-green-500">81%</span>
                <span className="text-sm text-green-500 ml-2">(+6%)</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 多商机对比
function PortfolioComparison() {
  const [opportunities, _setOpportunities] = useState([
    {
      name: "宁德时代 FCT",
      customer: "宁德时代",
      amount: 3500000,
      win_rate: 75,
      expected_value: 2625000,
      relationship: 78,
      technical: 81,
      price: 66,
      other: 72,
      weakness: "价格",
      close_date: "2026-03-31",
    },
    {
      name: "比亚迪 EOL",
      customer: "比亚迪",
      amount: 4200000,
      win_rate: 82,
      expected_value: 3444000,
      relationship: 85,
      technical: 88,
      price: 75,
      other: 78,
      weakness: "无明显短板",
      close_date: "2026-03-25",
    },
    {
      name: "中创新航 ICT",
      customer: "中创新航",
      amount: 2800000,
      win_rate: 58,
      expected_value: 1624000,
      relationship: 62,
      technical: 70,
      price: 55,
      other: 58,
      weakness: "商务关系",
      close_date: "2026-04-15",
    },
    {
      name: "亿纬锂能 烧录",
      customer: "亿纬锂能",
      amount: 1800000,
      win_rate: 68,
      expected_value: 1224000,
      relationship: 72,
      technical: 75,
      price: 60,
      other: 65,
      weakness: "价格",
      close_date: "2026-04-05",
    },
  ]);

  return (
    <div className="space-y-6">
      {/* 汇总统计 */}
      <div className="grid md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">总商机数</div>
            <div className="text-3xl font-bold">28</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">Pipeline 总额</div>
            <div className="text-3xl font-bold">¥125M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">加权Pipeline</div>
            <div className="text-3xl font-bold text-green-500">¥68.5M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">平均赢单率</div>
            <div className="text-3xl font-bold">64%</div>
          </CardContent>
        </Card>
      </div>

      {/* 商机列表 */}
      <Card>
        <CardHeader>
          <CardTitle>重点商机赢单率分析</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>商机</TableHead>
                <TableHead>金额</TableHead>
                <TableHead>赢单率</TableHead>
                <TableHead>预期收入</TableHead>
                <TableHead>商务关系</TableHead>
                <TableHead>技术方案</TableHead>
                <TableHead>价格</TableHead>
                <TableHead>主要短板</TableHead>
                <TableHead>预计成交</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {opportunities.map((opp) => (
                <TableRow key={opp.name}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{opp.name}</div>
                      <div className="text-xs text-slate-400">{opp.customer}</div>
                    </div>
                  </TableCell>
                  <TableCell>¥{(opp.amount / 1000000).toFixed(1)}M</TableCell>
                  <TableCell>
                    <Badge variant={opp.win_rate >= 70 ? "default" : opp.win_rate >= 50 ? "secondary" : "destructive"}>
                      {opp.win_rate}%
                    </Badge>
                  </TableCell>
                  <TableCell className="font-medium">
                    ¥{(opp.expected_value / 10000).toFixed(0)}万
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={opp.relationship} className="w-16 h-2" />
                      <span className="text-xs w-8">{opp.relationship}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={opp.technical} className="w-16 h-2" />
                      <span className="text-xs w-8">{opp.technical}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={opp.price} className="w-16 h-2" />
                      <span className="text-xs w-8">{opp.price}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">
                      {opp.weakness}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-slate-400">{opp.close_date}</TableCell>
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
export default function WinRatePrediction() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="赢单率综合预测"
          description="商务关系 + 技术方案 + 价格竞争力 + 其他因素"
          icon={<Target className="w-6 h-6 text-cyan-500" />}
        />

        <Tabs defaultValue="assessment" className="mt-6">
          <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
            <TabsTrigger value="assessment">
              <Target className="w-4 h-4 mr-2" />
              单商机评估
            </TabsTrigger>
            <TabsTrigger value="portfolio">
              <TrendingUp className="w-4 h-4 mr-2" />
              多商机对比
            </TabsTrigger>
          </TabsList>

          <TabsContent value="assessment" className="mt-6">
            <OpportunityAssessment />
          </TabsContent>

          <TabsContent value="portfolio" className="mt-6">
            <PortfolioComparison />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
