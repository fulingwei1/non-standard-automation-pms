import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui";

export function ImportPreviewResult({ previewData }) {
    if (!previewData) return null;

    return (
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

                    {previewData.errors && previewData.errors?.length > 0 && (
                        <div>
                            <div className="text-sm font-semibold mb-2">错误列表：</div>
                            <div className="max-h-60 overflow-y-auto space-y-1">
                                {previewData.errors.slice(0, 20).map((error, idx) => (
                                    <div
                                        key={idx}
                                        className="text-sm text-red-600 p-2 bg-red-50 rounded"
                                    >
                                        第 {error.row} 行，字段 {error.field}：{error.message}
                                    </div>
                                ))}
                                {previewData.errors?.length > 20 && (
                                    <div className="text-sm text-gray-500">
                                        还有 {previewData.errors?.length - 20} 个错误...
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {previewData.preview_data && previewData.preview_data?.length > 0 && (
                        <div>
                            <div className="text-sm font-semibold mb-2">
                                预览数据（前10行）：
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b">
                                            {Object.keys(previewData.preview_data[0] || {}).map(
                                                (key) => (
                                                    <th key={key} className="text-left p-2">
                                                        {key}
                                                    </th>
                                                )
                                            )}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {(previewData.preview_data || []).map((row, idx) => (
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
    );
}
