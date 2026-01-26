import React from "react";
import { PageHeader } from "../../components/layout";
import { Award } from "lucide-react";

export default function AcceptanceList() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="验收管理" subtitle="项目验收任务列表" icon={<Award className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">验收任务列表页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
