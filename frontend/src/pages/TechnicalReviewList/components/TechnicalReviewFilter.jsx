import React from 'react';
import { Search, Plus } from "lucide-react";
import { Button, Input, Select, Card, CardContent } from "../../../components/ui";

export function TechnicalReviewFilter({
    searchKeyword, setSearchKeyword,
    projectId, setProjectId,
    reviewType, setReviewType,
    status, setStatus,
    projectList,
    onSearch,
    onReset,
    onCreate
}) {
    return (
        <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="p-4">
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <div className="md:col-span-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                            <Input
                                placeholder="搜索评审编号、名称..."
                                value={searchKeyword}
                                onChange={(e) => setSearchKeyword(e.target.value)}
                                onKeyPress={(e) => e.key === "Enter" && onSearch()}
                                className="pl-10 bg-slate-800/50 border-slate-700 text-slate-100"
                            />
                        </div>
                    </div>
                    <Select
                        value={projectId || ""}
                        onValueChange={(value) => setProjectId(value || null)}
                        className="bg-slate-800/50 border-slate-700"
                    >
                        <option value="">全部项目</option>
                        {projectList.map((p) => (
                            <option key={p.id} value={p.id}>
                                {p.project_code} - {p.project_name}
                            </option>
                        ))}
                    </Select>
                    <Select
                        value={reviewType || ""}
                        onValueChange={(value) => setReviewType(value || null)}
                        className="bg-slate-800/50 border-slate-700"
                    >
                        <option value="">全部类型</option>
                        <option value="PDR">方案设计评审</option>
                        <option value="DDR">详细设计评审</option>
                        <option value="PRR">生产准备评审</option>
                        <option value="FRR">出厂评审</option>
                        <option value="ARR">现场评审</option>
                    </Select>
                    <Select
                        value={status || ""}
                        onValueChange={(value) => setStatus(value || null)}
                        className="bg-slate-800/50 border-slate-700"
                    >
                        <option value="">全部状态</option>
                        <option value="DRAFT">草稿</option>
                        <option value="PENDING">待评审</option>
                        <option value="IN_PROGRESS">评审中</option>
                        <option value="COMPLETED">已完成</option>
                        <option value="CANCELLED">已取消</option>
                    </Select>
                </div>
                <div className="flex gap-2 mt-4">
                    <Button onClick={onSearch} className="bg-blue-600 hover:bg-blue-700">
                        <Search className="w-4 h-4 mr-2" />
                        搜索
                    </Button>
                    <Button onClick={onReset} variant="outline" className="border-slate-700">
                        重置
                    </Button>
                    <Button onClick={onCreate} className="bg-emerald-600 hover:bg-emerald-700 ml-auto">
                        <Plus className="w-4 h-4 mr-2" />
                        创建技术评审
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
