import React from "react";
import { RefreshCw } from "lucide-react";

export default function LoadingState() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
        <div className="text-slate-600">加载中...</div>
      </div>
    </div>
  );
}
