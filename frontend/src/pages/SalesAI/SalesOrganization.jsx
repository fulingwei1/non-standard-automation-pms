/**
 * 销售组织架构页面
 * 
 * 4 层层级：销售总经理 → 销售总监 → 销售经理 → 销售
 * 支持层级式数据汇总和钻取
 */

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Users,
  User,
  Briefcase,
  TrendingUp,
  DollarSign,
  Target,
  ChevronRight,
  ChevronDown,
  Building2,
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

// 组织树节点组件
function OrgNode({ node, level, onSelect, selectedId }) {
  const [expanded, setExpanded] = useState(level < 2); // 默认展开前 2 层
  
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selectedId === node.id;
  
  const getLevelColor = (_level) => {
    const colors = {
      GM: "border-purple-500 bg-purple-500/10",
      Director: "border-blue-500 bg-blue-500/10",
      Manager: "border-green-500 bg-green-500/10",
      Sales: "border-slate-500 bg-slate-500/10",
    };
    return colors[node.level] || colors.Sales;
  };
  
  const getRateColor = (rate) => {
    if (rate >= 70) return "text-green-500";
    if (rate >= 60) return "text-blue-500";
    if (rate >= 50) return "text-orange-500";
    return "text-red-500";
  };

  return (
    <div className="ml-4">
      <div
        className={`flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-all ${getLevelColor(node.level)} ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
        onClick={() => onSelect(node)}
      >
        {hasChildren ? (
          <button onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); }}>
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
        ) : (
          <div className="w-4" />
        )}
        
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium">{node.name}</span>
            <Badge variant="outline" className="text-xs">{node.level}</Badge>
          </div>
          {node.person && (
            <div className="text-xs text-slate-400">{node.person.name} · {node.person.title}</div>
          )}
        </div>
        
        {node.metrics && (
          <div className="text-right">
            <div className={`text-sm font-bold ${getRateColor(node.metrics.achievement_rate)}`}>
              {node.metrics.achievement_rate}%
            </div>
            <div className="text-xs text-slate-400">
              ¥{(node.metrics.achieved_ytd / 1000000).toFixed(1)}M / ¥{(node.metrics.quota_annual / 1000000).toFixed(0)}M
            </div>
          </div>
        )}
      </div>
      
      {expanded && hasChildren && (
        <div className="mt-2 border-l-2 border-slate-700 pl-2">
          {node.children.map((child) => (
            <OrgNode
              key={child.id}
              node={child}
              level={level + 1}
              onSelect={onSelect}
              selectedId={selectedId}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// 组织树视图
function OrganizationTree() {
  const [selectedNode, setSelectedNode] = useState(null);
  
  const orgTree = {
    id: 1,
    name: "销售总部",
    level: "GM",
    person: { id: 1, name: "陈总", title: "销售总经理" },
    metrics: { quota_annual: 800000000, achieved_ytd: 512000000, achievement_rate: 64.0, team_size: 28 },
    children: [
      {
        id: 2,
        name: "深圳分公司",
        level: "Director",
        person: { id: 2, name: "张总监", title: "销售总监" },
        metrics: { quota_annual: 300000000, achieved_ytd: 198000000, achievement_rate: 66.0, team_size: 10 },
        children: [
          {
            id: 5,
            name: "华南一区",
            level: "Manager",
            person: { id: 5, name: "张三", title: "销售经理" },
            metrics: { quota_annual: 100000000, achieved_ytd: 68000000, achievement_rate: 68.0, team_size: 4 },
            children: [
              { id: 11, name: "张三", level: "Sales", role: "销售工程师", metrics: { quota: 50000000, achieved: 32000000, rate: 64.0 } },
              { id: 12, name: "李小妹", level: "Sales", role: "销售工程师", metrics: { quota: 30000000, achieved: 22000000, rate: 73.3 } },
              { id: 13, name: "王小助", level: "Sales", role: "销售助理", metrics: { quota: 20000000, achieved: 14000000, rate: 70.0 } },
            ],
          },
          {
            id: 6,
            name: "华南二区",
            level: "Manager",
            person: { id: 6, name: "李四", title: "销售经理" },
            metrics: { quota_annual: 100000000, achieved_ytd: 65000000, achievement_rate: 65.0, team_size: 3 },
            children: [
              { id: 14, name: "赵六", level: "Sales", role: "销售工程师", metrics: { quota: 35000000, achieved: 21700000, rate: 62.0 } },
              { id: 15, name: "钱七", level: "Sales", role: "销售工程师", metrics: { quota: 30000000, achieved: 18000000, rate: 60.0 } },
              { id: 16, name: "孙八", level: "Sales", role: "销售助理", metrics: { quota: 20000000, achieved: 12000000, rate: 60.0 } },
            ],
          },
          {
            id: 7,
            name: "华南三区",
            level: "Manager",
            person: { id: 7, name: "王五", title: "销售经理" },
            metrics: { quota_annual: 100000000, achieved_ytd: 65000000, achievement_rate: 65.0, team_size: 3 },
            children: [
              { id: 17, name: "周九", level: "Sales", metrics: { rate: 68.0 } },
              { id: 18, name: "吴十", level: "Sales", metrics: { rate: 63.0 } },
              { id: 19, name: "郑十一", level: "Sales", metrics: { rate: 64.0 } },
            ],
          },
        ],
      },
      {
        id: 3,
        name: "苏州分公司",
        level: "Director",
        person: { id: 3, name: "李总监", title: "销售总监" },
        metrics: { quota_annual: 280000000, achieved_ytd: 175000000, achievement_rate: 62.5, team_size: 10 },
        children: [
          {
            id: 8,
            name: "华东一区",
            level: "Manager",
            person: { id: 8, name: "赵经理", title: "销售经理" },
            metrics: { quota_annual: 100000000, achieved_ytd: 62000000, achievement_rate: 62.0, team_size: 4 },
            children: [
              { id: 20, name: "队员 A", level: "Sales", metrics: { rate: 65.0 } },
              { id: 21, name: "队员 B", level: "Sales", metrics: { rate: 61.0 } },
              { id: 22, name: "队员 C", level: "Sales", metrics: { rate: 60.0 } },
              { id: 23, name: "队员 D", level: "Sales", metrics: { rate: 62.0 } },
            ],
          },
          {
            id: 9,
            name: "华东二区",
            level: "Manager",
            person: { id: 9, name: "钱经理", title: "销售经理" },
            metrics: { quota_annual: 80000000, achieved_ytd: 48000000, achievement_rate: 60.0, team_size: 3 },
            children: [
              { id: 24, name: "队员 E", level: "Sales", metrics: { rate: 62.0 } },
              { id: 25, name: "队员 F", level: "Sales", metrics: { rate: 59.0 } },
              { id: 26, name: "队员 G", level: "Sales", metrics: { rate: 59.0 } },
            ],
          },
        ],
      },
      {
        id: 4,
        name: "合肥分公司",
        level: "Director",
        person: { id: 4, name: "王总监", title: "销售总监" },
        metrics: { quota_annual: 220000000, achieved_ytd: 139000000, achievement_rate: 63.2, team_size: 8 },
        children: [
          {
            id: 10,
            name: "华北一区",
            level: "Manager",
            person: { id: 10, name: "孙经理", title: "销售经理" },
            metrics: { quota_annual: 80000000, achieved_ytd: 47000000, achievement_rate: 58.8, team_size: 3 },
            children: [
              { id: 27, name: "队员 H", level: "Sales", metrics: { rate: 60.0 } },
              { id: 28, name: "队员 I", level: "Sales", metrics: { rate: 58.0 } },
              { id: 29, name: "队员 J", level: "Sales", metrics: { rate: 58.5 } },
            ],
          },
        ],
      },
    ],
  };

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      {/* 组织树 */}
      <Card>
        <CardHeader>
          <CardTitle>销售组织架构</CardTitle>
          <CardDescription>点击节点查看详情</CardDescription>
        </CardHeader>
        <CardContent>
          <OrgNode node={orgTree} level={0} onSelect={setSelectedNode} selectedId={selectedNode?.id} />
        </CardContent>
      </Card>

      {/* 选中节点详情 */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedNode ? (
              <div className="flex items-center gap-2">
                {selectedNode.level === "GM" && <Briefcase className="w-5 h-5 text-purple-500" />}
                {selectedNode.level === "Director" && <Building2 className="w-5 h-5 text-blue-500" />}
                {selectedNode.level === "Manager" && <Users className="w-5 h-5 text-green-500" />}
                {selectedNode.level === "Sales" && <User className="w-5 h-5 text-slate-500" />}
                {selectedNode.name}
              </div>
            ) : (
              "选择节点查看详情"
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {selectedNode ? (
            <div className="space-y-4">
              {selectedNode.person && (
                <div>
                  <div className="text-sm text-slate-400">负责人</div>
                  <div className="font-medium">{selectedNode.person.name} · {selectedNode.person.title}</div>
                </div>
              )}
              
              {selectedNode.metrics && (
                <>
                  <div>
                    <div className="text-sm text-slate-400 mb-1">业绩完成率</div>
                    <div className="flex items-center gap-3">
                      <span className={`text-3xl font-bold ${selectedNode.metrics.achievement_rate >= 70 ? 'text-green-500' : selectedNode.metrics.achievement_rate >= 60 ? 'text-blue-500' : 'text-orange-500'}`}>
                        {selectedNode.metrics.achievement_rate}%
                      </span>
                      <Progress value={selectedNode.metrics.achievement_rate} className="flex-1" />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-slate-400">已完成</div>
                      <div className="text-lg font-bold">¥{(selectedNode.metrics.achieved_ytd / 1000000).toFixed(1)}M</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400">年度指标</div>
                      <div className="text-lg font-bold">¥{(selectedNode.metrics.quota_annual / 1000000).toFixed(0)}M</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400">团队人数</div>
                      <div className="text-lg font-bold">{selectedNode.metrics.team_size}人</div>
                    </div>
                    {selectedNode.metrics.pipeline_total && (
                      <div>
                        <div className="text-sm text-slate-400">Pipeline</div>
                        <div className="text-lg font-bold">¥{(selectedNode.metrics.pipeline_total / 1000000).toFixed(0)}M</div>
                      </div>
                    )}
                  </div>
                </>
              )}
              
              {selectedNode.children && selectedNode.children.length > 0 && (
                <div>
                  <div className="text-sm text-slate-400 mb-2">下属团队 ({selectedNode.children.length}个)</div>
                  <div className="space-y-2">
                    {selectedNode.children.map((child) => (
                      <div key={child.id} className="p-2 border rounded text-sm">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{child.name}</span>
                          <Badge variant="outline">{child.level}</Badge>
                        </div>
                        {child.metrics && (
                          <div className="text-xs text-slate-400 mt-1">
                            完成率：<span className={child.metrics.rate >= 70 ? 'text-green-500' : child.metrics.rate >= 60 ? 'text-blue-500' : 'text-orange-500'}>{child.metrics.rate}%</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-slate-400 py-8">
              <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <div>点击左侧组织节点查看详情</div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// 层级汇总视图
function HierarchyRollup() {
  const [selectedLevel, setSelectedLevel] = useState("Director");

  return (
    <div className="space-y-6">
      <Tabs value={selectedLevel} onValueChange={setSelectedLevel}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="GM">
            <Briefcase className="w-4 h-4 mr-2" />
            总经理
          </TabsTrigger>
          <TabsTrigger value="Director">
            <Building2 className="w-4 h-4 mr-2" />
            总监
          </TabsTrigger>
          <TabsTrigger value="Manager">
            <Users className="w-4 h-4 mr-2" />
            经理
          </TabsTrigger>
          <TabsTrigger value="Sales">
            <User className="w-4 h-4 mr-2" />
            销售
          </TabsTrigger>
        </TabsList>

        <TabsContent value="Director" className="mt-6">
          {/* 总监层级汇总 */}
          <Card>
            <CardHeader>
              <CardTitle>分公司业绩对比（总监级）</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>分公司</TableHead>
                    <TableHead>总监</TableHead>
                    <TableHead>团队规模</TableHead>
                    <TableHead>年度指标</TableHead>
                    <TableHead>已完成</TableHead>
                    <TableHead>完成率</TableHead>
                    <TableHead>同比增长</TableHead>
                    <TableHead>排名</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[
                    { branch: "深圳分公司", director: "张总监", team: 10, quota: 300, achieved: 198, rate: 66.0, yoy: 32.0, rank: 1 },
                    { branch: "合肥分公司", director: "王总监", team: 8, quota: 220, achieved: 139, rate: 63.2, yoy: 22.0, rank: 2 },
                    { branch: "苏州分公司", director: "李总监", team: 10, quota: 280, achieved: 175, rate: 62.5, yoy: 25.0, rank: 3 },
                  ].map((item) => (
                    <TableRow key={item.branch}>
                      <TableCell className="font-medium">{item.branch}</TableCell>
                      <TableCell>{item.director}</TableCell>
                      <TableCell>{item.team}人</TableCell>
                      <TableCell>¥{item.quota}M</TableCell>
                      <TableCell>¥{item.achieved}M</TableCell>
                      <TableCell>
                        <Badge variant={item.rate >= 70 ? "default" : item.rate >= 60 ? "secondary" : "destructive"}>
                          {item.rate}%
                        </Badge>
                      </TableCell>
                      <TableCell className="text-green-500">+{item.yoy}%</TableCell>
                      <TableCell>
                        <Badge variant="outline">#{item.rank}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="Manager" className="mt-6">
          {/* 经理层级汇总 */}
          <Card>
            <CardHeader>
              <CardTitle>团队业绩对比（经理级）</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>团队</TableHead>
                    <TableHead>经理</TableHead>
                    <TableHead>分公司</TableHead>
                    <TableHead>团队规模</TableHead>
                    <TableHead>年度指标</TableHead>
                    <TableHead>已完成</TableHead>
                    <TableHead>完成率</TableHead>
                    <TableHead>排名</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[
                    { team: "华南一区", manager: "张三", branch: "深圳", members: 4, quota: 100, achieved: 68, rate: 68.0, rank: 1 },
                    { team: "华南二区", manager: "李四", branch: "深圳", members: 3, quota: 100, achieved: 65, rate: 65.0, rank: 2 },
                    { team: "华南三区", manager: "王五", branch: "深圳", members: 3, quota: 100, achieved: 65, rate: 65.0, rank: 3 },
                    { team: "华东一区", manager: "赵经理", branch: "苏州", members: 4, quota: 100, achieved: 62, rate: 62.0, rank: 4 },
                    { team: "华东二区", manager: "钱经理", branch: "苏州", members: 3, quota: 80, achieved: 48, rate: 60.0, rank: 5 },
                    { team: "华北一区", manager: "孙经理", branch: "合肥", members: 3, quota: 80, achieved: 47, rate: 58.8, rank: 6 },
                  ].map((item) => (
                    <TableRow key={item.team}>
                      <TableCell className="font-medium">{item.team}</TableCell>
                      <TableCell>{item.manager}</TableCell>
                      <TableCell><Badge variant="outline">{item.branch}</Badge></TableCell>
                      <TableCell>{item.members}人</TableCell>
                      <TableCell>¥{item.quota}M</TableCell>
                      <TableCell>¥{item.achieved}M</TableCell>
                      <TableCell>
                        <Badge variant={item.rate >= 70 ? "default" : item.rate >= 60 ? "secondary" : "destructive"}>
                          {item.rate}%
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">#{item.rank}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="Sales" className="mt-6">
          {/* 销售个人排名 */}
          <Card>
            <CardHeader>
              <CardTitle>个人业绩排名（销售级）</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>排名</TableHead>
                    <TableHead>姓名</TableHead>
                    <TableHead>角色</TableHead>
                    <TableHead>团队</TableHead>
                    <TableHead>个人指标</TableHead>
                    <TableHead>已完成</TableHead>
                    <TableHead>完成率</TableHead>
                    <TableHead>商机数</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[
                    { name: "李小妹", role: "销售工程师", team: "华南一区", quota: 30, achieved: 22, rate: 73.3, opps: 2 },
                    { name: "王小助", role: "销售助理", team: "华南一区", quota: 20, achieved: 14, rate: 70.0, opps: 2 },
                    { name: "张三", role: "销售工程师", team: "华南一区", quota: 50, achieved: 32, rate: 64.0, opps: 3 },
                    { name: "赵六", role: "销售工程师", team: "华南二区", quota: 35, achieved: 21.7, rate: 62.0, opps: 2 },
                    { name: "钱七", role: "销售工程师", team: "华南二区", quota: 30, achieved: 18, rate: 60.0, opps: 2 },
                  ].map((item, idx) => (
                    <TableRow key={item.name}>
                      <TableCell>
                        <Badge variant={idx < 3 ? "default" : "outline"}>#{idx + 1}</Badge>
                      </TableCell>
                      <TableCell className="font-medium">{item.name}</TableCell>
                      <TableCell><Badge variant="secondary">{item.role}</Badge></TableCell>
                      <TableCell>{item.team}</TableCell>
                      <TableCell>¥{item.quota}M</TableCell>
                      <TableCell>¥{item.achieved}M</TableCell>
                      <TableCell>
                        <Badge variant={item.rate >= 70 ? "default" : item.rate >= 60 ? "secondary" : "destructive"}>
                          {item.rate}%
                        </Badge>
                      </TableCell>
                      <TableCell>{item.opps}个</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="GM" className="mt-6">
          {/* 总经理视图 */}
          <div className="grid md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">公司年度指标</div>
                <div className="text-2xl font-bold">¥800M</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">已完成</div>
                <div className="text-2xl font-bold text-green-500">¥512M</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">完成率</div>
                <div className="text-2xl font-bold">64.0%</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4">
                <div className="text-sm text-slate-400">同比增长</div>
                <div className="text-2xl font-bold text-green-500">+28%</div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// 主页面
export default function SalesOrganization() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="销售组织架构"
          description="4 层层级管理 · 数据自动汇总 · 钻取查看"
          icon={<Users className="w-6 h-6 text-indigo-500" />}
        />

        <Tabs defaultValue="tree" className="mt-6">
          <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
            <TabsTrigger value="tree">
              <Users className="w-4 h-4 mr-2" />
              组织树
            </TabsTrigger>
            <TabsTrigger value="rollup">
              <TrendingUp className="w-4 h-4 mr-2" />
              层级汇总
            </TabsTrigger>
          </TabsList>

          <TabsContent value="tree" className="mt-6">
            <OrganizationTree />
          </TabsContent>

          <TabsContent value="rollup" className="mt-6">
            <HierarchyRollup />
          </TabsContent>
        </Tabs>

        {/* 层级定义说明 */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>销售组织层级定义</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-4 gap-4">
              {[
                { level: "L1", name: "销售总经理", code: "GM", scope: "全公司", report: "CEO", manage: "所有总监" },
                { level: "L2", name: "销售总监", code: "Director", scope: "分公司", report: "销售总经理", manage: "2-3 个经理" },
                { level: "L3", name: "销售经理", code: "Manager", scope: "销售团队", report: "销售总监", manage: "3-5 人" },
                { level: "L4", name: "销售", code: "Sales", scope: "个人", report: "销售经理", manage: "-" },
              ].map((item) => (
                <Card key={item.level}>
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">{item.level}</Badge>
                      <span className="font-medium">{item.name}</span>
                    </div>
                    <div className="text-sm text-slate-400 space-y-1">
                      <div>范围：{item.scope}</div>
                      <div>汇报：{item.report}</div>
                      <div>管理：{item.manage}</div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
