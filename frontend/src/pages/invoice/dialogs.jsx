// Invoice dialog components - placeholder
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui";

export function CreateInvoiceDialog({ open, onOpenChange }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>创建发票</DialogTitle>
        </DialogHeader>
        <div className="p-4">功能开发中...</div>
      </DialogContent>
    </Dialog>
  );
}

export function EditInvoiceDialog({ open, onOpenChange }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>编辑发票</DialogTitle>
        </DialogHeader>
        <div className="p-4">功能开发中...</div>
      </DialogContent>
    </Dialog>
  );
}

export function IssueInvoiceDialog({ open, onOpenChange }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>开具发票</DialogTitle>
        </DialogHeader>
        <div className="p-4">功能开发中...</div>
      </DialogContent>
    </Dialog>
  );
}

export function PaymentDialog({ open, onOpenChange }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>付款记录</DialogTitle>
        </DialogHeader>
        <div className="p-4">功能开发中...</div>
      </DialogContent>
    </Dialog>
  );
}

export function DeleteConfirmDialog({ open, onOpenChange }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>确认删除</DialogTitle>
        </DialogHeader>
        <div className="p-4">确定要删除吗？</div>
      </DialogContent>
    </Dialog>
  );
}
