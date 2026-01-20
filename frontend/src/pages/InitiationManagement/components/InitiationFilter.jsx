import React from 'react';
import { Search } from "lucide-react";
import { Card, CardContent, Input } from "../../../components/ui";

export function InitiationFilter({ keyword, setKeyword, statusFilter, setStatusFilter }) {
    return (
        <Card className="mb-6">
            <CardContent className="p-4">
                <div className="flex flex-col sm:flex-row gap-4">
                    <div className="flex-1">
                        <Input
                            placeholder="搜索申请编号、项目名称..."
                            value={keyword}
                            onChange={(e) => setKeyword(e.target.value)}
                            className="w-full"
                            icon={Search}
                        />
                    </div>
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                        <option value="">全部状态</option>
                        <option value="DRAFT">草稿</option>
                        <option value="SUBMITTED">已提交</option>
                        <option value="REVIEWING">评审中</option>
                        <option value="APPROVED">已通过</option>
                        <option value="REJECTED">已驳回</option>
                    </select>
                </div>
            </CardContent>
        </Card>
    );
}
