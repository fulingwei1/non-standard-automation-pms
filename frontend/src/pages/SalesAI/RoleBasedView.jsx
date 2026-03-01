/**
 * 多角色视图测试页面
 * 
 * 测试不同角色（销售/经理/领导）的数据展示是否清晰直观
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  User,
  Users,
  Briefcase,
  Eye,
  Target,
  TrendingUp,
  DollarSign,
  CheckCircle,
  AlertCircle,
  BarChart3,
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
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui";

// 销售角色视图
function SalesRepView() {
  const [myData, _setMyData] = useState({
    name: "张三",
    team: "华南大区",
    quota: 50000000,
    achieved: 32000000,
    achievement_rate: 64,
    opportunities: [
      {
        name: "宁德时代 FCT",
        amount: 3500000,
        stage: "商务谈判",
        win_rate: 75,
        expected_close: "2026-03-31",
        priority: "high",
        next_action: "准备 TCO 分析，3 天内",
      },
      {
        name: "中创新航 ICT",
        amount: 2800000,
        stage: "方案评估",
        win_rate: 58,
        expected_close: "2026-04-15",
        priority: "medium",
        next_action: "安排技术交流，1 周内",
      },
      {
        name: "欣旺达 FCT",
        amount: 3200000,
        stage: "需求分析",
        win_rate: 35,
        expected_close: "2026-05-15",
        priority: "low",
        next_action: "需求调研，2 周内",
      },
    ],
    tasks: [
      { task: "宁德时代 TCO 分析", deadline: "3 天内", priority: "high" },
      { task: "中创新航技术交流", deadline: "1 周内", priority: "medium" },
      { task: "欣旺达需求调研", deadline: "2 周内", priority: "low" },
      { task: "比亚迪合同跟进", deadline: "本周", priority: "high" },
    ],
  });

  return (
    <div className="space-y-6">
      <Alert className="border-blue-500 bg-blue-500/10">
        <Eye className="h-4 w-4" />
        <div>
          <strong>销售视角</strong>
          <div className="text-sm text-slate-400 mt-1">
            关注：我的业绩、我的商机、我的待办
          </div>
        </div>
      </Alert>

      {/* 业绩概览 */}
      <div className="grid md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">年度指标</div>
            <div className="text-2xl font-bold">¥{(myData.quota / 1000000).toFixed(0)}M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">已完成</div>
            <div className="text-2xl font-bold text-green-500">¥{(myData.achieved / 1000000).toFixed(0)}M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">完成率</div>
            <div className="text-2xl font-bold">{myData.achievement_rate}%</div>
            <Progress value={myData.achievement_rate} className="h-2 mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* 我的商机 */}
      <Card>
        <CardHeader>
          <CardTitle>我的重点商机</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>商机</TableHead>
                <TableHead>金额</TableHead>
                <TableHead>阶段</TableHead>
                <TableHead>赢单率</TableHead>
                <TableHead>预计成交</TableHead>
                <TableHead>优先级</TableHead>
                <TableHead>下一步</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {myData.opportunities.map((opp) => (
                <TableRow key={opp.name}>
                  <TableCell className="font-medium">{opp.name}</TableCell>
                  <TableCell>¥{(opp.amount / 1000000).toFixed(1)}M</TableCell>
                  <TableCell><Badge variant="outline">{opp.stage}</Badge></TableCell>
                  <TableCell>
                    <Badge variant={opp.win_rate >= 70 ? "default" : opp.win_rate >= 50 ? "secondary" : "destructive"}>
                      {opp.win_rate}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-slate-400">{opp.expected_close}</TableCell>
                  <TableCell>
                    <Badge variant={opp.priority === "high" ? "default" : opp.priority === "medium" ? "secondary" : "outline"}>
                      {opp.priority === "high" ? "高" : opp.priority === "medium" ? "中" : "低"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{opp.next_action}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 我的待办 */}
      <Card>
        <CardHeader>
          <CardTitle>我的待办事项</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {myData.tasks.map((task, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 border rounded">
                <div className="flex items-center gap-3">
                  <CheckCircle className={`w-5 h-5 ${task.priority === "high" ? "text-red-500" : task.priority === "medium" ? "text-orange-500" : "text-slate-400"}`} />
                  <span>{task.task}</span>
                </div>
                <Badge variant="outline" className="text-xs">{task.deadline}</Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 经理角色视图
function ManagerView() {
  const [teamData, _setTeamData] = useState({
    team_name: "华南大区",
    members: 5,
    quota: 200000000,
    achieved: 128000000,
    achievement_rate: 64,
    team_members: [
      { name: "张三", quota: 50000000, achieved: 32000000, rate: 64, opportunities: 3, top_opportunity: "宁德时代 FCT" },
      { name: "李四", quota: 45000000, achieved: 30000000, rate: 67, opportunities: 2, top_opportunity: "比亚迪 EOL" },
      { name: "王五", quota: 40000000, achieved: 28000000, rate: 70, opportunities: 4, top_opportunity: "亿纬锂能 烧录" },
      { name: "赵六", quota: 35000000, achieved: 20000000, rate: 57, opportunities: 3, top_opportunity: "欣旺达 FCT" },
      { name: "钱七", quota: 30000000, achieved: 18000000, rate: 60, opportunities: 2, top_opportunity: "国轩高科 ICT" },
    ],
    pipeline_health: {
      total: 85000000,
      high_confidence: 35000000,
      medium_confidence: 30000000,
      low_confidence: 20000000,
    },
    alerts: [
      { type: "warning", message: "赵六 连续 2 周未拜访重点客户", priority: "high" },
      { type: "info", message: "宁德时代项目需安排高层拜访", priority: "medium" },
      { type: "success", message: "李四 提前完成 Q1 指标", priority: "low" },
    ],
  });

  return (
    <div className="space-y-6">
      <Alert className="border-purple-500 bg-purple-500/10">
        <Users className="h-4 w-4" />
        <div>
          <strong>经理视角</strong>
          <div className="text-sm text-slate-400 mt-1">
            关注：团队业绩、成员表现、pipeline 健康度、风险预警
          </div>
        </div>
      </Alert>

      {/* 团队业绩 */}
      <div className="grid md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">团队指标</div>
            <div className="text-2xl font-bold">¥{(teamData.quota / 1000000).toFixed(0)}M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">已完成</div>
            <div className="text-2xl font-bold text-green-500">¥{(teamData.achieved / 1000000).toFixed(0)}M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">完成率</div>
            <div className="text-2xl font-bold">{teamData.achievement_rate}%</div>
            <Progress value={teamData.achievement_rate} className="h-2 mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">团队成员</div>
            <div className="text-2xl font-bold">{teamData.members}人</div>
          </CardContent>
        </Card>
      </div>

      {/* 团队成员表现 */}
      <Card>
        <CardHeader>
          <CardTitle>团队成员表现</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>姓名</TableHead>
                <TableHead>指标</TableHead>
                <TableHead>已完成</TableHead>
                <TableHead>完成率</TableHead>
                <TableHead>商机数</TableHead>
                <TableHead>重点商机</TableHead>
                <TableHead>状态</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {teamData.team_members.map((member) => (
                <TableRow key={member.name}>
                  <TableCell className="font-medium">{member.name}</TableCell>
                  <TableCell>¥{(member.quota / 1000000).toFixed(0)}M</TableCell>
                  <TableCell>¥{(member.achieved / 1000000).toFixed(0)}M</TableCell>
                  <TableCell>
                    <Badge variant={member.rate >= 70 ? "default" : member.rate >= 60 ? "secondary" : "destructive"}>
                      {member.rate}%
                    </Badge>
                  </TableCell>
                  <TableCell>{member.opportunities}个</TableCell>
                  <TableCell className="text-sm text-slate-400">{member.top_opportunity}</TableCell>
                  <TableCell>
                    {member.rate >= 70 && <CheckCircle className="w-4 h-4 text-green-500" />}
                    {member.rate >= 60 && member.rate < 70 && <AlertCircle className="w-4 h-4 text-orange-500" />}
                    {member.rate < 60 && <AlertCircle className="w-4 h-4 text-red-500" />}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Pipeline 健康度 */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline 健康度</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">高置信度（≥70%）</div>
                <div className="text-xl font-bold text-green-500">¥{(teamData.pipeline_health.high_confidence / 10000).toFixed(0)}万</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">中置信度（40-69%）</div>
                <div className="text-xl font-bold text-blue-500">¥{(teamData.pipeline_health.medium_confidence / 10000).toFixed(0)}万</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">低置信度（&lt;40%）</div>
                <div className="text-xl font-bold text-orange-500">¥{(teamData.pipeline_health.low_confidence / 10000).toFixed(0)}万</div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* 风险预警 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            风险预警
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {teamData.alerts.map((alert, idx) => (
              <div key={idx} className={`p-3 rounded ${alert.type === "warning" ? "bg-orange-500/10" : alert.type === "success" ? "bg-green-500/10" : "bg-blue-500/10"}`}>
                <div className="flex items-center gap-2">
                  <AlertCircle className={`w-4 h-4 ${alert.type === "warning" ? "text-orange-500" : alert.type === "success" ? "text-green-500" : "text-blue-500"}`} />
                  <span>{alert.message}</span>
                  <Badge variant="outline" className="ml-auto text-xs">{alert.priority === "high" ? "高" : alert.priority === "medium" ? "中" : "低"}</Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 领导角色视图
function ExecutiveView() {
  const [execData, _setExecData] = useState({
    company_quota: 800000000,
    company_achieved: 512000000,
    achievement_rate: 64,
    yoy_growth: 28,
    teams: [
      { name: "华南大区", quota: 300000000, achieved: 198000000, rate: 66, yoy: 32 },
      { name: "华东大区", quota: 280000000, achieved: 175000000, rate: 62.5, yoy: 25 },
      { name: "华北大区", quota: 220000000, achieved: 139000000, rate: 63.2, yoy: 22 },
    ],
    pipeline_total: 450000000,
    weighted_pipeline: 285000000,
    top_risks: [
      { risk: "华东大区完成率偏低（62.5%）", impact: "高", action: "加强华东区支持" },
      { risk: "竞品 D 在电子行业攻势猛", impact: "中", action: "制定专项竞争策略" },
      { risk: "Q2 交付压力大", impact: "中", action: "提前协调产能" },
    ],
    strategic_opportunities: [
      { name: "宁德时代 战略合作", value: 50000000, win_rate: 75, owner: "张三" },
      { name: "比亚迪 二期项目", value: 40000000, win_rate: 82, owner: "李四" },
      { name: "中创新航 框架合同", value: 30000000, win_rate: 58, owner: "张三" },
    ],
  });

  return (
    <div className="space-y-6">
      <Alert className="border-green-500 bg-green-500/10">
        <Briefcase className="h-4 w-4" />
        <div>
          <strong>领导视角</strong>
          <div className="text-sm text-slate-400 mt-1">
            关注：公司整体业绩、团队对比、战略机会、重大风险
          </div>
        </div>
      </Alert>

      {/* 公司整体业绩 */}
      <div className="grid md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">公司指标</div>
            <div className="text-2xl font-bold">¥{(execData.company_quota / 1000000).toFixed(0)}M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">已完成</div>
            <div className="text-2xl font-bold text-green-500">¥{(execData.company_achieved / 1000000).toFixed(0)}M</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">完成率</div>
            <div className="text-2xl font-bold">{execData.achievement_rate}%</div>
            <Progress value={execData.achievement_rate} className="h-2 mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-400">同比增长</div>
            <div className="text-2xl font-bold text-green-500">+{execData.yoy_growth}%</div>
          </CardContent>
        </Card>
      </div>

      {/* 团队对比 */}
      <Card>
        <CardHeader>
          <CardTitle>大区业绩对比</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>大区</TableHead>
                <TableHead>指标</TableHead>
                <TableHead>已完成</TableHead>
                <TableHead>完成率</TableHead>
                <TableHead>同比增长</TableHead>
                <TableHead>状态</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {execData.teams.map((team) => (
                <TableRow key={team.name}>
                  <TableCell className="font-medium">{team.name}</TableCell>
                  <TableCell>¥{(team.quota / 1000000).toFixed(0)}M</TableCell>
                  <TableCell>¥{(team.achieved / 1000000).toFixed(0)}M</TableCell>
                  <TableCell>
                    <Badge variant={team.rate >= 70 ? "default" : team.rate >= 60 ? "secondary" : "destructive"}>
                      {team.rate}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-green-500">+{team.yoy}%</TableCell>
                  <TableCell>
                    {team.rate >= 70 && <CheckCircle className="w-4 h-4 text-green-500" />}
                    {team.rate >= 60 && team.rate < 70 && <AlertCircle className="w-4 h-4 text-orange-500" />}
                    {team.rate < 60 && <AlertCircle className="w-4 h-4 text-red-500" />}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 战略机会 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            战略级商机
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>商机</TableHead>
                <TableHead>金额</TableHead>
                <TableHead>赢单率</TableHead>
                <TableHead>负责人</TableHead>
                <TableHead>预期收入</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {execData.strategic_opportunities.map((opp) => (
                <TableRow key={opp.name}>
                  <TableCell className="font-medium">{opp.name}</TableCell>
                  <TableCell>¥{(opp.value / 1000000).toFixed(0)}M</TableCell>
                  <TableCell>
                    <Badge variant={opp.win_rate >= 70 ? "default" : "secondary"}>
                      {opp.win_rate}%
                    </Badge>
                  </TableCell>
                  <TableCell>{opp.owner}</TableCell>
                  <TableCell className="font-medium">¥{(opp.value * opp.win_rate / 100 / 10000).toFixed(0)}万</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 重大风险 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            重大风险
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {execData.top_risks.map((risk, idx) => (
              <div key={idx} className="p-3 border border-red-500/30 rounded">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium">{risk.risk}</div>
                    <div className="text-sm text-slate-400 mt-1">应对：{risk.action}</div>
                  </div>
                  <Badge variant={risk.impact === "高" ? "destructive" : "secondary"}>
                    影响：{risk.impact}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// 主页面
export default function RoleBasedView() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="多角色视图测试"
          description="验证不同角色的数据展示是否清晰直观"
          icon={<Eye className="w-6 h-6 text-cyan-500" />}
        />

        <Tabs defaultValue="sales" className="mt-6">
          <TabsList className="grid w-full grid-cols-3 lg:w-[600px]">
            <TabsTrigger value="sales">
              <User className="w-4 h-4 mr-2" />
              销售视角
            </TabsTrigger>
            <TabsTrigger value="manager">
              <Users className="w-4 h-4 mr-2" />
              经理视角
            </TabsTrigger>
            <TabsTrigger value="executive">
              <Briefcase className="w-4 h-4 mr-2" />
              领导视角
            </TabsTrigger>
          </TabsList>

          <TabsContent value="sales" className="mt-6">
            <SalesRepView />
          </TabsContent>

          <TabsContent value="manager" className="mt-6">
            <ManagerView />
          </TabsContent>

          <TabsContent value="executive" className="mt-6">
            <ExecutiveView />
          </TabsContent>
        </Tabs>

        {/* 测试反馈 */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>测试检查清单</CardTitle>
            <CardDescription>验证各角色视图的数据输入和展示是否直观</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span>销售能否快速看到自己的业绩和待办？</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span>经理能否清晰了解团队成员表现？</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span>领导能否一眼看到公司整体业绩和战略机会？</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span>数据展示是否简洁，无冗余信息？</span>
              </div>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span>风险预警是否醒目，便于快速响应？</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
