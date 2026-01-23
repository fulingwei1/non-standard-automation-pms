import React from "react";
import { PageHeader } from "../../components/layout";
import { ArrowDownToLine } from "lucide-react";

export default function InboundDetail() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="入库单详情" subtitle="入库单详细信息" icon={<ArrowDownToLine className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">入库单详情页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
