/**
 * Accountability Analysis Page - 深度归责分析
 * Features: 按环节归责、按人员归责、按部门归责、责任成本分析
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Users,
  Building2,
  DollarSign,
  TrendingDown,
  AlertTriangle,
  BarChart3,
  Calendar,
  Filter,
} from "lucide-react";
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
  TabsTrigger,
} from "../components/ui";
import { fadeIn, staggerContainer } from "../lib/animations";
import { accountabilityApi } from "../services/api";
import { formatAmount, formatDate } from "../lib/utils";

export default function AccountabilityAnalysis() {
  const [loading, setLoading] = useState(false);
  const [byStageData, setByStageData] = useState(null);
  const [byPersonData, setByPersonData] = useState(null);
  const [byDepartmentData, setByDepartmentData] = useState(null);
  const [costImpactData, setCostImpactData] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [activeTab, setActiveTab] = useState("stage");

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const [stageRes, personRes, deptRes, costRes] = await Promise.all([
        accountabilityApi.getByStage(params),
        accountabilityApi.getByPerson(params),
        accountabilityApi.getByDepartment(params),
        accountabilityApi.getCostImpact(params),
      ]);

      if (stageRes.data?.data) setByStageData(stageRes.data.data);
      if (personRes.data?.data) setByPersonData(personRes.data.data);
      if (deptRes.data?.data) setByDepartmentData(deptRes.data.data);
      if (costRes.data?.data) setCostImpactData(costRes.data.data);
    } catch (error) {
      console.error("加载归责分析失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, []);

  const getBreakStageLabel = (stage) => {
    const labels = {
      LEAD_TO_OPP: "线索→商机",
      OPP_TO_QUOTE: "商机→报价",
      QUOTE_TO_CONTRACT: "报价→合同",
      CONTRACT_TO_PROJECT: "合同→项目",
      PROJECT_TO_INVOICE: "项目→发票",
      INVOICE_TO_PAYMENT: "发票→回款",
    };
    return labels[stage] || stage;
  };

  return (
    <div className="space-y-6">
      <PageHeader title="深度归责分析" />

      {/* 筛选条件 */}
      <Card>
        <CardHeader>
          <CardTitle>筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                开始日期
              </label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                结束日期
              </label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={loadAnalysis} className="w-full">
                查询
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 责任成本总览 */}
      {costImpactData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-slate-500">总成本影响</div>
              <div className="text-2xl font-bold mt-2">
                {formatAmount(costImpactData.summary?.total_cost_impact || 0)}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-slate-500">总机会成本</div>
              <div className="text-2xl font-bold mt-2">
                {formatAmount(
                  costImpactData.summary?.total_opportunity_cost || 0
                )}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-sm text-slate-500">总损失</div>
              <div className="text-2xl font-bold mt-2 text-red-600">
                {formatAmount(costImpactData.summary?.total_loss || 0)}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="stage">按环节归责</TabsTrigger>
          <TabsTrigger value="person">按人员归责</TabsTrigger>
          <TabsTrigger value="department">按部门归责</TabsTrigger>
          <TabsTrigger value="cost">责任成本</TabsTrigger>
        </TabsList>

        {/* 按环节归责 */}
        <TabsContent value="stage">
          {byStageData && (
            <div className="space-y-6">
              {Object.entries(byStageData.by_stage || {}).map(
                ([stage, data]) => (
                  <Card key={stage}>
                    <CardHeader>
                      <CardTitle>{getBreakStageLabel(stage)}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="mb-4 text-sm text-slate-500">
                        总断链数: {data.total_breaks}
                      </div>
                      {data.by_person && data.by_person.length > 0 && (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>人员</TableHead>
                              <TableHead>部门</TableHead>
                              <TableHead>断链次数</TableHead>
                              <TableHead>成本影响</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {data.by_person.map((person, idx) => (
                              <TableRow key={idx}>
                                <TableCell>{person.person_name}</TableCell>
                                <TableCell>
                                  {person.department || "未设置"}
                                </TableCell>
                                <TableCell>{person.break_count}</TableCell>
                                <TableCell>
                                  {formatAmount(person.cost_impact)}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )}
                    </CardContent>
                  </Card>
                )
              )}
            </div>
          )}
        </TabsContent>

        {/* 按人员归责 */}
        <TabsContent value="person">
          {byPersonData && (
            <Card>
              <CardHeader>
                <CardTitle>按人员归责</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4 text-sm text-slate-500">
                  总人数: {byPersonData.summary?.total_people} · 总断链数:{" "}
                  {byPersonData.summary?.total_breaks} · 总成本影响:{" "}
                  {formatAmount(byPersonData.summary?.total_cost_impact || 0)}
                </div>
                {byPersonData.by_person && byPersonData.by_person.length > 0 && (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>人员</TableHead>
                        <TableHead>部门</TableHead>
                        <TableHead>总断链数</TableHead>
                        <TableHead>成本影响</TableHead>
                        <TableHead>机会成本</TableHead>
                        <TableHead>涉及环节</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {byPersonData.by_person.map((person, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{person.person_name}</TableCell>
                          <TableCell>{person.department || "未设置"}</TableCell>
                          <TableCell>{person.total_breaks}</TableCell>
                          <TableCell>
                            {formatAmount(person.cost_impact)}
                          </TableCell>
                          <TableCell>
                            {formatAmount(person.opportunity_cost)}
                          </TableCell>
                          <TableCell>
                            {Object.keys(person.stages || {}).length} 个环节
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 按部门归责 */}
        <TabsContent value="department">
          {byDepartmentData && (
            <Card>
              <CardHeader>
                <CardTitle>按部门归责</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4 text-sm text-slate-500">
                  总部门数: {byDepartmentData.summary?.total_departments} ·
                  总断链数: {byDepartmentData.summary?.total_breaks} · 总成本影响:{" "}
                  {formatAmount(
                    byDepartmentData.summary?.total_cost_impact || 0
                  )}
                </div>
                {byDepartmentData.by_department &&
                  byDepartmentData.by_department.length > 0 && (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>部门</TableHead>
                          <TableHead>总断链数</TableHead>
                          <TableHead>成本影响</TableHead>
                          <TableHead>涉及人员</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {byDepartmentData.by_department.map((dept, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{dept.department}</TableCell>
                            <TableCell>{dept.total_breaks}</TableCell>
                            <TableCell>{formatAmount(dept.cost_impact)}</TableCell>
                            <TableCell>{dept.person_count} 人</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 责任成本 */}
        <TabsContent value="cost">
          {costImpactData && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>按环节成本影响</CardTitle>
                </CardHeader>
                <CardContent>
                  {costImpactData.by_stage && (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>环节</TableHead>
                          <TableHead>成本影响</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {Object.entries(costImpactData.by_stage).map(
                          ([stage, cost]) => (
                            <TableRow key={stage}>
                              <TableCell>
                                {getBreakStageLabel(stage)}
                              </TableCell>
                              <TableCell>{formatAmount(cost)}</TableCell>
                            </TableRow>
                          )
                        )}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
