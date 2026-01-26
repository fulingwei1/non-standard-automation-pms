import React from "react";
import { PageHeader } from "../../components/layout";
import { MapPin } from "lucide-react";

export default function LocationManagement() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="库位管理" subtitle="仓库库位设置" icon={<MapPin className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">库位管理页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
