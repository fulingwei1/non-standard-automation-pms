/**
 * Quote Cost Analysis Page - 报价成本分析页面
 * Features: Version comparison, cost trend, cost structure analysis
 */

import { useState, useEffect, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Download } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui";
import { cn, formatCurrency, formatDate } from "../lib/utils";
import { staggerContainer } from "../lib/animations";
import { quoteApi } from "../services/api";
import { CostTrendChart } from "../components/cost/CostTrendChart";
import { CostStructureChart } from "../components/cost/CostStructureChart";

export default function QuoteCostAnalysis() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [quote, setQuote] = useState(null);
  const [versions, setVersions] = useState([]);
  const [selectedVersions, setSelectedVersions] = useState([null, null]);
  const [comparison, setComparison] = useState(null);
  const [costStructure, setCostStructure] = useState(null);
  const [_costTrend, setCostTrend] = useState(null);

  useEffect(() => {
    loadData();
  }, [id]);

  useEffect(() => {
    if (selectedVersions[0] && selectedVersions[1]) {
      loadComparison();
    }
  }, [selectedVersions]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load quote
      const quoteRes = await quoteApi.get(id);
      setQuote(quoteRes.data?.data || quoteRes.data);

      // Load versions
      const versionsRes = await quoteApi.getVersions(id);
      const versionsList = versionsRes.data?.data || versionsRes.data || [];
      setVersions(versionsList);

      // Set default selected versions (latest two)
      if (versionsList.length >= 2) {
        setSelectedVersions([
        versionsList[versionsList.length - 2],
        versionsList[versionsList.length - 1]]
        );
      } else if (versionsList.length === 1) {
        setSelectedVersions([versionsList[0], versionsList[0]]);
      }

      // Load cost structure for current version
      if (versionsList.length > 0) {
        const currentVersion = versionsList[versionsList.length - 1];
        try {
          const structureRes = await quoteApi.getCostStructure(
            id,
            currentVersion.id
          );
          setCostStructure(structureRes.data?.data || structureRes.data);
        } catch (_e) {
          console.log("Cost structure not available:", _e);
        }
      }

      // Load cost trend
      try {
        const trendRes = await quoteApi.getCostTrend(id, {});
        setCostTrend(trendRes.data?.data || trendRes.data);
      } catch (_e) {
        console.log("Cost trend not available:", _e);
      }
    } catch (error) {
      console.error("加载数据失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadComparison = async () => {
    try {
      const res = await quoteApi.compareCosts(id, {
        version_ids: `${selectedVersions[0].id},${selectedVersions[1].id}`
      });
      setComparison(res.data?.data || res.data);
    } catch (error) {
      console.error("加载对比数据失败:", error);
    }
  };

  // Calculate cost structure by category
  const structureByCategory = useMemo(() => {
    if (!costStructure?.by_category) {return [];}
    return costStructure.by_category.map((cat) => ({
      ...cat,
      percentage:
      costStructure.total_cost > 0 ?
      (cat.amount / costStructure.total_cost * 100).toFixed(2) :
      0
    }));
  }, [costStructure]);

  if (loading && !quote) {
    return (
      <div className="flex items-center justify-center h-64">加载中...</div>);

  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6">

      <PageHeader
        title="报价成本分析"
        description={quote ? `报价编号: ${quote.quote_no || id}` : ""}
        actions={
        <div className="flex gap-2">
            <Button
            variant="outline"
            onClick={() => navigate(`/sales/quotes/${id}/cost`)}>

              <ArrowLeft className="h-4 w-4 mr-2" />
              返回成本管理
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              导出报告
            </Button>
        </div>
        } />


      <Tabs defaultValue="comparison" className="space-y-4">
        <TabsList>
          <TabsTrigger value="comparison">版本对比</TabsTrigger>
          <TabsTrigger value="trend">成本趋势</TabsTrigger>
          <TabsTrigger value="structure">成本结构</TabsTrigger>
        </TabsList>

        {/* Version Comparison Tab */}
        <TabsContent value="comparison" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>版本对比</CardTitle>
              <CardDescription>对比不同版本的成本变化</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-6">
                <div className="flex-1">
                  <label className="text-sm text-slate-400 mb-2 block">
                    版本1
                  </label>
                  <Select
                    value={selectedVersions[0]?.id?.toString()}
                    onValueChange={(value) => {
                      const version = versions.find(
                        (v) => v.id.toString() === value
                      );
                      setSelectedVersions([version, selectedVersions[1]]);
                    }}>

                    <SelectTrigger>
                      <SelectValue placeholder="选择版本" />
                    </SelectTrigger>
                    <SelectContent>
                      {versions.map((v) =>
                      <SelectItem key={v.id} value={v.id.toString()}>
                          {v.version_no} - {formatDate(v.created_at)}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex-1">
                  <label className="text-sm text-slate-400 mb-2 block">
                    版本2
                  </label>
                  <Select
                    value={selectedVersions[1]?.id?.toString()}
                    onValueChange={(value) => {
                      const version = versions.find(
                        (v) => v.id.toString() === value
                      );
                      setSelectedVersions([selectedVersions[0], version]);
                    }}>

                    <SelectTrigger>
                      <SelectValue placeholder="选择版本" />
                    </SelectTrigger>
                    <SelectContent>
                      {versions.map((v) =>
                      <SelectItem key={v.id} value={v.id.toString()}>
                          {v.version_no} - {formatDate(v.created_at)}
                      </SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {comparison &&
              <div className="space-y-4">
                  {/* Summary Comparison */}
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-slate-400">
                          总价变化
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div
                        className={cn(
                          "text-2xl font-bold",
                          comparison.comparison?.price_change >= 0 ?
                          "text-green-400" :
                          "text-red-400"
                        )}>

                          {comparison.comparison?.price_change >= 0 ? "+" : ""}
                          {formatCurrency(
                          comparison.comparison?.price_change || 0
                        )}
                        </div>
                        <div className="text-sm text-slate-400 mt-1">
                          {comparison.comparison?.price_change_pct?.toFixed(2)}%
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-slate-400">
                          成本变化
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div
                        className={cn(
                          "text-2xl font-bold",
                          comparison.comparison?.cost_change >= 0 ?
                          "text-red-400" :
                          "text-green-400"
                        )}>

                          {comparison.comparison?.cost_change >= 0 ? "+" : ""}
                          {formatCurrency(
                          comparison.comparison?.cost_change || 0
                        )}
                        </div>
                        <div className="text-sm text-slate-400 mt-1">
                          {comparison.comparison?.cost_change_pct?.toFixed(2)}%
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-slate-400">
                          毛利率变化
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div
                        className={cn(
                          "text-2xl font-bold",
                          comparison.comparison?.margin_change >= 0 ?
                          "text-green-400" :
                          "text-red-400"
                        )}>

                          {comparison.comparison?.margin_change >= 0 ? "+" : ""}
                          {comparison.comparison?.margin_change?.toFixed(2)}%
                        </div>
                        <div className="text-sm text-slate-400 mt-1">
                          {comparison.comparison?.margin_change_pct?.toFixed(2)}
                          %
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Detailed Comparison Table */}
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>成本分类</TableHead>
                        <TableHead>版本1金额</TableHead>
                        <TableHead>版本2金额</TableHead>
                        <TableHead>变化金额</TableHead>
                        <TableHead>变化率</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {comparison.breakdown_comparison?.map((item, index) =>
                    <TableRow key={index}>
                          <TableCell>{item.category}</TableCell>
                          <TableCell>
                            {formatCurrency(item.v1_amount || 0)}
                          </TableCell>
                          <TableCell>
                            {formatCurrency(item.v2_amount || 0)}
                          </TableCell>
                          <TableCell
                        className={cn(
                          item.change >= 0 ?
                          "text-red-400" :
                          "text-green-400"
                        )}>

                            {item.change >= 0 ? "+" : ""}
                            {formatCurrency(item.change || 0)}
                          </TableCell>
                          <TableCell
                        className={cn(
                          item.change_pct >= 0 ?
                          "text-red-400" :
                          "text-green-400"
                        )}>

                            {item.change_pct >= 0 ? "+" : ""}
                            {item.change_pct?.toFixed(2)}%
                          </TableCell>
                    </TableRow>
                    )}
                    </TableBody>
                  </Table>
              </div>
              }

              {!comparison && selectedVersions[0] && selectedVersions[1] &&
              <div className="text-center py-8 text-slate-400">
                  加载对比数据中...
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cost Trend Tab */}
        <TabsContent value="trend" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>成本趋势</CardTitle>
              <CardDescription>分析报价多个版本的成本变化趋势</CardDescription>
            </CardHeader>
            <CardContent>
              {versions && versions.length > 0 ?
              <div className="space-y-4">
                  {/* Trend Chart */}
                  <div className="border border-slate-700 rounded-lg p-4 bg-slate-800/30">
                    <CostTrendChart
                    data={versions.map((v) => ({
                      version_no: v.version_no,
                      created_at: v.created_at,
                      total_price: v.total_price || 0,
                      total_cost: v.cost_total || 0,
                      gross_margin: v.gross_margin || 0
                    }))}
                    height={300}
                    showGrid
                    showPoints />

                  </div>

                  {/* Trend Data Table */}
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>版本</TableHead>
                        <TableHead>日期</TableHead>
                        <TableHead>总价</TableHead>
                        <TableHead>总成本</TableHead>
                        <TableHead>毛利率</TableHead>
                        <TableHead>变化</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {versions.map((version, index) => {
                      const prevVersion =
                      index > 0 ? versions[index - 1] : null;
                      const priceChange = prevVersion ?
                      (version.total_price || 0) - (
                      prevVersion.total_price || 0) :
                      0;
                      const marginChange = prevVersion ?
                      (version.gross_margin || 0) - (
                      prevVersion.gross_margin || 0) :
                      0;

                      return (
                        <TableRow key={version.id}>
                            <TableCell>{version.version_no}</TableCell>
                            <TableCell>
                              {formatDate(version.created_at)}
                            </TableCell>
                            <TableCell>
                              {formatCurrency(version.total_price || 0)}
                            </TableCell>
                            <TableCell>
                              {formatCurrency(version.cost_total || 0)}
                            </TableCell>
                            <TableCell>
                              {version.gross_margin?.toFixed(2)}%
                            </TableCell>
                            <TableCell>
                              {index > 0 &&
                            <div className="space-y-1">
                                  <div
                                className={cn(
                                  "text-sm",
                                  priceChange >= 0 ?
                                  "text-green-400" :
                                  "text-red-400"
                                )}>

                                    价格: {priceChange >= 0 ? "+" : ""}
                                    {formatCurrency(priceChange)}
                                  </div>
                                  <div
                                className={cn(
                                  "text-sm",
                                  marginChange >= 0 ?
                                  "text-green-400" :
                                  "text-red-400"
                                )}>

                                    毛利率: {marginChange >= 0 ? "+" : ""}
                                    {marginChange.toFixed(2)}%
                                  </div>
                            </div>
                            }
                            </TableCell>
                        </TableRow>);

                    })}
                    </TableBody>
                  </Table>
              </div> :

              <div className="text-center py-8 text-slate-400">
                  暂无版本数据
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cost Structure Tab */}
        <TabsContent value="structure" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>成本结构分析</CardTitle>
              <CardDescription>按成本分类统计和分析</CardDescription>
            </CardHeader>
            <CardContent>
              {costStructure && structureByCategory.length > 0 ?
              <div className="space-y-6">
                  {/* Summary */}
                  <div className="grid grid-cols-3 gap-4">
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-slate-400">
                          总成本
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {formatCurrency(costStructure.total_cost || 0)}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-slate-400">
                          成本分类数
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {costStructure.by_category?.length || 0}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm font-medium text-slate-400">
                          平均占比
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {costStructure.by_category?.length > 0 ?
                        (100 / costStructure.by_category.length).toFixed(
                          1
                        ) :
                        0}
                          %
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Structure Chart */}
                  <div className="border border-slate-700 rounded-lg p-6 bg-slate-800/30">
                    <CostStructureChart
                    data={structureByCategory.map((cat) => ({
                      category: cat.category,
                      amount: cat.amount,
                      percentage: parseFloat(cat.percentage)
                    }))}
                    size={300}
                    showLegend />

                  </div>

                  {/* Structure Table */}
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>成本分类</TableHead>
                        <TableHead>金额</TableHead>
                        <TableHead>占比</TableHead>
                        <TableHead>趋势</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {structureByCategory.map((category, index) =>
                    <TableRow key={index}>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div
                            className="w-3 h-3 rounded-full"
                            style={{
                              backgroundColor: `hsl(${index * 360 / structureByCategory.length}, 70%, 50%)`
                            }} />

                              {category.category}
                            </div>
                          </TableCell>
                          <TableCell>
                            {formatCurrency(category.amount || 0)}
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-slate-700 rounded-full h-2">
                                <div
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${category.percentage}%` }} />

                              </div>
                              <span className="text-sm w-16 text-right">
                                {category.percentage}%
                              </span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge className="bg-slate-600">-</Badge>
                          </TableCell>
                    </TableRow>
                    )}
                    </TableBody>
                  </Table>
              </div> :

              <div className="text-center py-8 text-slate-400">
                  暂无成本结构数据
              </div>
              }
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>);

}