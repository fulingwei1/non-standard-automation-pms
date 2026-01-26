import React from "react";
import { PageHeader } from "../../components/layout";
import { ArrowDownToLine } from "lucide-react";

export default function InboundList() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="入库管理" subtitle="入库单据列表" icon={<ArrowDownToLine className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">入库单据列表页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
