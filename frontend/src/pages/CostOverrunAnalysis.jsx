/**
 * Cost Overrun Analysis Page - 成本过高分析
 * Features: 成本超支原因分析、归责分析、影响分析
 */

import { useState, useEffect } from "react";


import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
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
import { costOverrunApi } from "../services/api";
import { formatAmount } from "../lib/utils";

export default function CostOverrunAnalysis() {
  const [_loading, setLoading] = useState(false);
  const [reasonsData, setReasonsData] = useState(null);
  const [accountabilityData, setAccountabilityData] = useState(null);
  const [impactData, setImpactData] = useState(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [projectId, setProjectId] = useState("");
  const [activeTab, setActiveTab] = useState("reasons");

  const loadReasons = async () => {
    setLoading(true);
    try {
      const params = {};
      if (startDate) {params.start_date = startDate;}
      if (endDate) {params.end_date = endDate;}
      if (projectId) {params.project_id = parseInt(projectId);}

      const response = await costOverrunApi.getReasons(params);
      if (response.data?.data) {
        setReasonsData(response.data.data);
      }
    } catch (error) {
      console.error("加载成本超支原因失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadAccountability = async () => {
    setLoading(true);
    try {
      const params = {};
      if (startDate) {params.start_date = startDate;}
      if (endDate) {params.end_date = endDate;}

      const response = await costOverrunApi.getAccountability(params);
      if (response.data?.data) {
        setAccountabilityData(response.data.data);
      }
    } catch (error) {
      console.error("加载成本超支归责失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadImpact = async () => {
    setLoading(true);
    try {
      const params = {};
      if (startDate) {params.start_date = startDate;}
      if (endDate) {params.end_date = endDate;}

      const response = await costOverrunApi.getImpact(params);
      if (response.data?.data) {
        setImpactData(response.data.data);
      }
    } catch (error) {
      console.error("加载成本超支影响失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "reasons") {loadReasons();}
    if (activeTab === "accountability") {loadAccountability();}
    if (activeTab === "impact") {loadImpact();}
  }, [activeTab]);

  return (
    <div className="space-y-6">
      <PageHeader title="成本过高分析" />

      {/* 筛选条件 */}
      <Card>
        <CardHeader>
          <CardTitle>筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                开始日期
              </label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)} />

            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                结束日期
              </label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)} />

            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                项目ID（可选）
              </label>
              <Input
                type="number"
                placeholder="项目ID"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)} />

            </div>
            <div className="flex items-end">
              <Button onClick={loadReasons} className="w-full">
                查询
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="reasons">超支原因</TabsTrigger>
          <TabsTrigger value="accountability">归责分析</TabsTrigger>
          <TabsTrigger value="impact">影响分析</TabsTrigger>
        </TabsList>

        {/* 超支原因 */}
        <TabsContent value="reasons">
          {reasonsData &&
          <div className="space-y-6">
              <Card>
                <CardContent className="pt-6">
                  <div className="text-sm text-slate-500">
                    成本超支项目总数
                  </div>
                  <div className="text-2xl font-bold mt-2">
                    {reasonsData.total_overrun_projects || 0}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>超支原因统计</CardTitle>
                </CardHeader>
                <CardContent>
                  {reasonsData.reasons && reasonsData.reasons.length > 0 &&
                <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>超支原因</TableHead>
                          <TableHead>项目数</TableHead>
                          <TableHead>总超支金额</TableHead>
                          <TableHead>平均超支金额</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {reasonsData.reasons.map((reason, idx) =>
                    <TableRow key={idx}>
                            <TableCell>{reason.reason}</TableCell>
                            <TableCell>{reason.count}</TableCell>
                            <TableCell>
                              {formatAmount(reason.total_overrun)}
                            </TableCell>
                            <TableCell>
                              {formatAmount(reason.average_overrun)}
                            </TableCell>
                    </TableRow>
                    )}
                      </TableBody>
                </Table>
                }
                </CardContent>
              </Card>
          </div>
          }
        </TabsContent>

        {/* 归责分析 */}
        <TabsContent value="accountability">
          {accountabilityData &&
          <Card>
              <CardHeader>
                <CardTitle>按人员归责</CardTitle>
              </CardHeader>
              <CardContent>
                {accountabilityData.by_person &&
              accountabilityData.by_person.length > 0 &&
              <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>人员</TableHead>
                          <TableHead>部门</TableHead>
                          <TableHead>超支项目数</TableHead>
                          <TableHead>总超支金额</TableHead>
                          <TableHead>主要原因</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {accountabilityData.by_person.map((person, idx) =>
                  <TableRow key={idx}>
                            <TableCell>{person.person_name}</TableCell>
                            <TableCell>
                              {person.department || "未设置"}
                            </TableCell>
                            <TableCell>{person.overrun_count}</TableCell>
                            <TableCell>
                              {formatAmount(person.total_overrun)}
                            </TableCell>
                            <TableCell>
                              {Object.keys(person.reasons || {}).
                      slice(0, 2).
                      join(", ")}
                            </TableCell>
                  </TableRow>
                  )}
                      </TableBody>
              </Table>
              }
              </CardContent>
          </Card>
          }
        </TabsContent>

        {/* 影响分析 */}
        <TabsContent value="impact">
          {impactData &&
          <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-slate-500">总超支金额</div>
                    <div className="text-2xl font-bold mt-2 text-red-600">
                      {formatAmount(impactData.summary?.total_overrun || 0)}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-slate-500">总合同金额</div>
                    <div className="text-2xl font-bold mt-2">
                      {formatAmount(
                      impactData.summary?.total_contract_amount || 0
                    )}
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-sm text-slate-500">超支比例</div>
                    <div className="text-2xl font-bold mt-2">
                      {impactData.summary?.overrun_ratio?.toFixed(2) || 0}%
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>受影响项目</CardTitle>
                </CardHeader>
                <CardContent>
                  {impactData.affected_projects &&
                impactData.affected_projects.length > 0 &&
                <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>项目编码</TableHead>
                            <TableHead>合同金额</TableHead>
                            <TableHead>超支金额</TableHead>
                            <TableHead>毛利率影响</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {impactData.affected_projects.map((project, idx) =>
                    <TableRow key={idx}>
                              <TableCell>{project.project_code}</TableCell>
                              <TableCell>
                                {formatAmount(project.contract_amount)}
                              </TableCell>
                              <TableCell>
                                {formatAmount(project.overrun_amount)}
                              </TableCell>
                              <TableCell>
                                {project.margin_impact?.toFixed(2) || 0}%
                              </TableCell>
                    </TableRow>
                    )}
                        </TableBody>
                </Table>
                }
                </CardContent>
              </Card>
          </div>
          }
        </TabsContent>
      </Tabs>
    </div>);

}