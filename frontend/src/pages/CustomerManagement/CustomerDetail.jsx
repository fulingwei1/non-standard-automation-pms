/**
 * 客户详情页 - 整合版
 * 功能：基本信息、关系成熟度、交互历史、商机合同、购买分析
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";




import { cn } from "../../lib/utils";
import api from "../../services/api";
import { toast } from "sonner";

const ROLE_COLORS = {
  EB: "bg-red-500",
  TB: "bg-blue-500",
  PB: "bg-green-500",
  UB: "bg-amber-500",
  COACH: "bg-purple-500",
};
const ROLE_NAMES = {
  EB: "最终决策人",
  TB: "技术决策人",
  PB: "采购决策人",
  UB: "最终用户",
  COACH: "内线",
};
const MATURITY_COLORS = {
  L1: "text-red-500",
  L2: "text-orange-500",
  L3: "text-yellow-500",
  L4: "text-blue-500",
  L5: "text-purple-500",
};

// 基本信息组件
function BasicInfoTab({ customer, decisionChain }) {
  if (!customer) return <EmptyState message="暂无数据" />;

  const getAttitudeIcon = (attitude) => {
    switch (attitude) {
      case "supportive": return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "resistant": return <AlertTriangle className="w-4 h-4 text-red-500" />;
      default: return <Activity className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* 客户基本资料 */}
      <Card>
        <CardHeader>
          <CardTitle>客户基本资料</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-slate-400 mb-1">客户名称</div>
              <div className="font-medium">{customer.customer_name}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">简称</div>
              <div className="font-medium">{customer.short_name || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">客户等级</div>
              <Badge variant={customer.customer_level === "A" ? "default" : "secondary"}>
                {customer.customer_level}级
              </Badge>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">行业</div>
              <div className="font-medium">{customer.industry || "-"}</div>
            </div>
            <div>
              <div className="text-sm text-slate-400 mb-1">类型</div>
              <div className="font-medium">{customer.customer_type || "-"}</div>
            </div>
            <div className="col-span-2">
              <div className="text-sm text-slate-400 mb-1">地址</div>
              <div className="flex items-center gap-2 font-medium">
                <MapPin className="w-4 h-4 text-slate-500" />
                {customer.basic_info?.address || "-"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 联系人管理（决策链）*/}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" />
            联系人管理（决策链）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>姓名</TableHead>
                <TableHead>职位</TableHead>
                <TableHead>决策角色</TableHead>
                <TableHead>态度</TableHead>
                <TableHead>关系强度</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(decisionChain?.contacts || []).map((contact, idx) => (
                <TableRow key={idx}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{contact.name}</span>
                      {contact.is_primary && (
                        <Badge variant="outline" className="text-xs bg-amber-500/20 text-amber-400 border-amber-500/30">
                          主联系人
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{contact.title || "-"}</TableCell>
                  <TableCell>
                    {contact.role ? (
                      <Badge className={ROLE_COLORS[contact.role]}>
                        {ROLE_NAMES[contact.role] || contact.role}
                      </Badge>
                    ) : (
                      <Badge variant="secondary">未分类</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getAttitudeIcon(contact.attitude)}
                      <span className="text-sm">
                        {contact.attitude === "supportive" ? "支持" :
                         contact.attitude === "resistant" ? "反对" :
                         contact.attitude === "neutral" ? "中立" : "未知"}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress value={contact.relationship || 0} className="w-20 h-2" />
                      <span className="text-sm w-8">{contact.relationship || 0}%</span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              {(!decisionChain?.contacts || decisionChain.contacts.length === 0) && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-slate-400 py-8">
                    暂无联系人数据
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// 关系成熟度组件
function MaturityTab({ healthScore }) {
  if (!healthScore) return <EmptyState message="暂无数据" />;

  const getStatusColor = (status) => {
    switch (status) {
      case "GOOD": return "text-green-500";
      case "MEDIUM": return "text-orange-500";
      case "POOR": return "text-red-500";
      default: return "text-slate-400";
    }
  };

  return (
    <div className="space-y-6">
      {/* 成熟度概览 */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6 text-center">
            <div className={cn("text-5xl font-bold mb-2", MATURITY_COLORS[healthScore.maturity_level] || "text-slate-400")}>
              {healthScore.overall_score}
            </div>
            <div className="text-slate-400 mb-2">成熟度总分</div>
            <Badge className={cn("mt-1", MATURITY_COLORS[healthScore.maturity_level])}>
              {healthScore.maturity_level} - {healthScore.maturity_level_name}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="text-5xl font-bold text-green-500 mb-2">
              {healthScore.estimated_win_rate}%
            </div>
            <div className="text-slate-400">预估赢单率</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="text-2xl font-bold mb-2">
              {healthScore.health_trend === "improving" ? "📈 上升" : "📊 稳定"}
            </div>
            <div className="text-slate-400">健康趋势</div>
          </CardContent>
        </Card>
      </div>

      {/* 六维度评分 */}
      <Card>
        <CardHeader>
          <CardTitle>六维度评分</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(healthScore.dimensions || []).map((dim, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm">{dim.name}</span>
                  <span className={cn("text-sm font-medium", getStatusColor(dim.status))}>
                    {dim.score} / {dim.max_score}
                    ({dim.status === "GOOD" ? "良好" : dim.status === "MEDIUM" ? "中等" : "待提升"})
                  </span>
                </div>
                <Progress value={Math.round((dim.score / dim.max_score) * 100)} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 交互历史组件
function TimelineTab({ timeline }) {
  if (!timeline) return <EmptyState message="暂无数据" />;

  const getTypeIcon = (type) => {
    switch (type) {
      case "meeting": return <Video className="w-4 h-4" />;
      case "call": return <Phone className="w-4 h-4" />;
      case "email": return <Mail className="w-4 h-4" />;
      case "wechat": return <MessageSquare className="w-4 h-4" />;
      default: return <Calendar className="w-4 h-4" />;
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case "positive": return "text-green-500 bg-green-500/10";
      case "negative": return "text-red-500 bg-red-500/10";
      default: return "text-slate-400 bg-slate-500/10";
    }
  };

  return (
    <div className="space-y-6">
      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <Activity className="w-6 h-6 mx-auto mb-2 text-blue-500" />
            <div className="text-2xl font-bold">{timeline.total_interactions || 0}</div>
            <div className="text-sm text-slate-400">总互动次数</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <Clock className="w-6 h-6 mx-auto mb-2 text-amber-500" />
            <div className={cn("text-2xl font-bold", timeline.days_since_last_contact > 14 ? "text-red-500" : "text-green-500")}>
              {timeline.days_since_last_contact || 0}天
            </div>
            <div className="text-sm text-slate-400">距上次联系</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <CheckCircle className="w-6 h-6 mx-auto mb-2 text-green-500" />
            <div className="text-2xl font-bold">{timeline.sentiment_distribution?.positive || 0}</div>
            <div className="text-sm text-slate-400">正面互动</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2 text-red-500" />
            <div className="text-2xl font-bold">{timeline.sentiment_distribution?.negative || 0}</div>
            <div className="text-sm text-slate-400">负面互动</div>
          </CardContent>
        </Card>
      </div>

      {/* 交互时间线 */}
      <Card>
        <CardHeader>
          <CardTitle>交互时间线</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(timeline.timeline || []).slice(0, 10).map((item, idx) => (
              <div key={idx} className="flex items-start gap-4 pb-4 border-b border-white/5 last:border-0">
                <div className={cn("p-2 rounded-full", getSentimentColor(item.sentiment))}>
                  {getTypeIcon(item.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <div className="font-medium">{item.title}</div>
                    <span className="text-sm text-slate-400">{item.date}</span>
                  </div>
                  {item.outcome && (
                    <div className="text-sm text-slate-400">{item.outcome}</div>
                  )}
                </div>
              </div>
            ))}
            {(!timeline.timeline || timeline.timeline.length === 0) && (
              <div className="text-center text-slate-400 py-8">暂无交互记录</div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 商机合同组件
function OpportunitiesTab({ customer }) {
  if (!customer) return <EmptyState message="暂无数据" />;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="w-5 h-5" />
          活跃商机
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>商机名称</TableHead>
              <TableHead>阶段</TableHead>
              <TableHead>预估金额</TableHead>
              <TableHead>赢单率</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(customer.active_opportunities || []).map((opp, idx) => (
              <TableRow key={idx}>
                <TableCell className="font-medium">{opp.name}</TableCell>
                <TableCell>
                  <Badge variant="outline">{opp.stage}</Badge>
                </TableCell>
                <TableCell>
                  {opp.estimated_amount ? `${(opp.estimated_amount / 10000).toFixed(1)} 万` : "-"}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Progress value={opp.win_rate || 0} className="w-20 h-2" />
                    <span className="text-sm">{opp.win_rate || 0}%</span>
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {(!customer.active_opportunities || customer.active_opportunities.length === 0) && (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-slate-400 py-8">
                  暂无活跃商机
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

// 购买分析组件
function BuyingTab({ buyingPreferences }) {
  if (!buyingPreferences) return <EmptyState message="暂无数据" />;

  const insights = buyingPreferences.historical_insights || {};

  return (
    <div className="space-y-6">
      {/* 历史统计 */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold">{insights.total_opportunities || 0}</div>
            <div className="text-sm text-slate-400">历史商机数</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold text-green-500">{insights.won_opportunities || 0}</div>
            <div className="text-sm text-slate-400">赢单数</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold">{insights.win_rate || 0}%</div>
            <div className="text-sm text-slate-400">历史赢单率</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 text-center">
            <div className="text-2xl font-bold">
              {((insights.avg_opportunity_value || 0) / 10000).toFixed(1)}万
            </div>
            <div className="text-sm text-slate-400">平均商机金额</div>
          </CardContent>
        </Card>
      </div>

      {/* 推荐跟进策略 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star className="w-5 h-5 text-amber-500" />
            推荐跟进策略
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            <li className="flex items-start gap-3">
              <ArrowRight className="w-4 h-4 text-green-500 mt-1" />
              <span className="text-sm">根据历史偏好，推荐重点跟进高价值商机</span>
            </li>
            <li className="flex items-start gap-3">
              <ArrowRight className="w-4 h-4 text-green-500 mt-1" />
              <span className="text-sm">保持定期沟通，维护客户关系</span>
            </li>
            <li className="flex items-start gap-3">
              <ArrowRight className="w-4 h-4 text-green-500 mt-1" />
              <span className="text-sm">关注客户需求变化，及时调整方案</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

// 主页面
const CustomerDetail = () => {
  const { id: customerId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("basic");
  const [customer, setCustomer] = useState(null);
  const [decisionChain, setDecisionChain] = useState(null);
  const [healthScore, setHealthScore] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [buyingPreferences, setBuyingPreferences] = useState(null);

  useEffect(() => {
    if (customerId) loadAllData();
  }, [customerId]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [customerRes, chainRes, healthRes, timelineRes, prefRes] = await Promise.all([
        api.get(`/api/v1/customer-360/customers/${customerId}/360-view`),
        api.get(`/api/v1/customer-360/customers/${customerId}/decision-chain`),
        api.get(`/api/v1/customer-360/customers/${customerId}/health-score`),
        api.get(`/api/v1/customer-360/customers/${customerId}/timeline`),
        api.get(`/api/v1/customer-360/customers/${customerId}/buying-preferences`),
      ]);
      setCustomer(customerRes.data);
      setDecisionChain(chainRes.data);
      setHealthScore(healthRes.data);
      setTimeline(timelineRes.data);
      setBuyingPreferences(prefRes.data);
    } catch (_error) {
      toast.error("加载客户数据失败");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => navigate("/sales/customers");

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950"
    >
      <div className="container mx-auto px-4 py-6">
        {/* 页头 */}
        <PageHeader
          title={
            <div className="flex items-center gap-3">
              <Building2 className="w-6 h-6 text-blue-500" />
              {customer?.customer_name || "客户详情"}
              {customer?.customer_level && (
                <Badge variant={customer.customer_level === "A" ? "default" : "secondary"}>
                  {customer.customer_level}级客户
                </Badge>
              )}
              {healthScore?.maturity_level && (
                <Badge className={MATURITY_COLORS[healthScore.maturity_level]}>
                  {healthScore.maturity_level}
                </Badge>
              )}
            </div>
          }
          description="客户全景信息：基本资料、关系成熟度、交互历史、商机合同"
          actions={
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                返回列表
              </Button>
              <Button variant="outline" onClick={loadAllData}>
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新
              </Button>
            </div>
          }
        />

        {/* Tabs 内容 */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
          <TabsList className="grid w-full grid-cols-5 lg:w-[700px]">
            <TabsTrigger value="basic">
              <Building2 className="w-4 h-4 mr-2" />
              基本信息
            </TabsTrigger>
            <TabsTrigger value="maturity">
              <Activity className="w-4 h-4 mr-2" />
              关系成熟度
            </TabsTrigger>
            <TabsTrigger value="timeline">
              <Clock className="w-4 h-4 mr-2" />
              交互历史
            </TabsTrigger>
            <TabsTrigger value="opportunities">
              <Target className="w-4 h-4 mr-2" />
              商机合同
            </TabsTrigger>
            <TabsTrigger value="buying">
              <TrendingUp className="w-4 h-4 mr-2" />
              购买分析
            </TabsTrigger>
          </TabsList>

          <TabsContent value="basic">
            <BasicInfoTab customer={customer} decisionChain={decisionChain} />
          </TabsContent>

          <TabsContent value="maturity">
            <MaturityTab healthScore={healthScore} />
          </TabsContent>

          <TabsContent value="timeline">
            <TimelineTab timeline={timeline} />
          </TabsContent>

          <TabsContent value="opportunities">
            <OpportunitiesTab customer={customer} />
          </TabsContent>

          <TabsContent value="buying">
            <BuyingTab buyingPreferences={buyingPreferences} />
          </TabsContent>
        </Tabs>
      </div>
    </motion.div>
  );
};

export default CustomerDetail;
