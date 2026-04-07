/**
 * Quote Edit Dialog
 * 编辑报价对话框
 */

import { useNavigate } from "react-router-dom";

export default function QuoteEditDialog({ open, onOpenChange, selectedQuote }) {
  const navigate = useNavigate();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 text-white">
        <DialogHeader>
          <DialogTitle>编辑报价</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-slate-400">编辑请跳转到报价编辑页，避免字段丢失。</p>
          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button
              onClick={() => {
                onOpenChange(false);
                if (selectedQuote?.id) {
                  navigate(`/sales/quotes/${selectedQuote.id}/edit`);
                }
              }}>
              去编辑页
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
