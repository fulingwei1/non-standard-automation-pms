import React from "react";
import { PageHeader } from "../../components/layout";
import { XCircle } from "lucide-react";

export default function NCManagement() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="不合格品管理" subtitle="不合格品处理管理" icon={<XCircle className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">不合格品管理页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
