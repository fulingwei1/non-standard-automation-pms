import React from "react";
import { PageHeader } from "../../components/layout";
import { FileCheck } from "lucide-react";

export default function InspectionNew() {
  return (
    <div className="min-h-screen bg-surface-50">
      <PageHeader title="新建检验" subtitle="创建新的检验任务" icon={<FileCheck className="h-6 w-6" />} />
      <main className="container mx-auto px-4 py-6">
        <div className="bg-surface-200 rounded-xl border border-white/5 p-8 text-center">
          <p className="text-text-muted">新建检验任务页面 - 待实现</p>
        </div>
      </main>
    </div>
  );
}
