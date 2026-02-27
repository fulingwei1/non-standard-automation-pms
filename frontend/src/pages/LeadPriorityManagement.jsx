/**
 * Lead Priority Management Page - 销售线索优先级管理
 * Features: 优先级评分、关键线索筛选、优先级排名
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Star,
  TrendingUp,
  Target,
  Users,
  Building2,
  AlertCircle,
  CheckCircle2,
  Clock,
  Filter,
  RefreshCw } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui";
import { fadeIn as _fadeIn, staggerContainer as _staggerContainer } from "../lib/animations";
import { priorityApi } from "../services/api";

export default function LeadPriorityManagement() {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("leads");
  const [leadRankings, setLeadRankings] = useState([]);
  const [opportunityRankings, setOpportunityRankings] = useState([]);
  const [keyLeads, setKeyLeads] = useState([]);
  const [keyOpportunities, setKeyOpportunities] = useState([]);

  const loadLeadRankings = async () => {
    setLoading(true);
    try {
      const response = await priorityApi.getLeadPriorityRanking({ limit: 100 });
      if (response.data && response.data.data) {
        setLeadRankings(response.data.data.rankings || []);
      }
    } catch (error) {
      console.error("加载线索排名失败:", error);
      alert("加载线索排名失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const loadOpportunityRankings = async () => {
    setLoading(true);
    try {
      const response = await priorityApi.getOpportunityPriorityRanking({ limit: 100 });
      if (response.data && response.data.data) {
        setOpportunityRankings(response.data.data.rankings || []);
      }
    } catch (error) {
      console.error("加载商机排名失败:", error);
      alert("加载商机排名失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const loadKeyLeads = async () => {
    try {
      const response = await priorityApi.getKeyLeads();
      if (response.data && response.data.data) {
        setKeyLeads(response.data.data.key_leads || []);
      }
    } catch (error) {
      console.error("加载关键线索失败:", error);
    }
  };

  const loadKeyOpportunities = async () => {
    try {
      const response = await priorityApi.getKeyOpportunities();
      if (response.data && response.data.data) {
        setKeyOpportunities(response.data.data.key_opportunities || []);
      }
    } catch (error) {
      console.error("加载关键商机失败:", error);
    }
  };

  const calculateAllPriorities = async () => {
    setLoading(true);
    try {
      // 批量计算所有线索的优先级
      const leadResponse = await priorityApi.getLeadPriorityRanking({ limit: 1000 });
      if (leadResponse.data && leadResponse.data.data) {
        const leads = leadResponse.data.data.rankings || [];
        for (const lead of leads) {
          try {
            await priorityApi.calculateLeadPriority(lead.id);
          } catch (_e) {
            console.warn(`计算线索 ${lead.id} 优先级失败:`, _e);
          }
        }
      }

      // 批量计算所有商机的优先级
      const oppResponse = await priorityApi.getOpportunityPriorityRanking({ limit: 1000 });
      if (oppResponse.data && oppResponse.data.data) {
        const opportunities = oppResponse.data.data.rankings || [];
        for (const opp of opportunities) {
          try {
            await priorityApi.calculateOpportunityPriority(opp.id);
          } catch (_e) {
            console.warn(`计算商机 ${opp.id} 优先级失败:`, _e);
          }
        }
      }

      alert("批量计算优先级完成");
      loadLeadRankings();
      loadOpportunityRankings();
      loadKeyLeads();
      loadKeyOpportunities();
    } catch (error) {
      console.error("批量计算优先级失败:", error);
      alert("批量计算优先级失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "leads") {
      loadLeadRankings();
      loadKeyLeads();
    } else {
      loadOpportunityRankings();
      loadKeyOpportunities();
    }
  }, [activeTab]);

  const getPriorityBadge = (level) => {
    const config = {
      P1: { label: "P1-重要且紧急", color: "bg-red-500", textColor: "text-red-600" },
      P2: { label: "P2-重要不紧急", color: "bg-orange-500", textColor: "text-orange-600" },
      P3: { label: "P3-不重要但紧急", color: "bg-yellow-500", textColor: "text-yellow-600" },
      P4: { label: "P4-不重要不紧急", color: "bg-slate-500", textColor: "text-slate-600" }
    };
    const cfg = config[level] || config.P4;
    return (
      <Badge className={`${cfg.textColor} bg-${cfg.color.replace("bg-", "")}/10`}>
        {cfg.label}
      </Badge>);

  };

  const getScoreColor = (score) => {
    if (score >= 80) {return "text-green-600";}
    if (score >= 70) {return "text-blue-600";}
    if (score >= 60) {return "text-yellow-600";}
    return "text-slate-600";
  };

  return (
    <div className="space-y-6">
      <PageHeader title="销售线索优先级管理" />

      {/* 操作栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button onClick={calculateAllPriorities} disabled={loading}>
                <RefreshCw className="h-4 w-4 mr-2" />
                批量计算优先级
              </Button>
            </div>
            <div className="text-sm text-slate-500">
              优先级评分范围：0-100分，≥70分为关键线索/商机
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 关键线索/商机统计 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">关键线索</p>
                <p className="text-2xl font-bold mt-1">{keyLeads.length}</p>
              </div>
              <Star className="h-8 w-8 text-yellow-500 fill-yellow-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">关键商机</p>
                <p className="text-2xl font-bold mt-1">{keyOpportunities.length}</p>
              </div>
              <Target className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 优先级排名 */}
      <Card>
        <CardHeader>
          <CardTitle>优先级排名</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="leads">线索排名</TabsTrigger>
              <TabsTrigger value="opportunities">商机排名</TabsTrigger>
            </TabsList>

            <TabsContent value="leads" className="mt-4">
              {loading ?
              <div className="text-center py-8 text-slate-500">加载中...</div> :

              <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>排名</TableHead>
                      <TableHead>线索编号</TableHead>
                      <TableHead>客户名称</TableHead>
                      <TableHead>优先级评分</TableHead>
                      <TableHead>优先级等级</TableHead>
                      <TableHead>重要程度</TableHead>
                      <TableHead>紧急程度</TableHead>
                      <TableHead>是否关键</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {leadRankings.map((lead, index) =>
                  <TableRow key={lead.id}>
                        <TableCell>
                          <Badge variant="outline">#{index + 1}</Badge>
                        </TableCell>
                        <TableCell>{lead.code}</TableCell>
                        <TableCell>{lead.name}</TableCell>
                        <TableCell>
                          <span className={`font-bold ${getScoreColor(lead.total_score)}`}>
                            {lead.total_score}
                          </span>
                          /100
                        </TableCell>
                        <TableCell>{getPriorityBadge(lead.priority_level)}</TableCell>
                        <TableCell>
                          <Badge
                        variant={
                        lead.importance_level === "HIGH" ?
                        "default" :
                        lead.importance_level === "MEDIUM" ?
                        "secondary" :
                        "outline"
                        }>

                            {lead.importance_level === "HIGH" ?
                        "高" :
                        lead.importance_level === "MEDIUM" ?
                        "中" :
                        "低"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                        variant={
                        lead.urgency_level === "HIGH" ?
                        "destructive" :
                        lead.urgency_level === "MEDIUM" ?
                        "secondary" :
                        "outline"
                        }>

                            {lead.urgency_level === "HIGH" ?
                        "高" :
                        lead.urgency_level === "MEDIUM" ?
                        "中" :
                        "低"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {lead.is_key ?
                      <Badge className="bg-yellow-500/10 text-yellow-600">
                              <Star className="h-3 w-3 mr-1 fill-yellow-500" />
                              关键
                      </Badge> :

                      <span className="text-slate-400">-</span>
                      }
                        </TableCell>
                  </TableRow>
                  )}
                  </TableBody>
              </Table>
              }
            </TabsContent>

            <TabsContent value="opportunities" className="mt-4">
              {loading ?
              <div className="text-center py-8 text-slate-500">加载中...</div> :

              <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>排名</TableHead>
                      <TableHead>商机编号</TableHead>
                      <TableHead>商机名称</TableHead>
                      <TableHead>优先级评分</TableHead>
                      <TableHead>优先级等级</TableHead>
                      <TableHead>重要程度</TableHead>
                      <TableHead>紧急程度</TableHead>
                      <TableHead>是否关键</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {opportunityRankings.map((opp, index) =>
                  <TableRow key={opp.id}>
                        <TableCell>
                          <Badge variant="outline">#{index + 1}</Badge>
                        </TableCell>
                        <TableCell>{opp.code}</TableCell>
                        <TableCell>{opp.name}</TableCell>
                        <TableCell>
                          <span className={`font-bold ${getScoreColor(opp.total_score)}`}>
                            {opp.total_score}
                          </span>
                          /100
                        </TableCell>
                        <TableCell>{getPriorityBadge(opp.priority_level)}</TableCell>
                        <TableCell>
                          <Badge
                        variant={
                        opp.importance_level === "HIGH" ?
                        "default" :
                        opp.importance_level === "MEDIUM" ?
                        "secondary" :
                        "outline"
                        }>

                            {opp.importance_level === "HIGH" ?
                        "高" :
                        opp.importance_level === "MEDIUM" ?
                        "中" :
                        "低"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                        variant={
                        opp.urgency_level === "HIGH" ?
                        "destructive" :
                        opp.urgency_level === "MEDIUM" ?
                        "secondary" :
                        "outline"
                        }>

                            {opp.urgency_level === "HIGH" ?
                        "高" :
                        opp.urgency_level === "MEDIUM" ?
                        "中" :
                        "低"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {opp.is_key ?
                      <Badge className="bg-yellow-500/10 text-yellow-600">
                              <Star className="h-3 w-3 mr-1 fill-yellow-500" />
                              关键
                      </Badge> :

                      <span className="text-slate-400">-</span>
                      }
                        </TableCell>
                  </TableRow>
                  )}
                  </TableBody>
              </Table>
              }
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>);

}