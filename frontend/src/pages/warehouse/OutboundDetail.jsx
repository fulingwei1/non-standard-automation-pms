import React from "react";
import { PageHeader } from "../../components/layout";
import { ArrowUpFromLine } from "lucide-react";

export default function OutboundDetail() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="出库单详情" subtitle="出库单详细信息" icon={<ArrowUpFromLine className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">出库单详情页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
