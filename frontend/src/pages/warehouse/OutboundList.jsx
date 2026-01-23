import React from "react";
import { PageHeader } from "../../components/layout";
import { ArrowUpFromLine } from "lucide-react";

export default function OutboundList() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="出库管理" subtitle="出库单据列表" icon={<ArrowUpFromLine className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">出库单据列表页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
