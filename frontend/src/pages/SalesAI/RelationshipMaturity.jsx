/**
 * 商务关系成熟度评估页面
 */

import { useEffect, useMemo, useState } from "react";
import {
  Users,
  Target,
  Heart,
  AlertTriangle,
  CheckCircle,
  ArrowUp,
  Activity,
  RefreshCw,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Badge,
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Button,
} from "../../components/ui";
import { relationshipMaturityApi } from "../../services/api/relationshipMaturity";

const unwrapData = (response) => response?.data?.data ?? response?.data ?? {};

const levelClassName = (level) => {
  const classes = {
    L1: "text-slate-500 border-slate-300",
    L2: "text-blue-500 border-blue-300",
    L3: "text-green-600 border-green-300",
    L4: "text-indigo-600 border-indigo-300",
    L5: "text-purple-600 border-purple-300",
  };
  return classes[level] || classes.L1;
};

const formatCurrency = (value) => {
  const numberValue = Number(value || 0);
  if (!Number.isFinite(numberValue) || numberValue <= 0) {
    return "-";
  }
  if (numberValue >= 100000000) {
    return `¥${(numberValue / 100000000).toFixed(1)}亿`;
  }
  if (numberValue >= 10000) {
    return `¥${(numberValue / 10000).toFixed(0)}万`;
  }
  return `¥${numberValue.toFixed(0)}`;
};

function RelationshipAssessment({ customerId, refreshKey }) {
  const [assessment, setAssessment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadAssessment = async () => {
      if (!customerId) {
        setAssessment(null);
        return;
      }

      setLoading(true);
      setError("");
      try {
        const response = await relationshipMaturityApi.assessment(customerId);
        if (!cancelled) {
          setAssessment(unwrapData(response));
        }
      } catch (err) {
        if (!cancelled) {
          setAssessment(null);
          setError(err?.response?.data?.detail || "关系成熟度数据读取失败");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadAssessment();
    return () => {
      cancelled = true;
    };
  }, [customerId, refreshKey]);

  const overall = assessment?.overall_assessment || {};
  const radarData = assessment?.radar_data || [];
  const recommendations = assessment?.improvement_recommendations || [];

  if (loading) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-slate-500">加载中...</CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-red-500">{error}</CardContent>
      </Card>
    );
  }

  if (!assessment) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-slate-500">暂无关系成熟度数据</CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-4 gap-4">
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>{assessment.customer_name || `客户 #${assessment.customer_id}`}</CardTitle>
            <CardDescription>关系成熟度评估</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div>
                <div className="text-4xl font-bold text-indigo-600">
                  {overall.total_score || 0}
                </div>
                <div className="text-sm text-slate-400">总分 (100)</div>
              </div>
              <div className="flex-1">
                <Progress value={overall.total_score || 0} className="h-3" />
              </div>
              <Badge className={levelClassName(overall.maturity_level)}>
                {overall.maturity_level || "L1"} - {overall.maturity_level_name || "未评级"}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">预估赢单率</div>
            <div className="text-3xl font-bold text-green-600">
              {overall.estimated_win_rate || 0}%
            </div>
            <div className="text-xs text-slate-400 mt-1">基于关系成熟度</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">评分来源</div>
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-500" />
              <span className="text-base font-semibold">{assessment.data_source || "service"}</span>
            </div>
            <div className="text-xs text-slate-400 mt-1">{assessment.assessment_date}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>六维度评估</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {radarData.map((dim) => (
              <Card key={dim.dimension}>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{dim.dimension}</span>
                    <span className="text-sm text-slate-400">
                      {dim.score}/{dim.max}
                    </span>
                  </div>
                  <Progress value={dim.percentage} className="h-2" />
                  <div className="text-xs text-slate-400 mt-1">{dim.percentage}%</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            改进建议
          </CardTitle>
        </CardHeader>
        <CardContent>
          {recommendations.length === 0 ? (
            <div className="text-sm text-slate-500">暂无改进建议</div>
          ) : (
            <div className="space-y-4">
              {recommendations.map((item) => (
                <div key={`${item.priority}-${item.dimension}`} className="flex items-start gap-3 p-3 border rounded">
                  {item.priority === 1 ? (
                    <AlertTriangle className="w-5 h-5 text-orange-500 mt-0.5" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-indigo-500 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <div className="font-medium">{item.action}</div>
                    <div className="text-sm text-slate-500">{item.dimension}</div>
                    <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                      <span>
                        {item.current_score} → {item.target_score}
                      </span>
                      <span>{item.expected_impact}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PortfolioAnalysis({ refreshKey }) {
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadPortfolio = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await relationshipMaturityApi.portfolio();
        if (!cancelled) {
          setPortfolio(unwrapData(response));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err?.response?.data?.detail || "客户组合数据读取失败");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadPortfolio();
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const distribution = useMemo(
    () => Object.values(portfolio?.maturity_distribution || {}),
    [portfolio],
  );
  const keyAccounts = portfolio?.key_accounts || [];

  if (loading) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-slate-500">加载中...</CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-red-500">{error}</CardContent>
      </Card>
    );
  }

  if (!portfolio) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-slate-500">暂无客户组合数据</CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>客户成熟度分布</CardTitle>
          <CardDescription>
            总客户数：{portfolio.total_customers || 0} · 健康度（L3+）：
            {portfolio.health_assessment?.healthy_percentage || 0}%
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {distribution.map((dist) => (
              <Card key={dist.level}>
                <CardContent className="pt-4 text-center">
                  <div className="text-2xl font-bold text-indigo-600">{dist.count}</div>
                  <div className="text-xs text-slate-400">{dist.name}</div>
                  <div className="text-xs text-slate-400">{dist.percentage}%</div>
                  <div className="text-xs text-slate-400 mt-1">
                    赢单率{dist.avg_win_rate || 0}%
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>重点客户关系</CardTitle>
        </CardHeader>
        <CardContent>
          {keyAccounts.length === 0 ? (
            <div className="text-sm text-slate-500">暂无评分记录</div>
          ) : (
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
                {keyAccounts.map((account) => (
                  <TableRow key={account.customer_id}>
                    <TableCell className="font-medium">{account.customer_name}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className={levelClassName(account.maturity_level)}>
                        {account.maturity_level}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className={account.score >= 70 ? "text-green-600" : account.score >= 50 ? "text-indigo-600" : "text-orange-600"}>
                        {account.score}
                      </span>
                    </TableCell>
                    <TableCell>{formatCurrency(account.revenue_potential)}</TableCell>
                    <TableCell>
                      <Badge variant={account.estimated_win_rate >= 65 ? "default" : "secondary"}>
                        {account.estimated_win_rate || 0}%
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {account.score >= 70 ? (
                        <ArrowUp className="w-4 h-4 text-green-500" />
                      ) : (
                        <Activity className="w-4 h-4 text-slate-400" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function RelationshipMaturity() {
  const [customerId, setCustomerId] = useState(1);
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="商务关系成熟度"
          description="评估客户关系深度，预测赢单概率"
          icon={<Heart className="w-6 h-6 text-pink-500" />}
        />

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <label className="text-sm font-medium text-slate-600" htmlFor="relationship-customer-id">
            客户ID
          </label>
          <input
            id="relationship-customer-id"
            className="h-9 w-28 rounded border border-slate-300 px-3 text-sm"
            type="number"
            min="1"
            value={customerId}
            onChange={(event) => setCustomerId(Number(event.target.value || 0))}
          />
          <Button type="button" variant="outline" onClick={() => setRefreshKey((value) => value + 1)}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>

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
            <RelationshipAssessment customerId={customerId} refreshKey={refreshKey} />
          </TabsContent>

          <TabsContent value="portfolio" className="mt-6">
            <PortfolioAnalysis refreshKey={refreshKey} />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
