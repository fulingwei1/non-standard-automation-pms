import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Upload,
  Download,
  FileSpreadsheet,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { Label } from "../components/ui/label";
import { Checkbox } from "../components/ui/checkbox";
import { dataImportExportApi } from "../services/api";
import { fadeIn } from "../lib/animations";

export default function DataImportExport() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // 导入相关
  const [templateTypes, setTemplateTypes] = useState([]);
  const [selectedTemplateType, setSelectedTemplateType] = useState("");
  const [importFile, setImportFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [updateExisting, setUpdateExisting] = useState(false);

  // 导出相关
  const [exportType, setExportType] = useState("project_list");
  const [exportFilters, setExportFilters] = useState({});

  useEffect(() => {
    loadTemplateTypes();
  }, []);

  const loadTemplateTypes = async () => {
    try {
      const response = await dataImportExportApi.getTemplateTypes();
      const data = response.data?.data || response.data || response;
      setTemplateTypes(data.types || []);
    } catch (err) {
      console.error("Failed to load template types:", err);
    }
  };

  const handleDownloadTemplate = async (templateType) => {
    try {
      setLoading(true);
      setError(null);
      const response = await dataImportExportApi.downloadTemplate(templateType);

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `导入模板_${templateType}_${new Date().toISOString().split("T")[0]}.xlsx`,
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSuccess("模板下载成功");
    } catch (err) {
      console.error("Failed to download template:", err);
      setError(err.response?.data?.detail || err.message || "下载模板失败");
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewImport = async () => {
    if (!importFile || !selectedTemplateType) {
      setError("请选择模板类型和文件");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await dataImportExportApi.previewImport(
        importFile,
        selectedTemplateType,
      );
      const data = response.data?.data || response.data || response;
      setPreviewData(data);

      if (data.errors && data.errors.length > 0) {
        setError(`发现 ${data.errors.length} 个错误，请检查数据`);
      } else {
        setSuccess(
          `预览成功：共 ${data.total_rows} 行，有效 ${data.valid_rows} 行`,
        );
      }
    } catch (err) {
      console.error("Failed to preview import:", err);
      setError(err.response?.data?.detail || err.message || "预览失败");
      setPreviewData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadImport = async () => {
    if (!importFile || !selectedTemplateType) {
      setError("请选择模板类型和文件");
      return;
    }

    if (!window.confirm("确定要导入数据吗？")) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const response = await dataImportExportApi.uploadImport(
        importFile,
        selectedTemplateType,
        updateExisting,
      );
      const data = response.data?.data || response.data || response;

      setSuccess(data.message || "导入成功");
      setImportFile(null);
      setPreviewData(null);
    } catch (err) {
      console.error("Failed to upload import:", err);
      setError(err.response?.data?.detail || err.message || "导入失败");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      let response;
      const exportData = { filters: exportFilters };

      switch (exportType) {
        case "project_list":
          response = await dataImportExportApi.exportProjectList(exportData);
          break;
        case "project_detail":
          if (!exportFilters.project_id) {
            setError("请选择项目");
            return;
          }
          response = await dataImportExportApi.exportProjectDetail(exportData);
          break;
        case "task_list":
          response = await dataImportExportApi.exportTaskList(exportData);
          break;
        case "timesheet":
          if (!exportFilters.start_date || !exportFilters.end_date) {
            setError("请选择日期范围");
            return;
          }
          response = await dataImportExportApi.exportTimesheet(exportData);
          break;
        case "workload":
          if (!exportFilters.start_date || !exportFilters.end_date) {
            setError("请选择日期范围");
            return;
          }
          response = await dataImportExportApi.exportWorkload(exportData);
          break;
        default:
          setError("请选择导出类型");
          return;
      }

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      const filename = `${exportType}_${new Date().toISOString().split("T")[0]}.xlsx`;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSuccess("导出成功");
    } catch (err) {
      console.error("Failed to export:", err);
      setError(err.response?.data?.detail || err.message || "导出失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeIn}
      className="space-y-6"
    >
      <PageHeader title="数据导入导出" />

      {/* 消息提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded flex items-center gap-2">
          <XCircle className="h-5 w-5" />
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded flex items-center gap-2">
          <CheckCircle className="h-5 w-5" />
          {success}
        </div>
      )}

      <Tabs defaultValue="import" className="space-y-4">
        <TabsList>
          <TabsTrigger value="import">数据导入</TabsTrigger>
          <TabsTrigger value="export">数据导出</TabsTrigger>
        </TabsList>

        {/* 导入标签页 */}
        <TabsContent value="import" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>导入数据</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>模板类型</Label>
                  <Select
                    value={selectedTemplateType}
                    onValueChange={setSelectedTemplateType}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择模板类型" />
                    </SelectTrigger>
                    <SelectContent>
                      {templateTypes.map((type) => (
                        <SelectItem key={type.type} value={type.type}>
                          {type.name} - {type.description}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>选择文件</Label>
                  <Input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="update-existing"
                  checked={updateExisting}
                  onCheckedChange={setUpdateExisting}
                />
                <Label htmlFor="update-existing" className="cursor-pointer">
                  更新已存在的数据
                </Label>
              </div>

              <div className="flex gap-2">
                {selectedTemplateType && (
                  <Button
                    variant="outline"
                    onClick={() => handleDownloadTemplate(selectedTemplateType)}
                    disabled={loading}
                  >
                    <Download className="h-4 w-4 mr-2" />
                    下载模板
                  </Button>
                )}
                <Button
                  onClick={handlePreviewImport}
                  disabled={loading || !importFile || !selectedTemplateType}
                >
                  <FileSpreadsheet className="h-4 w-4 mr-2" />
                  预览数据
                </Button>
                <Button
                  onClick={handleUploadImport}
                  disabled={loading || !importFile || !selectedTemplateType}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  导入数据
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* 预览数据 */}
          {previewData && (
            <Card>
              <CardHeader>
                <CardTitle>预览结果</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">总行数</div>
                      <div className="text-2xl font-bold">
                        {previewData.total_rows || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">有效行数</div>
                      <div className="text-2xl font-bold text-green-600">
                        {previewData.valid_rows || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">无效行数</div>
                      <div className="text-2xl font-bold text-red-600">
                        {previewData.invalid_rows || 0}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">错误数</div>
                      <div className="text-2xl font-bold text-orange-600">
                        {previewData.errors?.length || 0}
                      </div>
                    </div>
                  </div>

                  {previewData.errors && previewData.errors.length > 0 && (
                    <div>
                      <div className="text-sm font-semibold mb-2">
                        错误列表：
                      </div>
                      <div className="max-h-60 overflow-y-auto space-y-1">
                        {previewData.errors.slice(0, 20).map((error, idx) => (
                          <div
                            key={idx}
                            className="text-sm text-red-600 p-2 bg-red-50 rounded"
                          >
                            第 {error.row} 行，字段 {error.field}：
                            {error.message}
                          </div>
                        ))}
                        {previewData.errors.length > 20 && (
                          <div className="text-sm text-gray-500">
                            还有 {previewData.errors.length - 20} 个错误...
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {previewData.preview_data &&
                    previewData.preview_data.length > 0 && (
                      <div>
                        <div className="text-sm font-semibold mb-2">
                          预览数据（前10行）：
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b">
                                {Object.keys(
                                  previewData.preview_data[0] || {},
                                ).map((key) => (
                                  <th key={key} className="text-left p-2">
                                    {key}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {previewData.preview_data.map((row, idx) => (
                                <tr key={idx} className="border-b">
                                  {Object.values(row).map((value, cellIdx) => (
                                    <td key={cellIdx} className="p-2">
                                      {String(value || "")}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 导出标签页 */}
        <TabsContent value="export" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>导出数据</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>导出类型</Label>
                <Select value={exportType} onValueChange={setExportType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="project_list">项目列表</SelectItem>
                    <SelectItem value="project_detail">项目详情</SelectItem>
                    <SelectItem value="task_list">任务列表</SelectItem>
                    <SelectItem value="timesheet">工时数据</SelectItem>
                    <SelectItem value="workload">负荷数据</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* 导出筛选条件 */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {exportType === "project_detail" && (
                  <div>
                    <Label>项目ID</Label>
                    <Input
                      type="number"
                      placeholder="项目ID"
                      value={exportFilters.project_id || ""}
                      onChange={(e) =>
                        setExportFilters({
                          ...exportFilters,
                          project_id: parseInt(e.target.value),
                        })
                      }
                    />
                  </div>
                )}

                {(exportType === "timesheet" || exportType === "workload") && (
                  <>
                    <div>
                      <Label>开始日期</Label>
                      <Input
                        type="date"
                        value={exportFilters.start_date || ""}
                        onChange={(e) =>
                          setExportFilters({
                            ...exportFilters,
                            start_date: e.target.value,
                          })
                        }
                      />
                    </div>
                    <div>
                      <Label>结束日期</Label>
                      <Input
                        type="date"
                        value={exportFilters.end_date || ""}
                        onChange={(e) =>
                          setExportFilters({
                            ...exportFilters,
                            end_date: e.target.value,
                          })
                        }
                      />
                    </div>
                  </>
                )}
              </div>

              <Button onClick={handleExport} disabled={loading}>
                <Download className="h-4 w-4 mr-2" />
                导出数据
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
