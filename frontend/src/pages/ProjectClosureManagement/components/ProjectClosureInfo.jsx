import React from 'react';
import { Card, CardContent } from '../../../components/ui';
import { formatDate } from '../../../lib/utils';

export function ProjectClosureInfo({ closure }) {
    return (
        <>
            {/* Acceptance Info */}
            <Card>
                <CardContent className="p-5">
                    <h3 className="text-lg font-semibold text-white mb-4">
                        验收信息
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <span className="text-sm text-slate-400">验收日期</span>
                            <p className="text-white mt-1">
                                {closure.acceptance_date
                                    ? formatDate(closure.acceptance_date)
                                    : "未设置"}
                            </p>
                        </div>
                        <div>
                            <span className="text-sm text-slate-400">验收结果</span>
                            <p className="text-white mt-1">
                                {closure.acceptance_result || "未设置"}
                            </p>
                        </div>
                        {closure.acceptance_notes && (
                            <div className="col-span-2">
                                <span className="text-sm text-slate-400">验收说明</span>
                                <p className="text-white mt-1 whitespace-pre-wrap">
                                    {closure.acceptance_notes}
                                </p>
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Project Summary */}
            {closure.project_summary && (
                <Card>
                    <CardContent className="p-5">
                        <h3 className="text-lg font-semibold text-white mb-4">
                            项目总结
                        </h3>
                        <p className="text-white whitespace-pre-wrap">
                            {closure.project_summary}
                        </p>
                    </CardContent>
                </Card>
            )}

            {/* Achievement */}
            {closure.achievement && (
                <Card>
                    <CardContent className="p-5">
                        <h3 className="text-lg font-semibold text-white mb-4">
                            项目成果
                        </h3>
                        <p className="text-white whitespace-pre-wrap">
                            {closure.achievement}
                        </p>
                    </CardContent>
                </Card>
            )}
        </>
    );
}
