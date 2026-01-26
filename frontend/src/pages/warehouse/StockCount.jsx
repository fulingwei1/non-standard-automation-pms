import React from "react";
import { PageHeader } from "../../components/layout";
import { ClipboardCheck } from "lucide-react";

export default function StockCount() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="盘点管理" subtitle="库存盘点任务" icon={<ClipboardCheck className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">盘点任务页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
