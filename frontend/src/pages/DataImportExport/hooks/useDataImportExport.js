import { useState, useEffect, useCallback } from "react";
import { dataImportExportApi } from "../../../services/api";

export function useDataImportExport() {
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
                `导入模板_${templateType}_${new Date().toISOString().split("T")[0]}.xlsx`
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
                selectedTemplateType
            );
            const data = response.data?.data || response.data || response;
            setPreviewData(data);

            if (data.errors && data.errors.length > 0) {
                setError(`发现 ${data.errors.length} 个错误，请检查数据`);
            } else {
                setSuccess(
                    `预览成功：共 ${data.total_rows} 行，有效 ${data.valid_rows} 行`
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
                updateExisting
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

    return {
        loading,
        error,
        success,
        templateTypes,
        selectedTemplateType, setSelectedTemplateType,
        importFile, setImportFile,
        previewData, setPreviewData,
        updateExisting, setUpdateExisting,
        exportType, setExportType,
        exportFilters, setExportFilters,
        handleDownloadTemplate,
        handlePreviewImport,
        handleUploadImport,
        handleExport
    };
}
