/**
 * 竞争对手分析页面
 * 
 * 分析对不同竞品的赢单率，指导竞争策略
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Sword,
  TrendingUp,
  TrendingDown,
  Target,
  Award,
  DollarSign,
  Users,
  Lightbulb,
  CheckCircle,
  XCircle,
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

// 竞争对手总览
function CompetitorOverview() {
  const [overview, _setOverview] = useState({
    total_opportunities: 156,
    time_range: "2024-01-01 ~ 2026-03-01",
    
    // 主要竞争对手
    competitors: [
      {
        name: "竞品 A",
        description: "德国知名自动化公司",
        position: "高端市场领导者",
        win_rate: 71.1,
        opportunities: 45,
        trend: "stable",
        strengths: ["品牌高", "技术成熟", "全球服务"],
        weaknesses: ["价格高", "交付慢", "定制弱"],
      },
      {
        name: "竞品 B",
        description: "国内上市公司",
        position: "中端市场主要竞争者",
        win_rate: 53.8,
        opportunities: 52,
        trend: "improving",
        strengths: ["价格适中", "响应快", "本地化"],
        weaknesses: ["技术浅", "案例少"],
      },
      {
        name: "竞品 C",
        description: "新兴公司",
        position: "低端市场挑战者",
        win_rate: 78.9,
        opportunities: 38,
        trend: "stable",
        strengths: ["价格低", "灵活", "服务积极"],
        weaknesses: ["品牌弱", "稳定性待验证"],
      },
      {
        name: "竞品 D",
        description: "台系厂商",
        position: "中端市场细分领域",
        win_rate: 47.6,
        opportunities: 21,
        trend: "declining",
        strengths: ["性价比", "电子行业经验"],
        weaknesses: ["服务弱", "大项目少"],
      },
    ],
    
    // 竞争优势对比
    advantages: [
      { name: "价格竞争力", vs_A: "优势", vs_B: "相当", vs_C: "劣势", vs_D: "相当" },
      { name: "技术实力", vs_A: "相当", vs_B: "领先", vs_C: "领先", vs_D: "领先" },
      { name: "交付周期", vs_A: "优势", vs_B: "优势", vs_C: "相当", vs_D: "相当" },
      { name: "售后服务", vs_A: "优势", vs_B: "优势", vs_C: "相当", vs_D: "劣势" },
      { name: "定制化能力", vs_A: "优势", vs_B: "优势", vs_C: "相当", vs_D: "劣势" },
    ],
  });

  const getWinRateColor = (rate) => {
    if (rate >= 70) return "text-green-500";
    if (rate >= 50) return "text-blue-500";
    if (rate >= 30) return "text-orange-500";
    return "text-red-500";
  };

  return (
    <div className="space-y-6">
      {/* 汇总统计 */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">分析商机数</div>
            <div className="text-3xl font-bold">{overview.total_opportunities}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">最高赢单率</div>
            <div className="text-3xl font-bold text-green-500">78.9%</div>
            <div className="text-xs text-slate-400">vs 竞品 C</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">最低赢单率</div>
            <div className="text-3xl font-bold text-red-500">47.6%</div>
            <div className="text-xs text-slate-400">vs 竞品 D</div>
          </CardContent>
        </Card>
      </div>

      {/* 竞争对手列表 */}
      <Card>
        <CardHeader>
          <CardTitle>主要竞争对手分析</CardTitle>
          <CardDescription>
            时间范围：{overview.time_range}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>竞争对手</TableHead>
                <TableHead>市场定位</TableHead>
                <TableHead>交锋次数</TableHead>
                <TableHead>赢单率</TableHead>
                <TableHead>趋势</TableHead>
                <TableHead>优势</TableHead>
                <TableHead>劣势</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {overview.competitors.map((comp) => (
                <TableRow key={comp.name}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{comp.name}</div>
                      <div className="text-xs text-slate-400">{comp.description}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{comp.position}</Badge>
                  </TableCell>
                  <TableCell>{comp.opportunities}次</TableCell>
                  <TableCell>
                    <span className={`text-lg font-bold ${getWinRateColor(comp.win_rate)}`}>
                      {comp.win_rate}%
                    </span>
                  </TableCell>
                  <TableCell>
                    {comp.trend === "stable" && <span className="text-slate-400">→ 稳定</span>}
                    {comp.trend === "improving" && <span className="text-green-500">↑ 提升</span>}
                    {comp.trend === "declining" && <span className="text-red-500">↓ 下降</span>}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {comp.strengths.slice(0, 2).map((s, i) => (
                        <Badge key={i} variant="secondary" className="text-xs">{s}</Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {comp.weaknesses.slice(0, 2).map((w, i) => (
                        <Badge key={i} variant="outline" className="text-xs text-red-400">{w}</Badge>
                      ))}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 竞争优势对比 */}
      <Card>
        <CardHeader>
          <CardTitle>竞争优势对比</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>竞争维度</TableHead>
                <TableHead>vs 竞品 A</TableHead>
                <TableHead>vs 竞品 B</TableHead>
                <TableHead>vs 竞品 C</TableHead>
                <TableHead>vs 竞品 D</TableHead>
                <TableHead>重要性</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {overview.advantages.map((adv, idx) => (
                <TableRow key={idx}>
                  <TableCell className="font-medium">{adv.name}</TableCell>
                  <TableCell>
                    <Badge variant={adv.vs_A === "优势" ? "default" : adv.vs_A === "劣势" ? "destructive" : "secondary"}>
                      {adv.vs_A}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={adv.vs_B === "优势" ? "default" : adv.vs_B === "劣势" ? "destructive" : "secondary"}>
                      {adv.vs_B}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={adv.vs_C === "优势" ? "default" : adv.vs_C === "劣势" ? "destructive" : "secondary"}>
                      {adv.vs_C}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={adv.vs_D === "优势" ? "default" : adv.vs_D === "劣势" ? "destructive" : "secondary"}>
                      {adv.vs_D}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{idx < 3 ? "高" : "中"}</Badge>
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

// 竞争策略建议
function StrategyRecommendations() {
  const [strategies, _setStrategies] = useState([
    {
      competitor: "竞品 A（德国知名）",
      win_rate: 71.1,
      strategy: "价格 + 服务双优势",
      tactics: [
        "强调价格低 15-20%，TCO 优势明显",
        "突出 2 小时响应 vs 竞品 A 的 48 小时",
        "强调交付周期快 30%",
        "提供标杆客户参观，弥补品牌劣势",
      ],
      sales_talks: [
        "我们价格比竞品 A 低 20%，性能相当，TCO 更低",
        "我们 2 小时响应，竞品 A 需要 48 小时",
        "我们交付周期 8 周，竞品 A 需要 12 周",
      ],
      pricing: "保持 15-20% 价格优势",
    },
    {
      competitor: "竞品 B（国内上市）",
      win_rate: 53.8,
      strategy: "技术 + 案例差异化",
      tactics: [
        "强调技术积累和专利优势",
        "展示同行业标杆案例",
        "突出定制化能力",
        "强调售后服务网络",
      ],
      sales_talks: [
        "我们有 50+ 专利，技术领先竞品 B 一代",
        "我们在宁德时代有成功案例，竞品 B 没有",
        "我们可以完全定制，竞品 B 只能标准方案",
      ],
      pricing: "与竞品 B 持平，强调价值",
    },
    {
      competitor: "竞品 C（新兴公司）",
      win_rate: 78.9,
      strategy: "品牌 + 稳定性压制",
      tactics: [
        "强调品牌实力和稳定性",
        "展示长期合作客户",
        "突出售后保障",
        "强调项目风险控制",
      ],
      sales_talks: [
        "我们成立 15 年，竞品 C 只有 3 年",
        "我们有 100+ 长期客户，返修率<1%",
        "我们提供 3 年质保，竞品 C 只有 1 年",
      ],
      pricing: "溢价 10-15%，强调价值",
    },
    {
      competitor: "竞品 D（台系厂商）",
      win_rate: 47.6,
      strategy: "加强性价比 + 电子行业案例",
      tactics: [
        "提升性价比，缩小价格差距",
        "加强电子行业案例建设",
        "强调本地化服务优势",
        "突出大项目经验",
      ],
      sales_talks: [
        "我们价格与竞品 D 相当，但配置更高",
        "我们有电子行业 20+ 案例",
        "我们大陆服务团队 50 人，竞品 D 只有 10 人",
      ],
      pricing: "与竞品 D 持平或略低 5%",
    },
  ]);

  return (
    <div className="space-y-6">
      {strategies.map((item, idx) => (
        <Card key={idx}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Sword className="w-5 h-5" />
                  {item.competitor}
                </CardTitle>
                <CardDescription>
                  当前赢单率：<span className={item.win_rate >= 70 ? "text-green-500" : item.win_rate >= 50 ? "text-blue-500" : "text-orange-500"}>{item.win_rate}%</span>
                </CardDescription>
              </div>
              <Badge variant="outline" className="text-sm">
                策略：{item.strategy}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <Target className="w-4 h-4" />
                  竞争战术
                </h4>
                <ul className="text-sm text-slate-400 space-y-1">
                  {item.tactics.map((tactic, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle className="w-3 h-3 mt-0.5 text-green-500" />
                      {tactic}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <Lightbulb className="w-4 h-4" />
                  销售话术
                </h4>
                <ul className="text-sm text-slate-400 space-y-1">
                  {item.sales_talks.map((talk, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Lightbulb className="w-3 h-3 mt-0.5 text-blue-500" />
                      {talk}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="mt-4 p-3 bg-slate-800 rounded">
              <div className="flex items-center gap-2 text-sm">
                <DollarSign className="w-4 h-4" />
                <span className="text-slate-400">定价策略：</span>
                <span className="font-medium">{item.pricing}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// 主页面
export default function CompetitorAnalysis() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="竞争对手分析"
          description="分析对不同竞品的赢单率，制定竞争策略"
          icon={<Sword className="w-6 h-6 text-orange-500" />}
        />

        <Tabs defaultValue="overview" className="mt-6">
          <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
            <TabsTrigger value="overview">
              <TrendingUp className="w-4 h-4 mr-2" />
              竞争总览
            </TabsTrigger>
            <TabsTrigger value="strategy">
              <Target className="w-4 h-4 mr-2" />
              竞争策略
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <CompetitorOverview />
          </TabsContent>

          <TabsContent value="strategy" className="mt-6">
            <StrategyRecommendations />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
