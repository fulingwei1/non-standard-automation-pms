/**
 * Qualification Assessment List - 任职资格评估记录列表
 * 用于查看和管理所有评估记录
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Search,
  Filter,
  Download,
  Eye,
  Calendar,
  TrendingUp,
  Award } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../components/ui/table";
import { QualificationTrendChart } from "../components/qualification/QualificationTrendChart";
import { qualificationApi } from "../services/api";
import { toast } from "../components/ui/toast";
import { formatDate } from "../lib/utils";
import { fadeIn } from "../lib/animations";

export default function QualificationAssessmentList() {
  const navigate = useNavigate();
  const [_loading, setLoading] = useState(false);
  const [assessments, setAssessments] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filters, setFilters] = useState({
    employee_id: "",
    qualification_id: "",
    assessment_type: "",
    result: ""
  });
  const [pagination, setPagination] = useState({
    page: 1,
    page_size: 20,
    total: 0
  });

  useEffect(() => {
    loadAssessments();
  }, [filters, pagination.page, searchKeyword]);

  const loadAssessments = async () => {
    setLoading(true);
    try {
      const params = {
        page: pagination.page,
        page_size: pagination.page_size,
        ...filters
      };
      if (searchKeyword) {
        params.keyword = searchKeyword;
      }

      // 这里需要调用评估记录列表API
      // 由于后端可能没有统一的评估记录列表接口，我们可以通过员工任职资格接口获取
      const response = await qualificationApi.getEmployeeQualifications({
        page: pagination.page,
        page_size: pagination.page_size,
        ...filters
      });

      if (response.data?.code === 200) {
        // 获取每个员工的评估记录
        const employeeIds =
        response.data.data?.items?.map((q) => q.employee_id) || [];
        const assessmentPromises = (employeeIds || []).map((id) =>
        qualificationApi.
        getAssessments(id).
        catch(() => ({ data: { data: { items: [] } } }))
        );
        const assessmentResults = await Promise.all(assessmentPromises);
        const allAssessments = (assessmentResults || []).flatMap(
          (res) => res.data?.data?.items || []
        );
        setAssessments(allAssessments);
        setPagination((prev) => ({
          ...prev,
          total: allAssessments.length
        }));
      }
    } catch (error) {
      console.error("加载评估记录失败:", error);
      toast.error("加载评估记录失败");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    try {
      const exportData = (assessments || []).map((assessment) => ({
        员工ID: assessment.employee_id,
        评估类型: assessment.assessment_type,
        评估周期: assessment.assessment_period,
        评估日期: assessment.assessed_at ?
        formatDate(assessment.assessed_at) :
        "-",
        综合得分: assessment.total_score || 0,
        评估结果: assessment.result,
        评估人: assessment.assessor_id || "-",
        备注: assessment.comments || "-"
      }));

      const headers = Object.keys(exportData[0] || {});
      const csvContent = [
      headers.join(","),
      ...(exportData || []).map((row) =>
      (headers || []).map((header) => `"${row[header] || ""}"`).join(",")
      )].
      join("\n");

      const BOM = "\uFEFF";
      const blob = new Blob([BOM + csvContent], {
        type: "text/csv;charset=utf-8;"
      });
      const link = document.createElement("a");
      const url = URL.createObjectURL(blob);
      link.setAttribute("href", url);
      link.setAttribute(
        "download",
        `评估记录列表_${new Date().toISOString().split("T")[0]}.csv`
      );
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success("导出成功");
    } catch (error) {
      console.error("导出失败:", error);
      toast.error("导出失败");
    }
  };

  const getResultBadge = (result) => {
    const badges = {
      PASS: { label: "通过", color: "bg-green-100 text-green-800" },
      PARTIAL: { label: "部分通过", color: "bg-yellow-100 text-yellow-800" },
      FAIL: { label: "未通过", color: "bg-red-100 text-red-800" }
    };
    const badge = badges[result] || {
      label: result,
      color: "bg-gray-100 text-gray-800"
    };
    return <Badge className={badge.color}>{badge.label}</Badge>;
  };

  // 按员工分组评估记录，用于趋势图
  const assessmentsByEmployee = (assessments || []).reduce((acc, assessment) => {
    const employeeId = assessment.employee_id;
    if (!acc[employeeId]) {
      acc[employeeId] = [];
    }
    acc[employeeId].push(assessment);
    return acc;
  }, {});

  return (
    <motion.div
      variants={fadeIn}
      initial="hidden"
      animate="show"
      className="space-y-6">

      <PageHeader
        title="评估记录管理"
        description="查看和管理所有任职资格评估记录"
        icon={ArrowLeft}
        onBack={() => navigate("/qualifications")} />


      {/* 搜索和筛选 */}
      <Card>
        <CardHeader>
          <CardTitle>搜索和筛选</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索员工ID、评估周期..."
                value={searchKeyword || "unknown"}
                onChange={(e) => setSearchKeyword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    setPagination((prev) => ({ ...prev, page: 1 }));
                    loadAssessments();
                  }
                }}
                className="pl-10" />

            </div>
            <Select
              value={filters.assessment_type}
              onValueChange={(value) =>
              setFilters({ ...filters, assessment_type: value })
              }>

              <SelectTrigger>
                <SelectValue placeholder="评估类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="ANNUAL">年度评估</SelectItem>
                <SelectItem value="PROMOTION">晋升评估</SelectItem>
                <SelectItem value="PERIODIC">定期评估</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.result}
              onValueChange={(value) =>
              setFilters({ ...filters, result: value })
              }>

              <SelectTrigger>
                <SelectValue placeholder="评估结果" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部</SelectItem>
                <SelectItem value="PASS">通过</SelectItem>
                <SelectItem value="PARTIAL">部分通过</SelectItem>
                <SelectItem value="FAIL">未通过</SelectItem>
              </SelectContent>
            </Select>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setSearchKeyword("");
                  setFilters({
                    employee_id: "",
                    qualification_id: "",
                    assessment_type: "",
                    result: ""
                  });
                  setPagination((prev) => ({ ...prev, page: 1 }));
                  loadAssessments();
                }}>

                重置
              </Button>
              <Button variant="outline" onClick={handleExport}>
                <Download className="h-4 w-4 mr-2" />
                导出
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 评估记录列表 */}
      <Card>
        <CardHeader>
          <CardTitle>评估记录</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>员工ID</TableHead>
                <TableHead>评估类型</TableHead>
                <TableHead>评估周期</TableHead>
                <TableHead>评估日期</TableHead>
                <TableHead>综合得分</TableHead>
                <TableHead>评估结果</TableHead>
                <TableHead>操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assessments.length === 0 ?
              <TableRow>
                  <TableCell
                  colSpan={7}
                  className="text-center text-gray-500 py-8">

                    暂无评估记录
                  </TableCell>
              </TableRow> :

              (assessments || []).map((assessment) =>
              <TableRow key={assessment.id}>
                    <TableCell className="font-medium">
                      员工 #{assessment.employee_id}
                    </TableCell>
                    <TableCell>{assessment.assessment_type}</TableCell>
                    <TableCell>{assessment.assessment_period || "-"}</TableCell>
                    <TableCell>
                      {assessment.assessed_at ?
                  formatDate(assessment.assessed_at) :
                  "-"}
                    </TableCell>
                    <TableCell>
                      <span className="font-semibold text-blue-600">
                        {assessment.total_score?.toFixed(1) || 0}
                      </span>
                    </TableCell>
                    <TableCell>{getResultBadge(assessment.result)}</TableCell>
                    <TableCell>
                      <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                    navigate(
                      `/qualifications/employees/${assessment.employee_id}/view`
                    )
                    }>

                        <Eye className="h-4 w-4 mr-2" />
                        查看详情
                      </Button>
                    </TableCell>
              </TableRow>
              )
              }
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* 评估趋势分析 */}
      {Object.keys(assessmentsByEmployee).length > 0 &&
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Object.entries(assessmentsByEmployee).
        slice(0, 4).
        map(([employeeId, employeeAssessments]) =>
        <Card key={employeeId}>
                <CardHeader>
                  <CardTitle>员工 #{employeeId} 评估趋势</CardTitle>
                </CardHeader>
                <CardContent>
                  <QualificationTrendChart
              data={(employeeAssessments || []).map((a) => ({
                date: a.assessed_at || a.assessment_period,
                total_score: a.total_score || 0,
                result: a.result,
                period: a.assessment_period
              }))} />

                </CardContent>
        </Card>
        )}
      </div>
      }

      {/* 分页 */}
      {pagination.total > pagination.page_size &&
      <Card>
          <CardContent className="flex items-center justify-between py-4">
            <div className="text-sm text-gray-500">
              共 {pagination.total} 条记录，第 {pagination.page} /{" "}
              {Math.ceil(pagination.total / pagination.page_size)} 页
            </div>
            <div className="flex gap-2">
              <Button
              variant="outline"
              size="sm"
              onClick={() =>
              setPagination((prev) => ({
                ...prev,
                page: Math.max(1, prev.page - 1)
              }))
              }
              disabled={pagination.page === 1}>

                上一页
              </Button>
              <Button
              variant="outline"
              size="sm"
              onClick={() =>
              setPagination((prev) => ({
                ...prev,
                page: Math.min(
                  Math.ceil(prev.total / prev.page_size),
                  prev.page + 1
                )
              }))
              }
              disabled={
              pagination.page >=
              Math.ceil(pagination.total / pagination.page_size)
              }>

                下一页
              </Button>
            </div>
          </CardContent>
      </Card>
      }
    </motion.div>);

}