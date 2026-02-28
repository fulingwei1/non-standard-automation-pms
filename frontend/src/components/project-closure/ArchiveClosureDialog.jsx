/**
 * 文档归档对话框
 */

import { useState, useEffect } from "react";



import { confirmAction } from "@/lib/confirmAction";
import { Button, Dialog, DialogBody, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui";
export default function ArchiveClosureDialog({ open, onOpenChange, onSubmit }) {
  const [pathsText, setPathsText] = useState("");

  useEffect(() => {
    if (open) {setPathsText("");}
  }, [open]);

  const parsePaths = (text) => {
    const raw = String(text || "")
      .split(/\n|,|;|，|；/)
      .map((s) => s.trim())
      .filter(Boolean);
    // 去重（保持顺序）
    const seen = new Set();
    const out = [];
    for (const p of raw) {
      if (seen.has(p)) {continue;}
      seen.add(p);
      out.push(p);
    }
    return out;
  };

  const handleSubmit = async () => {
    const ok = await confirmAction("确认将该结项记录归档？归档后将不可编辑。");
    if (!ok) {return;}
    onSubmit(parsePaths(pathsText));
  };

  const parsedPaths = parsePaths(pathsText);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>文档归档</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            <div className="text-sm text-slate-400">
              可选：填写归档文件路径列表（每行一个，或用逗号分隔）
            </div>
            <div>
              <label className="block text-sm font-medium text-white mb-2">
                归档路径
              </label>
              <textarea
                value={pathsText}
                onChange={(e) => setPathsText(e.target.value)}
                placeholder={"/archives/closure/xxx.pdf\n/uploads/xxx.docx"}
                className="w-full px-4 py-2 rounded-xl bg-white/[0.03] border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
                rows={6}
              />
            </div>

            {parsedPaths.length > 0 && (
              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <div className="text-sm text-slate-300 mb-2">
                  已解析 {parsedPaths.length} 条路径
                </div>
                <div className="max-h-32 overflow-y-auto pr-2">
                  <div className="space-y-1">
                    {(parsedPaths || []).map((p) => (
                      <div
                        key={p}
                        className="text-xs text-slate-400 font-mono break-all"
                      >
                        {p}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleSubmit}>确认归档</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
