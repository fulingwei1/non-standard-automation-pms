import React from "react";
import { Card, CardContent } from "../../components/ui";
import { Building2, Clock, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function LeadStatsCards({ stats }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">总线索数</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </div>
            <Building2 className="h-8 w-8 text-blue-400" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">待跟进</p>
              <p className="text-2xl font-bold text-white">{stats.new}</p>
            </div>
            <Clock className="h-8 w-8 text-blue-400" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">评估中</p>
              <p className="text-2xl font-bold text-white">
                {stats.qualifying}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-amber-400" />
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">已转化</p>
              <p className="text-2xl font-bold text-white">
                {stats.converted}
              </p>
            </div>
            <CheckCircle2 className="h-8 w-8 text-emerald-400" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
