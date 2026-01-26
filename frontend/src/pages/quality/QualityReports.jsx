import React from "react";
import { PageHeader } from "../../components/layout";
import { TrendingUp } from "lucide-react";

export default function QualityReports() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="质量报表" subtitle="质量统计分析报表" icon={<TrendingUp className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">质量报表页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
