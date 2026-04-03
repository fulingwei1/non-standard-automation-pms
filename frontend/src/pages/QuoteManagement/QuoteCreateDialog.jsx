/**
 * Quote Create Dialog
 * 创建报价对话框
 */

import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";

export default function QuoteCreateDialog({ open, onOpenChange }) {
  const navigate = useNavigate();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-slate-900 border-slate-700 text-white">
        <DialogHeader>
          <DialogTitle>新建报价</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <p className="text-slate-400">为保证字段完整性，请在独立页面创建报价。</p>
          <div className="flex justify-end gap-3 pt-4">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button
              onClick={() => {
                onOpenChange(false);
                navigate("/sales/quotes/create");
              }}>
              去创建页
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
