import React from "react";
import { CheckCircle2 } from "lucide-react";
import { Card, CardContent, Badge } from "../../../components/ui";
import { getStatusBadge } from "../constants";

export function ProjectClosureStatusCard({ status }) {
    const badge = getStatusBadge(status);

    return (
        <Card>
            <CardContent className="p-5">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500/20 to-green-500/10 ring-1 ring-emerald-500/20">
                            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                        </div>
                        <div>
                            <h3 className="font-semibold text-white">结项状态</h3>
                            <p className="text-sm text-slate-400">
                                {badge.label}
                            </p>
                        </div>
                    </div>
                    <Badge variant={badge.variant}>
                        {badge.label}
                    </Badge>
                </div>
            </CardContent>
        </Card>
    );
}
