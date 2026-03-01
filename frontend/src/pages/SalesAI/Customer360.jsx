/**
 * 客户 360°画像页面
 * 
 * 功能：
 * 1. 交互历史时间线
 * 2. 决策链分析
 * 3. 健康度评分
 * 4. 购买偏好
 */

import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Users,
  TrendingUp,
  Heart,
  ShoppingCart,
  Calendar,
  Phone,
  Mail,
  MessageSquare,
  Video,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Target,
  Star,
  Clock,
  ArrowRight,
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
  Progress,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Alert,
} from "../../components/ui";

// 交互历史时间线
function InteractionTimeline() {
  const [timeline, setTimeline] = useState([
    {
      date: "2025-02-28",
      type: "meeting",
      title: "技术方案评审会议",
      participants: ["张三（技术总监）", "李四（采购经理）"],
      outcome: "方案基本认可，需调整 2 处细节",
      sentiment: "positive",
    },
    {
      date: "2025-02-25",
      type: "call",
      title: "电话跟进",
      participants: ["王五（销售）"],
      outcome: "确认预算范围 300-350 万",
      sentiment: "neutral",
    },
    {
      date: "2025-02-20",
      type: "email",
      title: "发送 FCT 方案 V1",
      outcome: "已发送，待确认",
      sentiment: "neutral",
    },
    {
      date: "2025-02-15",
      type: "meeting",
      title: "首次拜访",
      participants: ["张三（技术总监）", "赵六（生产经理）"],
      outcome: "了解需求，约定方案提交时间",
      sentiment: "positive",
    },
  ]);

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
    <div className="space-y-4">
      <div className="flex gap-4 mb-4">
        <Badge variant="outline">会议 {timeline.filter(t => t.type === "meeting").length}</Badge>
        <Badge variant="outline">电话 {timeline.filter(t => t.type === "call").length}</Badge>
        <Badge variant="outline">邮件 {timeline.filter(t => t.type === "email").length}</Badge>
        <Badge variant="outline">微信 {timeline.filter(t => t.type === "wechat").length}</Badge>
      </div>

      <div className="space-y-4">
        {timeline.map((item, idx) => (
          <Card key={idx}>
            <CardContent className="pt-4">
              <div className="flex items-start gap-4">
                <div className={`p-2 rounded-full ${getSentimentColor(item.sentiment)}`}>
                  {getTypeIcon(item.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <div className="font-medium">{item.title}</div>
                      <div className="text-sm text-slate-400">{item.date}</div>
                    </div>
                    <Badge variant={item.sentiment === "positive" ? "default" : "secondary"}>
                      {item.sentiment === "positive" ? "积极" : item.sentiment === "negative" ? "消极" : "中性"}
                    </Badge>
                  </div>
                  {item.participants && item.participants.length > 0 && (
                    <div className="text-sm text-slate-400 mb-2">
                      参与人：{item.participants.join(", ")}
                    </div>
                  )}
                  <div className="text-sm">
                    <span className="text-slate-400">结果：</span>
                    {item.outcome}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// 决策链分析
function DecisionChain() {
  const [decisionChain, setDecisionChain] = useState({
    contacts: [
      { name: "张三", title: "技术总监", role: "TB", role_name: "技术决策人", influence: "HIGH", attitude: "supportive", relationship_strength: 85 },
      { name: "李四", title: "采购经理", role: "PB", role_name: "采购决策人", influence: "MEDIUM", attitude: "neutral", relationship_strength: 60 },
      { name: "王五", title: "总经理", role: "EB", role_name: "最终决策人", influence: "HIGH", attitude: "unknown", relationship_strength: 40 },
      { name: "赵六", title: "生产经理", role: "UB", role_name: "最终用户", influence: "MEDIUM", attitude: "supportive", relationship_strength: 75 },
      { name: "钱七", title: "设备工程师", role: "Coach", role_name: "内线", influence: "LOW", attitude: "supportive", relationship_strength: 90 },
    ],
  });

  const getRoleBadge = (role) => {
    const colors = {
      EB: "bg-red-500",
      TB: "bg-blue-500",
      PB: "bg-green-500",
      UB: "bg-yellow-500",
      Coach: "bg-purple-500",
    };
    return colors[role] || "bg-slate-500";
  };

  const getAttitudeIcon = (attitude) => {
    switch (attitude) {
      case "supportive": return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "resistant": return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return <AlertCircle className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>姓名</TableHead>
            <TableHead>职位</TableHead>
            <TableHead>角色</TableHead>
            <TableHead>影响力</TableHead>
            <TableHead>态度</TableHead>
            <TableHead>关系强度</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {decisionChain.contacts.map((contact, idx) => (
            <TableRow key={idx}>
              <TableCell className="font-medium">{contact.name}</TableCell>
              <TableCell>{contact.title}</TableCell>
              <TableCell>
                <Badge className={getRoleBadge(contact.role)}>{contact.role_name}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant={contact.influence === "HIGH" ? "destructive" : "secondary"}>
                  {contact.influence === "HIGH" ? "高" : contact.influence === "MEDIUM" ? "中" : "低"}
                </Badge>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  {getAttitudeIcon(contact.attitude)}
                  <span className="text-sm">
                    {contact.attitude === "supportive" ? "支持" : contact.attitude === "resistant" ? "反对" : "未知"}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress value={contact.relationship_strength} className="w-20 h-2" />
                  <span className="text-sm w-8">{contact.relationship_strength}%</span>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <div className="text-sm">
          <strong>风险提示：</strong>EB（最终决策人）关系强度仅 40%，需加强接触
        </div>
      </Alert>
    </div>
  );
}

// 健康度评分
function HealthScore() {
  const [healthData, setHealthData] = useState({
    overall_score: 78,
    health_level: "GOOD",
    dimensions: [
      { name: "互动活跃度", score: 85, weight: 25, status: "GOOD" },
      { name: "关系深度", score: 70, weight: 25, status: "MEDIUM" },
      { name: "商机进展", score: 80, weight: 30, status: "GOOD" },
      { name: "客户满意度", score: 75, weight: 20, status: "GOOD" },
    ],
  });

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
      {/* 整体评分 */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="col-span-1">
          <CardContent className="pt-6 text-center">
            <div className="text-5xl font-bold text-green-500 mb-2">{healthData.overall_score}</div>
            <div className="text-slate-400">健康度评分</div>
            <Badge className="mt-2" variant="default">{healthData.health_level}</Badge>
          </CardContent>
        </Card>
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>各维度评分</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {healthData.dimensions.map((dim, idx) => (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm">{dim.name}</span>
                    <span className={`text-sm font-medium ${getStatusColor(dim.status)}`}>
                      {dim.score}分 ({dim.status === "GOOD" ? "良好" : dim.status === "MEDIUM" ? "中等" : "差"})
                    </span>
                  </div>
                  <Progress value={dim.score} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 建议行动 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            建议行动
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <Badge variant="destructive">高优先级</Badge>
              <div>
                <div className="font-medium">安排总经理级别拜访</div>
                <div className="text-sm text-slate-400">提升 EB 关系强度</div>
              </div>
              <Badge variant="outline" className="ml-auto">2 周内</Badge>
            </div>
            <div className="flex items-start gap-3">
              <Badge variant="secondary">中优先级</Badge>
              <div>
                <div className="font-medium">邀请技术总监参观案例项目</div>
                <div className="text-sm text-slate-400">巩固 TB 支持</div>
              </div>
              <Badge variant="outline" className="ml-auto">1 个月内</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 购买偏好
function BuyingPreferences() {
  const [preferences, setPreferences] = useState({
    product_preferences: {
      preferred_categories: [
        { category: "FCT", count: 3, percentage: 60 },
        { category: "EOL", count: 1, percentage: 20 },
        { category: "ICT", count: 1, percentage: 20 },
      ],
    },
    price_sensitivity: {
      level: "MEDIUM",
      score: 60,
      analysis: "关注价格但更重视价值，愿意为技术优势支付溢价",
    },
    decision_pattern: {
      avg_decision_cycle_days: 45,
      key_decision_factors: [
        { factor: "技术实力", weight: 35 },
        { factor: "行业案例", weight: 25 },
        { factor: "价格", weight: 20 },
        { factor: "交付周期", weight: 15 },
        { factor: "售后服务", weight: 5 },
      ],
    },
  });

  return (
    <div className="space-y-6">
      <div className="grid md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>产品类型偏好</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {preferences.product_preferences.preferred_categories.map((cat, idx) => (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm">{cat.category}</span>
                    <span className="text-sm text-slate-400">{cat.percentage}%</span>
                  </div>
                  <Progress value={cat.percentage} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>价格敏感度</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold mb-2">
              {preferences.price_sensitivity.level === "HIGH" ? "高" :
               preferences.price_sensitivity.level === "MEDIUM" ? "中" : "低"}
            </div>
            <div className="text-sm text-slate-400 mb-4">
              {preferences.price_sensitivity.analysis}
            </div>
            <Progress value={preferences.price_sensitivity.score} className="h-2" />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>关键决策因素</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {preferences.decision_pattern.key_decision_factors.map((factor, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm">{factor.factor}</span>
                  <span className="text-sm font-medium">{factor.weight}%</span>
                </div>
                <Progress value={factor.weight} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>推荐跟进策略</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            <li className="flex items-start gap-2">
              <ArrowRight className="w-4 h-4 text-green-500 mt-0.5" />
              <span className="text-sm">强调技术优势和锂电行业案例</span>
            </li>
            <li className="flex items-start gap-2">
              <ArrowRight className="w-4 h-4 text-green-500 mt-0.5" />
              <span className="text-sm">提供详细的技术方案和测试数据</span>
            </li>
            <li className="flex items-start gap-2">
              <ArrowRight className="w-4 h-4 text-green-500 mt-0.5" />
              <span className="text-sm">准备 TCO 分析支撑价格</span>
            </li>
            <li className="flex items-start gap-2">
              <ArrowRight className="w-4 h-4 text-green-500 mt-0.5" />
              <span className="text-sm">安排已交付客户参观</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

// 主页面
export default function Customer360() {
  const { customerId } = useParams();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="客户 360°画像"
          description="全面了解客户，提升销售成功率"
          icon={<Users className="w-6 h-6 text-cyan-500" />}
          actions={
            <div className="flex gap-2">
              <Button variant="outline">
                <Calendar className="w-4 h-4 mr-2" />
                预约拜访
              </Button>
              <Button>
                <Phone className="w-4 h-4 mr-2" />
                立即联系
              </Button>
            </div>
          }
        />

        <Tabs defaultValue="timeline" className="mt-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
            <TabsTrigger value="timeline">
              <Clock className="w-4 h-4 mr-2" />
              交互历史
            </TabsTrigger>
            <TabsTrigger value="decision">
              <Users className="w-4 h-4 mr-2" />
              决策链
            </TabsTrigger>
            <TabsTrigger value="health">
              <Heart className="w-4 h-4 mr-2" />
              健康度
            </TabsTrigger>
            <TabsTrigger value="preferences">
              <ShoppingCart className="w-4 h-4 mr-2" />
              购买偏好
            </TabsTrigger>
          </TabsList>

          <TabsContent value="timeline" className="mt-6">
            <InteractionTimeline />
          </TabsContent>

          <TabsContent value="decision" className="mt-6">
            <DecisionChain />
          </TabsContent>

          <TabsContent value="health" className="mt-6">
            <HealthScore />
          </TabsContent>

          <TabsContent value="preferences" className="mt-6">
            <BuyingPreferences />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
