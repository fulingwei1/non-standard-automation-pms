/**
 * AI销售助手页面
 * 
 * 功能：
 * 1. AI话术推荐
 * 2. AI方案生成
 * 3. 竞品分析
 * 4. 谈判建议
 * 5. 流失风险预警
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Sparkles,
  MessageSquare,
  FileText,
  Target,
  AlertTriangle,
  TrendingUp,
  Copy,
  RefreshCw,
  ChevronRight,
  Users,
  Lightbulb,
  ShieldAlert,
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
  Alert,
  AlertTitle,
  AlertDescription,
  Progress,
} from "../../components/ui";
import { aiSalesApi } from "../../services/api";

// 话术推荐组件
function ScriptRecommendation() {
  const [customerId, _setCustomerId] = useState("1");
  const [scenario, setScenario] = useState("初次接触");
  const [loading, setLoading] = useState(false);
  const [scripts, setScripts] = useState([]);

  const scenarios = [
    "初次接触",
    "需求挖掘",
    "方案介绍",
    "价格谈判",
    "异议处理",
    "成交促成",
  ];

  const fetchScripts = async () => {
    setLoading(true);
    try {
      const res = await aiSalesApi.recommendScripts(customerId, null, scenario);
      setScripts(res.recommended_scripts || []);
    } catch (error) {
      console.error("获取话术失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScripts();
  }, [scenario]);

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Select value={scenario || "unknown"} onValueChange={setScenario}>
          <SelectTrigger className="w-[200px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {scenarios.map((s) => (
              <SelectItem key={s} value={s || "unknown"}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button onClick={fetchScripts} disabled={loading}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          刷新推荐
        </Button>
      </div>

      <div className="grid gap-4">
        {scripts.map((script, idx) => (
          <Card key={idx} className={script.is_recommended ? "border-purple-500" : ""}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{script.title}</CardTitle>
                <Badge variant={script.match_score > 90 ? "default" : "secondary"}>
                  匹配度 {script.match_score}%
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-300 mb-3">{script.content}</p>
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-400">
                  成功率: {script.success_rate}% | 使用次数: {script.usage_count}
                </div>
                <Button variant="outline" size="sm" onClick={() => navigator.clipboard.writeText(script.content)}>
                  <Copy className="w-3 h-3 mr-1" />
                  复制
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// 方案生成组件
function ProposalGeneration() {
  const [opportunityId, _setOpportunityId] = useState("101");
  const [proposalType, setProposalType] = useState("technical");
  const [loading, setLoading] = useState(false);
  const [proposal, setProposal] = useState(null);

  const generateProposal = async () => {
    setLoading(true);
    try {
      const res = await aiSalesApi.generateProposal(opportunityId, proposalType);
      setProposal(res);
    } catch (error) {
      console.error("生成方案失败:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Select value={proposalType || "unknown"} onValueChange={setProposalType}>
          <SelectTrigger className="w-[200px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="technical">技术方案</SelectItem>
            <SelectItem value="business">商务方案</SelectItem>
          </SelectContent>
        </Select>
        <Button onClick={generateProposal} disabled={loading}>
          <Sparkles className={`w-4 h-4 mr-2 ${loading ? "animate-pulse" : ""}`} />
          {loading ? "生成中..." : "生成方案"}
        </Button>
      </div>

      {proposal && (
        <Card>
          <CardHeader>
            <CardTitle>{proposal.title}</CardTitle>
            <CardDescription>
              参考项目: {proposal.reference_projects?.map(p => p.name).join(", ")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {proposal.generated_content?.sections?.map((section, idx) => (
                <div key={idx}>
                  <h4 className="font-medium text-slate-200 mb-1">{section.title}</h4>
                  <p className="text-sm text-slate-400">{section.content}</p>
                </div>
              ))}
            </div>
            <div className="flex gap-2 mt-4">
              <Button size="sm">
                <FileText className="w-3 h-3 mr-1" />
                导出PDF
              </Button>
              <Button variant="outline" size="sm">
                <Copy className="w-3 h-3 mr-1" />
                复制内容
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// 竞品分析组件
function CompetitorAnalysis() {
  const [competitorName, setCompetitorName] = useState("");
  const [analysis, setAnalysis] = useState(null);

  const analyze = async () => {
    if (!competitorName) return;
    try {
      const res = await aiSalesApi.analyzeCompetitor(competitorName);
      setAnalysis(res);
    } catch (error) {
      console.error("分析失败:", error);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <input
          type="text"
          placeholder="输入竞品公司名称"
          className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2"
          value={competitorName || "unknown"}
          onChange={(e) => setCompetitorName(e.target.value)}
        />
        <Button onClick={analyze}>
          <Target className="w-4 h-4 mr-2" />
          分析
        </Button>
      </div>

      {analysis && (
        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                交锋记录
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-400">总交锋</div>
                  <div className="text-2xl font-bold">{analysis.competitor_info.encounter_count}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400">我们赢单</div>
                  <div className="text-2xl font-bold text-green-500">{analysis.competitor_info.our_wins}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400">对手赢单</div>
                  <div className="text-2xl font-bold text-red-500">{analysis.competitor_info.our_losses}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400">胜率</div>
                  <div className="text-2xl font-bold text-blue-500">{analysis.competitor_info.win_rate}%</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5" />
                我们的优势
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {analysis.our_advantages.map((adv, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <ChevronRight className="w-4 h-4 text-green-500 mt-0.5" />
                    {adv}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>应对策略</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {analysis.recommended_strategy.map((strategy, idx) => (
                  <Alert key={idx}>
                    <Lightbulb className="h-4 w-4" />
                    <AlertDescription>{strategy}</AlertDescription>
                  </Alert>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

// 流失风险组件
function ChurnRisk() {
  const [riskList, setRiskList] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchRiskList = async () => {
    setLoading(true);
    try {
      const res = await aiSalesApi.getChurnRiskList();
      setRiskList(res.risk_list || []);
    } catch (error) {
      console.error("获取风险列表失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskList();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="text-sm text-slate-400">
          高风险客户需立即关注
        </div>
        <Button variant="outline" size="sm" onClick={fetchRiskList}>
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          刷新
        </Button>
      </div>

      <div className="grid gap-4">
        {riskList.map((risk, idx) => (
          <Card
            key={idx}
            className={
              risk.risk_level === "HIGH"
                ? "border-red-500 bg-red-500/5"
                : risk.risk_level === "MEDIUM"
                ? "border-orange-500 bg-orange-500/5"
                : "border-green-500 bg-green-500/5"
            }
          >
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {risk.risk_level === "HIGH" ? (
                    <ShieldAlert className="w-6 h-6 text-red-500" />
                  ) : risk.risk_level === "MEDIUM" ? (
                    <AlertTriangle className="w-6 h-6 text-orange-500" />
                  ) : (
                    <ShieldAlert className="w-6 h-6 text-green-500" />
                  )}
                  <div>
                    <div className="font-medium">{risk.customer_name}</div>
                    <div className="text-sm text-slate-400">
                      {risk.risk_factors?.map(f => f.factor).join(", ")}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <Badge
                    variant={risk.risk_level === "HIGH" ? "destructive" : "secondary"}
                  >
                    风险 {risk.risk_score}分
                  </Badge>
                  <div className="text-xs text-slate-400 mt-1">
                    {risk.risk_level === "HIGH" ? "立即处理" : risk.risk_level === "MEDIUM" ? "需要关注" : "正常"}
                  </div>
                </div>
              </div>
              <Progress
                value={risk.risk_score}
                className="mt-3 h-2"
              />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// 主页面
export default function SalesAIAssistant() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="AI 销售助手"
          description="AI 驱动的销售辅助工具，提供话术推荐、方案生成、竞品分析等功能"
          icon={<Sparkles className="w-6 h-6 text-purple-500" />}
        />

        <Tabs defaultValue="scripts" className="mt-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
            <TabsTrigger value="scripts">
              <MessageSquare className="w-4 h-4 mr-2" />
              话术推荐
            </TabsTrigger>
            <TabsTrigger value="proposal">
              <FileText className="w-4 h-4 mr-2" />
              方案生成
            </TabsTrigger>
            <TabsTrigger value="competitor">
              <Target className="w-4 h-4 mr-2" />
              竞品分析
            </TabsTrigger>
            <TabsTrigger value="churn">
              <AlertTriangle className="w-4 h-4 mr-2" />
              流失预警
            </TabsTrigger>
          </TabsList>

          <TabsContent value="scripts" className="mt-6">
            <ScriptRecommendation />
          </TabsContent>

          <TabsContent value="proposal" className="mt-6">
            <ProposalGeneration />
          </TabsContent>

          <TabsContent value="competitor" className="mt-6">
            <CompetitorAnalysis />
          </TabsContent>

          <TabsContent value="churn" className="mt-6">
            <ChurnRisk />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
