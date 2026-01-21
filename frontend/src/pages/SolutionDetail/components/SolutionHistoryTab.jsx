import React from 'react';
import { GitBranch, History } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/card";
import { Badge } from "../../../components/ui/badge";
import { cn } from "../../../lib/utils";

export function SolutionHistoryTab({ solution }) {
    return (
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
            <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                    <GitBranch className="w-5 h-5 text-primary" />
                    版本历史
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-6">
                    {solution.versionHistory.map((version, index) => (
                        <div key={index} className="flex gap-4">
                            <div className="flex flex-col items-center">
                                <div
                                    className={cn(
                                        "w-8 h-8 rounded-full flex items-center justify-center",
                                        index === 0 ? "bg-primary" : "bg-slate-600",
                                    )}
                                >
                                    <History className="w-4 h-4 text-white" />
                                </div>
                                {index < solution.versionHistory.length - 1 && (
                                    <div className="w-px h-full bg-slate-700 my-2" />
                                )}
                            </div>
                            <div className="flex-1 pb-6">
                                <div className="flex items-center gap-3 mb-1">
                                    <Badge
                                        variant="outline"
                                        className={cn(
                                            "text-xs",
                                            index === 0 && "border-primary text-primary",
                                        )}
                                    >
                                        {version.version}
                                    </Badge>
                                    <span className="text-sm text-slate-400">
                                        {version.date}
                                    </span>
                                    <span className="text-sm text-slate-500">
                                        by {version.author}
                                    </span>
                                </div>
                                <p className="text-sm text-white">{version.changes}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
