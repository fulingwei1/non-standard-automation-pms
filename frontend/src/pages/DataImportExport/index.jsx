import { motion } from "framer-motion";
import { CheckCircle, XCircle } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { fadeIn } from "../../lib/animations";
import { useDataImportExport } from "./hooks";
import { DataImportPanel, DataExportPanel, ImportPreviewResult } from "./components";

export default function DataImportExport() {
    const {
        loading,
        error,
        success,
        templateTypes,
        selectedTemplateType, setSelectedTemplateType,
        importFile, setImportFile,
        previewData,
        updateExisting, setUpdateExisting,
        exportType, setExportType,
        exportFilters, setExportFilters,
        handleDownloadTemplate,
        handlePreviewImport,
        handleUploadImport,
        handleExport
    } = useDataImportExport();

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
                    <DataImportPanel
                        loading={loading}
                        templateTypes={templateTypes}
                        selectedTemplateType={selectedTemplateType}
                        setSelectedTemplateType={setSelectedTemplateType}
                        importFile={importFile}
                        setImportFile={setImportFile}
                        updateExisting={updateExisting}
                        setUpdateExisting={setUpdateExisting}
                        onDownloadTemplate={handleDownloadTemplate}
                        onPreviewImport={handlePreviewImport}
                        onUploadImport={handleUploadImport}
                    />

                    <ImportPreviewResult previewData={previewData} />
                </TabsContent>

                {/* 导出标签页 */}
                <TabsContent value="export" className="space-y-4">
                    <DataExportPanel
                        loading={loading}
                        exportType={exportType}
                        setExportType={setExportType}
                        exportFilters={exportFilters}
                        setExportFilters={setExportFilters}
                        onExport={handleExport}
                    />
                </TabsContent>
            </Tabs>
        </motion.div>
    );
}
