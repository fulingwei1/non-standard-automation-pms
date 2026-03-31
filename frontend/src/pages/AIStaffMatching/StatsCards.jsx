// -*- coding: utf-8 -*-
import { Target, Zap, Check, History } from "lucide-react";
import {
  Card,
  CardContent
} from "../../components/ui/card";

export default function StatsCards({ stats }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-blue-500/10">
              <Target className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-400">
                {stats.openNeeds}
              </div>
              <div className="text-sm text-slate-400">待匹配需求</div>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-yellow-500/10">
              <Zap className="h-6 w-6 text-yellow-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-yellow-400">
                {stats.matchingNeeds}
              </div>
              <div className="text-sm text-slate-400">匹配中</div>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-green-500/10">
              <Check className="h-6 w-6 text-green-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-green-400">
                {stats.acceptedCount}
              </div>
              <div className="text-sm text-slate-400">已采纳</div>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-violet-500/10">
              <History className="h-6 w-6 text-violet-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-violet-400">
                {stats.totalMatches}
              </div>
              <div className="text-sm text-slate-400">总匹配次数</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
