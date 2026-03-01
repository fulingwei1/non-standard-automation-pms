/**
 * 绩效与激励页面
 * 
 * 功能：
 * 1. 实时业绩排行榜
 * 2. 提成计算
 * 3. PK 对战
 * 4. 成就系统
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Trophy,
  Medal,
  Target,
  TrendingUp,
  Award,
  Zap,
  DollarSign,
  Users,
  Crown,
  Star,
  Flame,
  Gift,
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

// 业绩排行榜
function Leaderboard() {
  const [leaderboard, setLeaderboard] = useState({
    individual_ranking: [
      { rank: 1, sales_name: "张三", department: "华南大区", revenue: 15800000, completion_rate: 158.0, deals_won: 12, trend: "up", rank_change: 0 },
      { rank: 2, sales_name: "李四", department: "华东大区", revenue: 12500000, completion_rate: 125.0, deals_won: 9, trend: "up", rank_change: 1 },
      { rank: 3, sales_name: "王五", department: "华北大区", revenue: 11200000, completion_rate: 112.0, deals_won: 8, trend: "down", rank_change: -1 },
      { rank: 4, sales_name: "赵六", department: "华南大区", revenue: 9800000, completion_rate: 98.0, deals_won: 7, trend: "stable", rank_change: 0 },
      { rank: 5, sales_name: "钱七", department: "华东大区", revenue: 8500000, completion_rate: 85.0, deals_won: 6, trend: "up", rank_change: 2 },
    ],
    team_ranking: [
      { rank: 1, team_name: "华南大区", revenue: 45800000, completion_rate: 114.5 },
      { rank: 2, team_name: "华东大区", revenue: 42500000, completion_rate: 106.2 },
      { rank: 3, team_name: "华北大区", revenue: 38200000, completion_rate: 95.5 },
    ],
  });

  const getTrendIcon = (trend) => {
    if (trend === "up") return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (trend === "down") return <TrendingUp className="w-4 h-4 text-red-500 rotate-180" />;
    return <span className="text-slate-400">-</span>;
  };

  const getRankBadge = (rank) => {
    if (rank === 1) return <Crown className="w-5 h-5 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-5 h-5 text-slate-400" />;
    if (rank === 3) return <Medal className="w-5 h-5 text-orange-500" />;
    return <span className="w-5 h-5 flex items-center justify-center font-bold">{rank}</span>;
  };

  return (
    <div className="space-y-6">
      {/* 个人排行榜 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-500" />
            个人业绩排行榜
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-16">排名</TableHead>
                <TableHead>姓名</TableHead>
                <TableHead>部门</TableHead>
                <TableHead className="text-right">业绩</TableHead>
                <TableHead className="text-right">完成率</TableHead>
                <TableHead className="text-right">签单数</TableHead>
                <TableHead>趋势</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {leaderboard.individual_ranking.map((item) => (
                <TableRow key={item.rank} className={item.rank <= 3 ? "bg-yellow-500/5" : ""}>
                  <TableCell>
                    <div className="flex items-center justify-center">
                      {getRankBadge(item.rank)}
                    </div>
                  </TableCell>
                  <TableCell className="font-medium">{item.sales_name}</TableCell>
                  <TableCell>{item.department}</TableCell>
                  <TableCell className="text-right">
                    ¥{(item.revenue / 10000).toFixed(0)}万
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant={item.completion_rate >= 100 ? "default" : "secondary"}>
                      {item.completion_rate}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">{item.deals_won}</TableCell>
                  <TableCell>{getTrendIcon(item.trend)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 团队排行榜 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5 text-blue-500" />
            团队业绩排行榜
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            {leaderboard.team_ranking.map((team) => (
              <Card key={team.rank} className={team.rank === 1 ? "border-yellow-500" : ""}>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">No.{team.rank} {team.team_name}</span>
                    {team.rank === 1 && <Crown className="w-4 h-4 text-yellow-500" />}
                  </div>
                  <div className="text-2xl font-bold mb-2">
                    ¥{(team.revenue / 10000).toFixed(0)}万
                  </div>
                  <Progress value={team.completion_rate} className="h-2" />
                  <div className="text-sm text-slate-400 mt-2">完成率 {team.completion_rate}%</div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 提成计算
function CommissionCalculator() {
  const [commission, setCommission] = useState({
    sales_name: "张三",
    month: "2025-02",
    base_data: {
      monthly_target: 10000000,
      monthly_revenue: 15800000,
      completion_rate: 158.0,
    },
    summary: {
      total_revenue: 15800000,
      final_commission: 456960,
      net_commission: 388416,
    },
    deals: [
      { deal_id: 1001, customer_name: "宁德时代", product_type: "FCT", revenue: 3200000, commission_amount: 103680 },
      { deal_id: 1002, customer_name: "比亚迪", product_type: "EOL", revenue: 2800000, commission_amount: 92400 },
      { deal_id: 1003, customer_name: "中创新航", product_type: "FCT", revenue: 3500000, commission_amount: 75600 },
    ],
  });

  return (
    <div className="space-y-6">
      {/* 总览 */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">本月业绩</div>
            <div className="text-2xl font-bold">¥{(commission.summary.total_revenue / 10000).toFixed(0)}万</div>
            <div className="text-sm text-green-500 mt-1">完成率 {commission.base_data.completion_rate}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">应发提成</div>
            <div className="text-2xl font-bold text-green-500">¥{(commission.summary.final_commission / 10000).toFixed(1)}万</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400 mb-1">实发提成</div>
            <div className="text-2xl font-bold text-blue-500">¥{(commission.summary.net_commission / 10000).toFixed(1)}万</div>
            <div className="text-xs text-slate-400 mt-1">税后估算</div>
          </CardContent>
        </Card>
      </div>

      {/* 提成明细 */}
      <Card>
        <CardHeader>
          <CardTitle>提成明细</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>客户</TableHead>
                <TableHead>产品类型</TableHead>
                <TableHead className="text-right">合同金额</TableHead>
                <TableHead className="text-right">提成金额</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {commission.deals.map((deal) => (
                <TableRow key={deal.deal_id}>
                  <TableCell>{deal.customer_name}</TableCell>
                  <TableCell><Badge variant="outline">{deal.product_type}</Badge></TableCell>
                  <TableCell className="text-right">¥{(deal.revenue / 10000).toFixed(0)}万</TableCell>
                  <TableCell className="text-right text-green-500">¥{(deal.commission_amount / 10000).toFixed(1)}万</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 提成规则 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            提成规则
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-slate-800 rounded">
              <div className="text-sm text-slate-400">0-80%</div>
              <div className="text-2xl font-bold">1%</div>
              <div className="text-xs text-slate-400">基础档</div>
            </div>
            <div className="text-center p-4 bg-blue-500/10 rounded border border-blue-500">
              <div className="text-sm text-blue-400">80-100%</div>
              <div className="text-2xl font-bold text-blue-500">1.5%</div>
              <div className="text-xs text-slate-400">达标档</div>
            </div>
            <div className="text-center p-4 bg-green-500/10 rounded border border-green-500">
              <div className="text-sm text-green-400">100-120%</div>
              <div className="text-2xl font-bold text-green-500">2%</div>
              <div className="text-xs text-slate-400">超额档</div>
            </div>
            <div className="text-center p-4 bg-yellow-500/10 rounded border border-yellow-500">
              <div className="text-sm text-yellow-400">120%+</div>
              <div className="text-2xl font-bold text-yellow-500">3%</div>
              <div className="text-xs text-slate-400">卓越档</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// PK 对战
function PKBattles() {
  const [battles, setBattles] = useState({
    active_battles: [
      {
        battle_id: 1,
        type: "official",
        title: "Q1 业绩 PK 赛",
        period: "2025-Q1",
        end_date: "2025-03-31",
        participants: [
          { sales_name: "张三", current_revenue: 15800000, rank: 1 },
          { sales_name: "李四", current_revenue: 12500000, rank: 2 },
        ],
        prize: { first: { amount: 20000 }, second: { amount: 10000 } },
        days_remaining: 28,
      },
      {
        battle_id: 2,
        type: "free",
        title: "张三 vs 王五 单挑赛",
        period: "2025-02",
        end_date: "2025-02-29",
        participants: [
          { sales_name: "张三", current_revenue: 15800000, rank: 1 },
          { sales_name: "王五", current_revenue: 11200000, rank: 2 },
        ],
        bet: { amount: 2000 },
        days_remaining: 3,
      },
    ],
  });

  return (
    <div className="space-y-4">
      {battles.active_battles.map((battle) => (
        <Card key={battle.battle_id} className={battle.type === "official" ? "border-yellow-500" : ""}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  {battle.type === "official" ? <Trophy className="w-5 h-5 text-yellow-500" /> : <Zap className="w-5 h-5" />}
                  {battle.title}
                </CardTitle>
                <CardDescription>
                  截止时间：{battle.end_date} · 剩余 {battle.days_remaining} 天
                </CardDescription>
              </div>
              <Badge variant={battle.type === "official" ? "default" : "secondary"}>
                {battle.type === "official" ? "官方 PK" : "自由 PK"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                {battle.participants.map((p, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded ${p.rank === 1 ? "bg-yellow-500/10 border border-yellow-500" : "bg-slate-800"}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{p.sales_name}</span>
                      <Badge variant={p.rank === 1 ? "default" : "secondary"}>No.{p.rank}</Badge>
                    </div>
                    <div className="text-2xl font-bold">¥{(p.current_revenue / 10000).toFixed(0)}万</div>
                  </div>
                ))}
              </div>
              {battle.prize && (
                <div className="flex items-center gap-4 text-sm">
                  <Gift className="w-4 h-4" />
                  <span>冠军：¥{battle.prize.first.amount / 10000}万</span>
                  {battle.prize.second && <span>· 亚军：¥{battle.prize.second.amount / 10000}万</span>}
                </div>
              )}
              {battle.bet && (
                <Alert>
                  <div className="text-sm">赌注：¥{battle.bet.amount}</div>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>
      ))}

      <Button className="w-full">
        <Zap className="w-4 h-4 mr-2" />
        发起 PK 挑战
      </Button>
    </div>
  );
}

// 成就系统
function Achievements() {
  const [achievements, setAchievements] = useState({
    total_achievements: 15,
    total_points: 2850,
    level: 8,
    level_name: "销售精英",
    badges: [
      { name: "签单王", icon: "🏆", rarity: "gold", earned_date: "2025-01-15" },
      { name: "破纪录者", icon: "💎", rarity: "diamond", earned_date: "2025-02-10" },
      { name: "锂电专家", icon: "⚡", rarity: "silver", earned_date: "2025-01-20" },
      { name: "新人王", icon: "🌟", rarity: "gold", earned_date: "2024-06-30" },
      { name: "常胜将军", icon: "👑", rarity: "platinum", earned_date: "2025-02-28" },
    ],
    progress: [
      { achievement_name: "百万俱乐部", current: 85000000, target: 100000000, progress: 85.0 },
      { achievement_name: "百单达人", current: 78, target: 100, progress: 78.0 },
    ],
  });

  const getRarityColor = (rarity) => {
    const colors = {
      platinum: "from-slate-400 to-slate-600",
      diamond: "from-blue-400 to-blue-600",
      gold: "from-yellow-400 to-yellow-600",
      silver: "from-slate-300 to-slate-500",
    };
    return colors[rarity] || colors.silver;
  };

  return (
    <div className="space-y-6">
      {/* 等级信息 */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-2xl font-bold">Lv.{achievements.level} {achievements.level_name}</div>
              <div className="text-sm text-slate-400">总积分：{achievements.total_points}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">成就总数</div>
              <div className="text-2xl font-bold">{achievements.total_achievements}</div>
            </div>
          </div>
          <Progress value={(achievements.total_points / 3500) * 100} className="h-3" />
          <div className="text-sm text-slate-400 mt-2">距离下一级还需 {3500 - achievements.total_points} 积分</div>
        </CardContent>
      </Card>

      {/* 徽章展示 */}
      <Card>
        <CardHeader>
          <CardTitle>我的徽章</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
            {achievements.badges.map((badge, idx) => (
              <div key={idx} className="text-center">
                <div className={`w-16 h-16 mx-auto rounded-full bg-gradient-to-br ${getRarityColor(badge.rarity)} flex items-center justify-center text-3xl mb-2`}>
                  {badge.icon}
                </div>
                <div className="text-sm font-medium">{badge.name}</div>
                <div className="text-xs text-slate-400">{badge.earned_date}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 成就进度 */}
      <Card>
        <CardHeader>
          <CardTitle>进行中成就</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {achievements.progress.map((item, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm">{item.achievement_name}</span>
                  <span className="text-sm text-slate-400">
                    {item.current >= 1000000 ? `¥${(item.current / 1000000).toFixed(0)}万` : item.current} / {item.target >= 1000000 ? `¥${(item.target / 1000000).toFixed(0)}万` : item.target}
                  </span>
                </div>
                <Progress value={item.progress} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 主页面
export default function PerformanceIncentive() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="绩效与激励"
          description="实时排行榜、提成计算、PK 对战、成就系统"
          icon={<Award className="w-6 h-6 text-yellow-500" />}
        />

        <Tabs defaultValue="leaderboard" className="mt-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
            <TabsTrigger value="leaderboard">
              <Trophy className="w-4 h-4 mr-2" />
              排行榜
            </TabsTrigger>
            <TabsTrigger value="commission">
              <DollarSign className="w-4 h-4 mr-2" />
              提成计算
            </TabsTrigger>
            <TabsTrigger value="pk">
              <Zap className="w-4 h-4 mr-2" />
              PK 对战
            </TabsTrigger>
            <TabsTrigger value="achievements">
              <Award className="w-4 h-4 mr-2" />
              成就系统
            </TabsTrigger>
          </TabsList>

          <TabsContent value="leaderboard" className="mt-6">
            <Leaderboard />
          </TabsContent>

          <TabsContent value="commission" className="mt-6">
            <CommissionCalculator />
          </TabsContent>

          <TabsContent value="pk" className="mt-6">
            <PKBattles />
          </TabsContent>

          <TabsContent value="achievements" className="mt-6">
            <Achievements />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
