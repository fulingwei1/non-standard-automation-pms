/**
 * Information Gap Analysis Page - 信息把握不足分析
 * Features: 信息缺失分析、影响分析、质量评分
 */

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  AlertCircle,
  CheckCircle2,
  XCircle,
  TrendingDown,
  BarChart3,
  Filter } from
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
import { informationGapApi } from "../services/api";
import { formatDate as _formatDate } from "../lib/utils";

export default function InformationGapAnalysis() {
  const [_loading, setLoading] = useState(false);
  const [missingData, setMissingData] = useState(null);
  const [impactData, setImpactData] = useState(null);
  const [qualityScore, setQualityScore] = useState(null);
  const [entityType, setEntityType] = useState("LEAD");
  const [entityId, setEntityId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, _setEndDate] = useState("");
  const [activeTab, setActiveTab] = useState("missing");

  const loadMissing = async () => {
    setLoading(true);
    try {
      const params = { entity_type: entityType };
      if (entityId) {params.entity_id = parseInt(entityId);}

      const response = await informationGapApi.getMissing(params);
      if (response.data?.data) {
        setMissingData(response.data.data);
      }
    } catch (error) {
      console.error("加载信息缺失分析失败:", error);
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

      const response = await informationGapApi.getImpact(params);
      if (response.data?.data) {
        setImpactData(response.data.data);
      }
    } catch (error) {
      console.error("加载信息影响分析失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadQualityScore = async () => {
    if (!entityId) {return;}
    setLoading(true);
    try {
      const response = await informationGapApi.getQualityScore({
        entity_type: entityType,
        entity_id: parseInt(entityId)
      });
      if (response.data?.data) {
        setQualityScore(response.data.data);
      }
    } catch (error) {
      console.error("加载质量评分失败:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "missing") {loadMissing();}
    if (activeTab === "impact") {loadImpact();}
  }, [activeTab]);

  const getQualityBadge = (score) => {
    if (score >= 80)
    {return <Badge variant="success">高质量</Badge>;}
    if (score >= 60)
    {return <Badge variant="warning">中等质量</Badge>;}
    return <Badge variant="destructive">低质量</Badge>;
  };

  return (
    <div className="space-y-6">
      <PageHeader title="信息把握不足分析" />

      {/* 筛选条件 */}
      <Card>
        <CardHeader>
          <CardTitle>筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                实体类型
              </label>
              <select
                className="w-full px-3 py-2 border rounded-md"
                value={entityType || "unknown"}
                onChange={(e) => setEntityType(e.target.value)}>

                <option value="LEAD">线索</option>
                <option value="OPPORTUNITY">商机</option>
                <option value="QUOTE">报价</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                实体ID（可选）
              </label>
              <Input
                type="number"
                placeholder="实体ID"
                value={entityId || "unknown"}
                onChange={(e) => setEntityId(e.target.value)} />

            </div>
            <div>
              <label className="text-sm text-slate-500 mb-1 block">
                开始日期
              </label>
              <Input
                type="date"
                value={startDate || "unknown"}
                onChange={(e) => setStartDate(e.target.value)} />

            </div>
            <div className="flex items-end gap-2">
              <Button onClick={loadMissing} className="flex-1">
                查询缺失
              </Button>
              <Button onClick={loadQualityScore} className="flex-1" disabled={!entityId}>
                质量评分
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs value={activeTab || "unknown"} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="missing">信息缺失</TabsTrigger>
          <TabsTrigger value="impact">影响分析</TabsTrigger>
          <TabsTrigger value="quality">质量评分</TabsTrigger>
        </TabsList>

        {/* 信息缺失 */}
        <TabsContent value="missing">
          {missingData &&
          <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>信息完整性</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="mb-4">
                    <div className="text-sm text-slate-500 mb-2">
                      完整度评分
                    </div>
                    <div className="text-3xl font-bold">
                      {missingData.completeness_score || 0} 分
                    </div>
                    {getQualityBadge(missingData.completeness_score || 0)}
                  </div>
                  {missingData.missing_fields &&
                missingData.missing_fields?.length > 0 &&
                <div>
                        <div className="text-sm text-slate-500 mb-2">
                          缺失字段
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {(missingData.missing_fields || []).map((field, idx) =>
                    <Badge key={idx} variant="destructive">
                              {field}
                    </Badge>
                    )}
                        </div>
                </div>
                }
                </CardContent>
              </Card>
          </div>
          }
        </TabsContent>

        {/* 影响分析 */}
        <TabsContent value="impact">
          {impactData &&
          <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>线索质量对转化率的影响</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-slate-500">高质量线索</div>
                      <div className="text-2xl font-bold mt-2">
                        {impactData.lead_quality_impact?.high_quality_count || 0}
                      </div>
                      <div className="text-sm text-slate-400 mt-1">
                        转化率:{" "}
                        {impactData.lead_quality_impact?.high_quality_conversion_rate?.toFixed(2) ||
                      0}
                        %
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500">低质量线索</div>
                      <div className="text-2xl font-bold mt-2">
                        {impactData.lead_quality_impact?.low_quality_count || 0}
                      </div>
                      <div className="text-sm text-slate-400 mt-1">
                        转化率:{" "}
                        {impactData.lead_quality_impact?.low_quality_conversion_rate?.toFixed(2) ||
                      0}
                        %
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <div className="text-sm font-medium text-blue-900">
                      转化率差距:{" "}
                      {impactData.lead_quality_impact?.conversion_gap?.toFixed(2) ||
                    0}
                      %
                    </div>
                    <div className="text-xs text-blue-700 mt-1">
                      高质量线索的转化率明显高于低质量线索
                    </div>
                  </div>
                </CardContent>
              </Card>
          </div>
          }
        </TabsContent>

        {/* 质量评分 */}
        <TabsContent value="quality">
          {qualityScore &&
          <Card>
              <CardHeader>
                <CardTitle>信息质量评分</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <div className="text-sm text-slate-500 mb-2">质量评分</div>
                  <div className="text-3xl font-bold">
                    {qualityScore.quality_score || 0} 分
                  </div>
                  {getQualityBadge(qualityScore.quality_score || 0)}
                  <div className="text-sm text-slate-400 mt-1">
                    质量等级: {qualityScore.quality_level}
                  </div>
                </div>
                {qualityScore.missing_fields &&
              qualityScore.missing_fields?.length > 0 &&
              <div className="mb-4">
                      <div className="text-sm text-slate-500 mb-2">
                        缺失字段
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {(qualityScore.missing_fields || []).map((field, idx) =>
                  <Badge key={idx} variant="destructive">
                            {field}
                  </Badge>
                  )}
                      </div>
              </div>
              }
                {qualityScore.recommendations &&
              qualityScore.recommendations?.length > 0 &&
              <div>
                      <div className="text-sm text-slate-500 mb-2">
                        改进建议
                      </div>
                      <ul className="list-disc list-inside space-y-1">
                        {(qualityScore.recommendations || []).map((rec, idx) =>
                  <li key={idx} className="text-sm">
                            {rec}
                  </li>
                  )}
                      </ul>
              </div>
              }
              </CardContent>
          </Card>
          }
        </TabsContent>
      </Tabs>
    </div>);

}