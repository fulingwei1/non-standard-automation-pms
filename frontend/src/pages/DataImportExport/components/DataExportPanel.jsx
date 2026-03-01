import React from 'react';
import { Download } from "lucide-react";
import {
    Card,
    CardHeader,
    CardTitle,
    CardContent,
    Button,
    Input,
    Select,
    SelectTrigger,
    SelectValue,
    SelectContent,
    SelectItem,
    Label
} from "../../../components/ui";

export function DataExportPanel({
    loading,
    exportType,
    setExportType,
    exportFilters,
    setExportFilters,
    onExport
}) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>导出数据</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                <div>
                    <Label>导出类型</Label>
                    <Select value={exportType || "unknown"} onValueChange={setExportType}>
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
                                        project_id: parseInt(e.target.value)
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
                                            start_date: e.target.value
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
                                            end_date: e.target.value
                                        })
                                    }
                                />
                            </div>
                        </>
                    )}
                </div>

                <Button onClick={onExport} disabled={loading}>
                    <Download className="h-4 w-4 mr-2" />
                    导出数据
                </Button>
            </CardContent>
        </Card>
    );
}
