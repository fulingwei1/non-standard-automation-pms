import React from 'react';
import { motion } from "framer-motion";
import { RefreshCw, FileSpreadsheet, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "../../../components/ui/button";
import { cn } from "../../../lib/utils";

export function EmployeeUploadModal({
    showUploadModal,
    setShowUploadModal,
    uploading,
    uploadResult,
    setUploadResult,
    fileInputRef,
    handleFileUpload
}) {
    if (!showUploadModal) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={() => {
                    setShowUploadModal(false);
                    setUploadResult(null);
                }}
            />
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="relative z-10 w-full max-w-lg bg-slate-900 border border-white/10 rounded-xl p-6 shadow-xl"
            >
                <h3 className="text-lg font-semibold text-white mb-4">
                    导入员工数据
                </h3>

                {/* 上传区域 */}
                <div
                    className={cn(
                        "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
                        uploading
                            ? "border-primary/50 bg-primary/5"
                            : "border-white/20 hover:border-primary/50 hover:bg-white/5",
                    )}
                    onClick={() => !uploading && fileInputRef.current?.click()}
                >
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".xlsx,.xls"
                        onChange={handleFileUpload}
                        className="hidden"
                    />
                    {uploading ? (
                        <div className="flex flex-col items-center gap-3">
                            <RefreshCw className="h-10 w-10 text-primary animate-spin" />
                            <div className="text-slate-300">正在导入...</div>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center gap-3">
                            <FileSpreadsheet className="h-10 w-10 text-slate-400" />
                            <div className="text-slate-300">
                                点击或拖拽上传 Excel 文件
                            </div>
                            <div className="text-xs text-slate-500">
                                支持 .xlsx、.xls 格式
                            </div>
                        </div>
                    )}
                </div>

                {/* 上传结果 */}
                {uploadResult && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={cn(
                            "mt-4 p-4 rounded-lg",
                            uploadResult.success
                                ? "bg-green-500/10 border border-green-500/30"
                                : "bg-red-500/10 border border-red-500/30",
                        )}
                    >
                        <div className="flex items-start gap-3">
                            {uploadResult.success ? (
                                <CheckCircle className="h-5 w-5 text-green-400 mt-0.5" />
                            ) : (
                                <AlertCircle className="h-5 w-5 text-red-400 mt-0.5" />
                            )}
                            <div>
                                <div
                                    className={
                                        uploadResult.success ? "text-green-300" : "text-red-300"
                                    }
                                >
                                    {uploadResult.message}
                                </div>
                                {uploadResult.success && (
                                    <div className="text-sm text-slate-400 mt-2">
                                        新增 {uploadResult.imported} 人 · 更新{" "}
                                        {uploadResult.updated} 人 · 跳过 {uploadResult.skipped}{" "}
                                        条
                                    </div>
                                )}
                                {uploadResult.errors?.length > 0 && (
                                    <div className="text-xs text-red-400/80 mt-2">
                                        {uploadResult.errors.slice(0, 3).map((err, i) => (
                                            <div key={i}>{err}</div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* 说明 */}
                <div className="mt-4 p-3 bg-white/5 rounded-lg text-xs text-slate-400 space-y-1">
                    <div className="font-medium text-slate-300 mb-2">导入说明：</div>
                    <div>• Excel 文件必须包含"姓名"列</div>
                    <div>
                        •
                        支持的列：姓名、一级部门、二级部门、三级部门、职务、联系方式、在职离职状态
                    </div>
                    <div>• 系统会根据 姓名+部门 判断员工是否已存在</div>
                    <div>• 已存在的员工会更新信息，不会重复创建</div>
                    <div>• 支持直接导入企业微信导出的通讯录</div>
                </div>

                {/* 按钮 */}
                <div className="mt-6 flex justify-end gap-3">
                    <Button
                        variant="outline"
                        onClick={() => {
                            setShowUploadModal(false);
                            setUploadResult(null);
                        }}
                    >
                        关闭
                    </Button>
                </div>
            </motion.div>
        </div>
    );
}
