import React, { useState } from "react";
import { FileWarning, Camera, X, Send } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
} from "../../ui";
import { cn } from "../../../lib/utils";

export default function QualityFeedbackDialog({ open, onClose, task: _task, material }) {
  const [issueType, setIssueType] = useState("dimension");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState("minor");
  const [photos, _setPhotos] = useState([]);

  const issueTypes = [
    { value: "dimension", label: "尺寸偏差" },
    { value: "surface", label: "表面缺陷" },
    { value: "function", label: "功能异常" },
    { value: "damage", label: "运输损坏" },
    { value: "mismatch", label: "型号不符" },
    { value: "other", label: "其他问题" },
  ];

  const handleSubmit = () => {
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileWarning className="w-5 h-5 text-red-400" />
            质量问题反馈
          </DialogTitle>
          <DialogDescription>
            反馈零部件质量问题，系统将通知质检和供应商
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {material && (
            <div className="p-3 rounded-lg bg-surface-2/50 text-sm">
              <p className="font-medium text-white">{material.name}</p>
              <p className="text-slate-400">规格：{material.spec}</p>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">问题类型</label>
            <div className="grid grid-cols-3 gap-2">
              {issueTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setIssueType(type.value)}
                  className={cn(
                    "py-2 px-3 rounded-lg text-xs font-medium transition-all",
                    issueType === type.value
                      ? "bg-primary text-white"
                      : "bg-surface-2 text-slate-400 hover:bg-surface-3"
                  )}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">严重程度</label>
            <div className="flex gap-2">
              {[
                {
                  value: "minor",
                  label: "轻微",
                  desc: "可继续使用",
                  color: "bg-yellow-500",
                },
                {
                  value: "major",
                  label: "严重",
                  desc: "影响使用",
                  color: "bg-orange-500",
                },
                {
                  value: "critical",
                  label: "致命",
                  desc: "无法使用",
                  color: "bg-red-500",
                },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setSeverity(opt.value)}
                  className={cn(
                    "flex-1 py-2 px-2 rounded-lg transition-all text-center",
                    severity === opt.value
                      ? `${opt.color} text-white`
                      : "bg-surface-2 text-slate-400 hover:bg-surface-3"
                  )}
                >
                  <div className="text-sm font-medium">{opt.label}</div>
                  <div className="text-[10px] opacity-80">{opt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">问题描述</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="请详细描述质量问题..."
              className={cn(
                "w-full h-24 px-3 py-2 rounded-lg resize-none",
                "bg-surface-2 border border-border",
                "text-white placeholder:text-slate-500",
                "focus:outline-none focus:ring-2 focus:ring-primary/50"
              )}
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-white">拍照取证</label>
            <div className="flex gap-2">
              <button
                className={cn(
                  "w-20 h-20 rounded-lg border-2 border-dashed border-border",
                  "flex flex-col items-center justify-center gap-1",
                  "text-slate-400 hover:text-white hover:border-primary/50",
                  "transition-all"
                )}
              >
                <Camera className="w-6 h-6" />
                <span className="text-[10px]">拍照</span>
              </button>
              {photos.map((photo, i) => (
                <div
                  key={i}
                  className="relative w-20 h-20 rounded-lg overflow-hidden"
                >
                  <img
                    src={photo}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                  <button className="absolute top-1 right-1 p-0.5 rounded-full bg-black/50">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            取消
          </Button>
          <Button
            onClick={handleSubmit}
            className="bg-red-500 hover:bg-red-600"
          >
            <Send className="w-4 h-4 mr-1" />
            提交反馈
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
