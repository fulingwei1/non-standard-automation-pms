/**
 * 智能报价页面
 * 
 * 功能：
 * 1. 历史价格参考
 * 2. 竞品价格对比
 * 3. 最优价格建议
 * 4. 自动折扣计算
 * 5. 赢单率预测
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  DollarSign,
  Target,
  Percent,
  Award,
  BarChart3,
  AlertCircle,
  CheckCircle,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui";
import { intelligentQuoteApi } from "../../services/api";

// 历史价格参考
function HistoricalPrices() {
  const [productCategory, setProductCategory] = useState("FCT");
  const [data, setData] = useState(null);

  const fetchData = async () => {
    try {
      const res = await intelligentQuoteApi.getHistoricalPrices(productCategory);
      setData(res);
    } catch (error) {
      console.error("获取历史价格失败:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, [productCategory]);

  return (
    <div className="space-y-4">
      <Select value={productCategory} onValueChange={setProductCategory}>
        <SelectTrigger className="w-[200px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="FCT">FCT</SelectItem>
          <SelectItem value="ICT">ICT</SelectItem>
          <SelectItem value="EOL">EOL</SelectItem>
          <SelectItem value="VISION">视觉检测</SelectItem>
        </SelectContent>
      </Select>

      {data && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">平均成交价</div>
                <div className="text-2xl font-bold">¥{(data.average_price / 10000).toFixed(0)}万</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">价格区间</div>
                <div className="text-2xl font-bold">
                  ¥{(data.price_range.min / 10000).toFixed(0)}-{((data.price_range.max) / 10000).toFixed(0)}万
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">匹配项目</div>
                <div className="text-2xl font-bold">{data.matched_count}个</div>
              </CardContent>
            </Card>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>项目名称</TableHead>
                <TableHead>成交价</TableHead>
                <TableHead>原价</TableHead>
                <TableHead>折扣率</TableHead>
                <TableHead>成交时间</TableHead>
                <TableHead>相似度</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.historical_prices.map((item, idx) => (
                <TableRow key={idx}>
                  <TableCell>{item.project_name}</TableCell>
                  <TableCell>¥{(item.final_price / 10000).toFixed(0)}万</TableCell>
                  <TableCell className="text-slate-400">¥{(item.original_quote / 10000).toFixed(0)}万</TableCell>
                  <TableCell>{item.discount_rate}%</TableCell>
                  <TableCell>{item.deal_date}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{item.similarity}</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </>
      )}
    </div>
  );
}

// 赢单率预测
function WinRatePrediction() {
  const [predictions, _setPredictions] = useState([
    { opportunity_id: 101, opportunity_name: "宁德时代FCT项目", win_rate: 75, risk_level: "LOW" },
    { opportunity_id: 102, opportunity_name: "比亚迪EOL项目", win_rate: 60, risk_level: "MEDIUM" },
    { opportunity_id: 103, opportunity_name: "中创新航ICT项目", win_rate: 45, risk_level: "HIGH" },
  ]);

  return (
    <div className="space-y-4">
      {predictions.map((pred, idx) => (
        <Card key={idx}>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="font-medium">{pred.opportunity_name}</div>
                <div className="text-sm text-slate-400">商机ID: {pred.opportunity_id}</div>
              </div>
              <Badge
                variant={pred.risk_level === "LOW" ? "default" : pred.risk_level === "MEDIUM" ? "secondary" : "destructive"}
              >
                {pred.risk_level === "LOW" ? "低风险" : pred.risk_level === "MEDIUM" ? "中风险" : "高风险"}
              </Badge>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <Progress value={pred.win_rate} className="h-3" />
              </div>
              <div className="text-2xl font-bold w-20 text-right">{pred.win_rate}%</div>
            </div>
            <div className="mt-4 flex gap-2">
              <Button size="sm" variant="outline">查看详情</Button>
              <Button size="sm">提升赢单率</Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// 最优价格建议
function OptimalPriceSuggestion() {
  const [suggestion, _setSuggestion] = useState({
    optimal_price: 3200000,
    optimal_win_rate: 70,
    optimal_margin: 32,
    suggestion: "平衡方案，推荐",
    price_scenarios: [
      { price: 2800000, win_rate: 85, margin_rate: 25, suggestion: "激进低价，快速抢占市场" },
      { price: 3200000, win_rate: 70, margin_rate: 32, suggestion: "平衡方案，推荐" },
      { price: 3500000, win_rate: 55, margin_rate: 38, suggestion: "标准报价" },
      { price: 3800000, win_rate: 35, margin_rate: 42, suggestion: "利润优先，风险较高" },
    ],
  });

  return (
    <div className="space-y-4">
      <Card className="border-purple-500">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-purple-500">
            <Award className="w-5 h-5" />
            AI推荐最优方案
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div>
              <div className="text-sm text-slate-400">建议价格</div>
              <div className="text-2xl font-bold text-purple-500">
                ¥{(suggestion.optimal_price / 10000).toFixed(0)}万
              </div>
            </div>
            <div>
              <div className="text-sm text-slate-400">预期赢单率</div>
              <div className="text-2xl font-bold text-green-500">{suggestion.optimal_win_rate}%</div>
            </div>
            <div>
              <div className="text-sm text-slate-400">预期毛利率</div>
              <div className="text-2xl font-bold text-blue-500">{suggestion.optimal_margin}%</div>
            </div>
          </div>
          <Alert className="bg-purple-500/10 border-purple-500">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>{suggestion.suggestion}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        {suggestion.price_scenarios.map((scenario, idx) => (
          <Card
            key={idx}
            className={
              scenario.price === suggestion.optimal_price
                ? "border-purple-500 bg-purple-500/5"
                : ""
            }
          >
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-24">
                    <div className="text-lg font-bold">¥{(scenario.price / 10000).toFixed(0)}万</div>
                  </div>
                  <div className="flex gap-4 text-sm">
                    <div>
                      <span className="text-slate-400">赢单率:</span>{" "}
                      <span className={scenario.win_rate >= 70 ? "text-green-500" : "text-orange-500"}>
                        {scenario.win_rate}%
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400">毛利率:</span>{" "}
                      <span>{scenario.margin_rate}%</span>
                    </div>
                  </div>
                </div>
                {scenario.price === suggestion.optimal_price && (
                  <Badge className="bg-purple-500">AI推荐</Badge>
                )}
              </div>
              <div className="mt-2 text-sm text-slate-400">{scenario.suggestion}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// 主页面
export default function IntelligentQuote() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="智能报价"
          description="AI驱动的报价决策支持，提供历史价格参考、赢单率预测、最优价格建议"
          icon={<DollarSign className="w-6 h-6 text-green-500" />}
        />

        <Tabs defaultValue="optimal" className="mt-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[450px]">
            <TabsTrigger value="optimal">
              <Target className="w-4 h-4 mr-2" />
              最优价格
            </TabsTrigger>
            <TabsTrigger value="historical">
              <BarChart3 className="w-4 h-4 mr-2" />
              历史价格
            </TabsTrigger>
            <TabsTrigger value="winrate">
              <TrendingUp className="w-4 h-4 mr-2" />
              赢单预测
            </TabsTrigger>
          </TabsList>

          <TabsContent value="optimal" className="mt-6">
            <OptimalPriceSuggestion />
          </TabsContent>

          <TabsContent value="historical" className="mt-6">
            <HistoricalPrices />
          </TabsContent>

          <TabsContent value="winrate" className="mt-6">
            <WinRatePrediction />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
