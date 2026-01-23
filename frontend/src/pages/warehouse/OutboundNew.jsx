import React from "react";
import { PageHeader } from "../../components/layout";
import { ArrowUpFromLine } from "lucide-react";

export default function OutboundNew() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="新建出库单" subtitle="创建新的出库单" icon={<ArrowUpFromLine className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">新建出库单页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
