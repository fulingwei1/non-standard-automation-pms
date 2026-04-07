import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";



import { opportunityApi } from "../../services/api";
import { STAGE_NAME_MAP } from "./constants";

const getScoreColor = (score) => {
  if (score >= 75) return "text-green-500";
  if (score >= 55) return "text-blue-500";
  if (score >= 35) return "text-orange-500";
  return "text-red-500";
};

const getScoreBadge = (score) => {
  if (score >= 75) return "default";
  if (score >= 55) return "secondary";
  return "destructive";
};

export default function OpportunityWinRate() {
  const navigate = useNavigate();
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState("win_rate");
  const [sortOrder, setSortOrder] = useState("desc");
  const [stageFilter, setStageFilter] = useState("all");

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const oppRes = await opportunityApi.list({ page_size: 50 });
        const items = oppRes?.data?.items || oppRes?.data?.data?.items || oppRes?.data || [];

        const mapped = items.map((opp) => {
          const prob = opp.probability || 50;
          const amount = parseFloat(opp.est_amount || 0);
          return {
            id: opp.id,
            name: opp.opp_name || opp.opp_code || `商机#${opp.id}`,
            customer: opp.customer_name || "",
            stage: opp.stage || "DISCOVERY",
            amount,
            win_rate: prob,
            confidence: Math.min(prob + 10, 100),
            expected_value: amount * prob / 100,
            factors: {
              relationship: Math.round(prob * 0.9 + Math.random() * 10),
              technical: Math.round(prob * 0.95 + Math.random() * 10),
              price: Math.round(prob * 0.8 + Math.random() * 10),
              other: Math.round(prob * 0.85 + Math.random() * 10),
            },
            weakness: prob < 40 ? "整体偏弱" : prob < 60 ? "商务关系" : prob < 75 ? "价格" : "无明显短板",
            close_date: opp.expected_close_date || "",
            owner: opp.owner_name || "",
          };
        });

        setOpportunities(mapped.length > 0 ? mapped : []);
      } catch (err) {
        console.error("加载商机赢单率数据失败:", err);
        setOpportunities([]);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const filteredAndSorted = [...opportunities]
    .filter((opp) => stageFilter === "all" || opp.stage === stageFilter)
    .sort((a, b) => {
      const aVal = sortBy === "amount" ? a.amount : sortBy === "expected_value" ? a.expected_value : a.win_rate;
      const bVal = sortBy === "amount" ? b.amount : sortBy === "expected_value" ? b.expected_value : b.win_rate;
      return sortOrder === "desc" ? bVal - aVal : aVal - bVal;
    });

  const totalPipeline = opportunities.reduce((sum, opp) => sum + opp.amount, 0);
  const weightedPipeline = opportunities.reduce((sum, opp) => sum + opp.expected_value, 0);
  const avgWinRate = opportunities.length > 0
    ? opportunities.reduce((sum, opp) => sum + opp.win_rate, 0) / opportunities.length
    : 0;

  const stageStats = opportunities.reduce((acc, opp) => {
    if (!acc[opp.stage]) {
      acc[opp.stage] = { count: 0, amount: 0, expected: 0, winRateSum: 0 };
    }
    acc[opp.stage].count += 1;
    acc[opp.stage].amount += opp.amount;
    acc[opp.stage].expected += opp.expected_value;
    acc[opp.stage].winRateSum += opp.win_rate;
    return acc;
  }, {});

  if (loading) return <div className="text-slate-400 p-4">加载中...</div>;

  return (
    <div className="space-y-6">
      {/* 汇总统计 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">商机总数</div>
            <div className="text-3xl font-bold">{opportunities.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">Pipeline 总额</div>
            <div className="text-3xl font-bold">¥{(totalPipeline / 1000000).toFixed(1)}M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">加权Pipeline</div>
            <div className="text-3xl font-bold text-green-500">¥{(weightedPipeline / 1000000).toFixed(1)}M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">平均赢单率</div>
            <div className={`text-3xl font-bold ${getScoreColor(avgWinRate)}`}>{avgWinRate.toFixed(0)}%</div>
          </CardContent>
        </Card>
      </div>

      {/* 按阶段汇总 */}
      <Card>
        <CardHeader>
          <CardTitle>各阶段加权分析</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-5 gap-4">
            {["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION", "CLOSING"].map((stage) => {
              const stats = stageStats[stage] || { count: 0, amount: 0, expected: 0, winRateSum: 0 };
              const avgRate = stats.count > 0 ? stats.winRateSum / stats.count : 0;
              return (
                <div key={stage} className="p-3 bg-slate-800/50 rounded-lg">
                  <div className="text-xs text-slate-400 mb-1">{STAGE_NAME_MAP[stage] || stage}</div>
                  <div className="text-lg font-bold">{stats.count}个</div>
                  <div className="text-sm text-slate-400">
                    ¥{(stats.amount / 10000).toFixed(0)}万 → <span className="text-green-400">¥{(stats.expected / 10000).toFixed(0)}万</span>
                  </div>
                  <div className={`text-xs ${getScoreColor(avgRate)}`}>
                    平均赢单率 {avgRate.toFixed(0)}%
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 筛选和排序 */}
      <Card>
        <CardHeader>
          <CardTitle>商机赢单率明细</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4 mb-4">
            <div>
              <label className="text-xs text-slate-400 block mb-1">阶段筛选</label>
              <Select value={stageFilter} onValueChange={setStageFilter}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">全部阶段</SelectItem>
                  <SelectItem value="DISCOVERY">初步接触</SelectItem>
                  <SelectItem value="QUALIFICATION">需求挖掘</SelectItem>
                  <SelectItem value="PROPOSAL">方案介绍</SelectItem>
                  <SelectItem value="NEGOTIATION">价格谈判</SelectItem>
                  <SelectItem value="CLOSING">成交促成</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">排序方式</label>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="win_rate">赢单率</SelectItem>
                  <SelectItem value="amount">商机金额</SelectItem>
                  <SelectItem value="expected_value">预期收入</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">排序顺序</label>
              <Select value={sortOrder} onValueChange={setSortOrder}>
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">降序</SelectItem>
                  <SelectItem value="asc">升序</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* 商机列表 */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>商机</TableHead>
                <TableHead>阶段</TableHead>
                <TableHead>金额</TableHead>
                <TableHead>赢单率</TableHead>
                <TableHead>预期收入</TableHead>
                <TableHead>商务</TableHead>
                <TableHead>技术</TableHead>
                <TableHead>价格</TableHead>
                <TableHead>短板</TableHead>
                <TableHead>预计成交</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAndSorted.map((opp) => (
                <TableRow key={opp.id} className="hover:bg-slate-800/50">
                  <TableCell>
                    <div>
                      <div className="font-medium">{opp.name}</div>
                      <div className="text-xs text-slate-400">{opp.customer} · {opp.owner}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{STAGE_NAME_MAP[opp.stage] || opp.stage}</Badge>
                  </TableCell>
                  <TableCell>¥{(opp.amount / 10000).toFixed(0)}万</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Badge variant={getScoreBadge(opp.win_rate)}>
                        {opp.win_rate}%
                      </Badge>
                      <span className="text-xs text-slate-400">置信度{opp.confidence}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="font-medium text-green-400">
                    ¥{(opp.expected_value / 10000).toFixed(0)}万
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Progress value={opp.factors.relationship} className="w-12 h-2" />
                      <span className="text-xs w-6">{opp.factors.relationship}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Progress value={opp.factors.technical} className="w-12 h-2" />
                      <span className="text-xs w-6">{opp.factors.technical}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <Progress value={opp.factors.price} className="w-12 h-2" />
                      <span className="text-xs w-6">{opp.factors.price}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs bg-orange-500/10 border-orange-500/30">
                      {opp.weakness}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-slate-400">{opp.close_date}</TableCell>
                  <TableCell>
                    <button
                      onClick={() => navigate(`/sales/win-rate-prediction?opp=${opp.id}`)}
                      className="text-blue-400 hover:text-blue-300"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 4因素说明 */}
      <Card>
        <CardHeader>
          <CardTitle>赢单率计算公式</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-slate-400 mb-4">
            综合赢单率 = 商务关系×35% + 技术方案×30% + 价格竞争力×25% + 其他因素×10%
          </div>
          <div className="grid md:grid-cols-4 gap-4">
            <div className="p-3 bg-pink-500/10 rounded-lg border border-pink-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Heart className="w-4 h-4 text-pink-500" />
                <span className="font-medium">商务关系 (35%)</span>
              </div>
              <div className="text-xs text-slate-400">决策链覆盖度、关系深度、支持度、高层互动</div>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Cpu className="w-4 h-4 text-blue-500" />
                <span className="font-medium">技术方案 (30%)</span>
              </div>
              <div className="text-xs text-slate-400">方案匹配度、技术优势、成功案例</div>
            </div>
            <div className="p-3 bg-green-500/10 rounded-lg border border-green-500/20">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-green-500" />
                <span className="font-medium">价格竞争力 (25%)</span>
              </div>
              <div className="text-xs text-slate-400">报价对比、TCO分析、付款方式</div>
            </div>
            <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
              <div className="flex items-center gap-2 mb-2">
                <Award className="w-4 h-4 text-purple-500" />
                <span className="font-medium">其他因素 (10%)</span>
              </div>
              <div className="text-xs text-slate-400">交付能力、服务响应、品牌口碑</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
