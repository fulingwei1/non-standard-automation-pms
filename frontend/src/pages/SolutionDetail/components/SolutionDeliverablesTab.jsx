import { Upload, FileText, Download } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../../../components/ui/card";
import { Button } from "../../../components/ui/button";
import { cn } from "../../../lib/utils";
import { getDeliverableStatus } from "../constants";

export function SolutionDeliverablesTab({ solution }) {
    return (
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-lg">交付物清单</CardTitle>
                <Button size="sm" className="flex items-center gap-2">
                    <Upload className="w-4 h-4" />
                    上传文件
                </Button>
            </CardHeader>
            <CardContent>
                <div className="space-y-3">
                    {solution.deliverables.map((item) => {
                        const statusConfig = getDeliverableStatus(item.status);
                        const StatusIcon = statusConfig.icon;
                        return (
                            <div
                                key={item.id}
                                className="flex items-center justify-between p-4 bg-surface-50 rounded-lg hover:bg-white/[0.03] transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                                        <FileText className="w-5 h-5 text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-white">
                                            {item.name}
                                        </p>
                                        {item.file ? (
                                            <p className="text-xs text-slate-500">
                                                {item.file} ({item.size})
                                            </p>
                                        ) : (
                                            <p className="text-xs text-slate-500">待上传</p>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2">
                                        <StatusIcon
                                            className={cn("w-4 h-4", statusConfig.color)}
                                        />
                                        <span className={cn("text-xs", statusConfig.color)}>
                                            {statusConfig.text}
                                        </span>
                                    </div>
                                    {item.file && (
                                        <Button variant="ghost" size="sm">
                                            <Download className="w-4 h-4" />
                                        </Button>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </CardContent>
        </Card>
    );
}
