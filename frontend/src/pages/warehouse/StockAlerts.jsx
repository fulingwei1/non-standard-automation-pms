import React from "react";
import { PageHeader } from "../../components/layout";
import { AlertTriangle } from "lucide-react";

export default function StockAlerts() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="库存预警" subtitle="库存预警管理" icon={<AlertTriangle className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">库存预警页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
