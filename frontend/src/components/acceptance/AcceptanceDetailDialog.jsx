/**
 * 验收详情对话框
 */

import { useState } from "react";
import {
  FileText
} from "lucide-react";


import { cn } from "../../lib/utils";
import { typeConfigs, statusConfigs, severityConfigs } from "./acceptanceConfig";
import { Badge, Button, Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui";
import { Camera } from "lucide-react";

export default function AcceptanceDetailDialog({ acceptance, open, onOpenChange }) {
  const [activeTab, setActiveTab] = useState("checklist");

  if (!acceptance) {return null;}

  const type = typeConfigs[acceptance.type] || {
    label: acceptance.type || "未知",
    color: "text-slate-400",
    bgColor: "bg-slate-500/10",
  };
  const status = statusConfigs[acceptance.status] || {
    label: acceptance.status || "未知",
    color: "bg-slate-500",
    icon: FileText,
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <Badge className={cn(type.bgColor, type.color)}>{type.label}</Badge>
            {acceptance.projectName} - {acceptance.machineNo}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Basic Info */}
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <label className="text-xs text-slate-500">验收单号</label>
              <p className="text-white font-mono">{acceptance.id}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">项目编号</label>
              <p className="text-accent">{acceptance.projectId}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">客户</label>
              <p className="text-white">{acceptance.customer}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">计划日期</label>
              <p className="text-white">{acceptance.scheduledDate}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">检验员</label>
              <p className="text-white">{acceptance.inspector || "-"}</p>
            </div>
            <div>
              <label className="text-xs text-slate-500">状态</label>
              <Badge className={cn("mt-1", status.color)}>{status.label}</Badge>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b border-border">
            {[
              { id: "checklist", label: "检查清单" },
              { id: "issues", label: `问题记录 (${acceptance.issues?.length || 0})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
                  activeTab === tab.id
                    ? "text-accent border-accent"
                    : "text-slate-400 border-transparent hover:text-white",
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Checklist Tab */}
          {activeTab === "checklist" && (
            <div className="space-y-3">
              {acceptance.checklistCategories?.length > 0 ? (
                acceptance.checklistCategories.map((category, index) => (
                  <div key={index} className="p-3 rounded-lg bg-surface-2">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-white">
                        {category.name}
                      </span>
                      <span className="text-sm text-slate-400">
                        {category.passed}/{category.total}
                      </span>
                    </div>
                    <div className="h-1.5 bg-surface-0 rounded-full overflow-hidden flex">
                      <div
                        className="bg-emerald-500"
                        style={{
                          width: `${(category.passed / category.total) * 100}%`,
                        }}
                      />
                      <div
                        className="bg-red-500"
                        style={{
                          width: `${(category.failed / category.total) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500">
                  暂无检查记录
                </div>
              )}
            </div>
          )}

          {/* Issues Tab */}
          {activeTab === "issues" && (
            <div className="space-y-3">
              {acceptance.issues?.length > 0 ? (
                acceptance.issues.map((issue) => (
                  <div
                    key={issue.id}
                    className={cn(
                      "p-4 rounded-lg border",
                      issue.status === "open"
                        ? "bg-amber-500/5 border-amber-500/30"
                        : "bg-surface-2 border-border/50",
                    )}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white">
                            {issue.item}
                          </span>
                          <Badge
                            className={cn(
                              "text-[10px] border",
                              (
                                severityConfigs[issue.severity] || {
                                  color:
                                    "bg-slate-500/20 text-slate-400 border-slate-500/30",
                                }
                              ).color,
                            )}
                          >
                            {
                              (
                                severityConfigs[issue.severity] || {
                                  label: issue.severity || "未知",
                                }
                              ).label
                            }
                          </Badge>
                        </div>
                        <span className="text-xs text-slate-500">
                          {issue.category}
                        </span>
                      </div>
                      <Badge
                        className={cn(
                          issue.status === "open"
                            ? "bg-amber-500"
                            : "bg-emerald-500",
                        )}
                      >
                        {issue.status === "open" ? "待解决" : "已解决"}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-300">
                      {issue.description}
                    </p>
                    {issue.photos?.length > 0 && (
                      <div className="flex gap-2 mt-2">
                        {issue.photos.map((photo, i) => (
                          <div
                            key={i}
                            className="w-16 h-16 rounded bg-surface-0 flex items-center justify-center"
                          >
                            <Image className="w-6 h-6 text-slate-600" />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-500">
                  暂无问题记录
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {acceptance.status === "in_progress" && (
            <>
              <Button variant="outline">
                <Camera className="w-4 h-4 mr-1" />
                记录问题
              </Button>
              <Button>
                <FileText className="w-4 h-4 mr-1" />
                生成报告
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
