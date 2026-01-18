/**
 * 图纸查看对话框组件
 */

import { useState, useEffect } from "react";




import { cn } from "../../lib/utils";

export default function DrawingViewerDialog({ open, onClose, task }) {
  const [selectedDrawing, setSelectedDrawing] = useState(null);
  const [zoom, setZoom] = useState(100);

  useEffect(() => {
    if (task?.drawings?.length > 0 && !selectedDrawing) {
      setSelectedDrawing(task.drawings[0]);
    }
  }, [task, selectedDrawing]);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileImage className="w-5 h-5 text-blue-400" />
            装配图纸 - {task?.title}
          </DialogTitle>
        </DialogHeader>

        <div className="flex gap-4 h-[60vh]">
          {/* 图纸列表 */}
          <div className="w-48 flex-shrink-0 space-y-2 overflow-y-auto">
            <p className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-2">
              图纸清单
            </p>
            {task?.drawings?.map((drawing) => (
              <button
                key={drawing.id}
                onClick={() => setSelectedDrawing(drawing)}
                className={cn(
                  "w-full p-3 rounded-lg text-left transition-all",
                  selectedDrawing?.id === drawing.id
                    ? "bg-primary/20 border border-primary/50"
                    : "bg-surface-2 hover:bg-surface-3 border border-transparent"
                )}
              >
                <p className="text-sm font-medium text-white truncate">
                  {drawing.name}
                </p>
                <p className="text-xs text-slate-400 capitalize">
                  {drawing.type}
                </p>
              </button>
            ))}

            {(!task?.drawings || task.drawings.length === 0) && (
              <div className="text-center py-8 text-slate-500">
                <FileImage className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">暂无图纸</p>
              </div>
            )}
          </div>

          {/* 图纸预览区 */}
          <div className="flex-1 flex flex-col rounded-lg border border-border overflow-hidden">
            {/* 工具栏 */}
            <div className="flex items-center justify-between p-2 border-b border-border bg-surface-2/50">
              <span className="text-sm text-slate-400">
                {selectedDrawing?.name || "请选择图纸"}
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setZoom(Math.max(50, zoom - 25))}
                >
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <span className="text-xs text-slate-400 w-12 text-center">
                  {zoom}%
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setZoom(Math.min(200, zoom + 25))}
                >
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <RotateCw className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm">
                  <Download className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* 图纸内容 */}
            <div className="flex-1 overflow-auto bg-slate-900 flex items-center justify-center p-4">
              {selectedDrawing ? (
                <div
                  className="bg-white rounded shadow-lg"
                  style={{ transform: `scale(${zoom / 100})` }}
                >
                  {/* 模拟图纸预览 */}
                  <div className="w-[600px] h-[400px] flex items-center justify-center text-slate-600">
                    <div className="text-center">
                      <FileImage className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p className="font-medium">{selectedDrawing.name}</p>
                      <p className="text-sm text-slate-400 mt-1">
                        图纸文件: {selectedDrawing.url}
                      </p>
                      <p className="text-xs text-slate-400 mt-4">
                        (实际应用中将显示PDF/图片预览)
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center text-slate-500">
                  <FileImage className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>请从左侧选择要查看的图纸</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
