import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  Button,
  Label,
  Input,
  Textarea
} from "../../ui";

const IssueInvoiceDialog = ({
  open,
  onOpenChange,
  issueData,
  setIssueData,
  onConfirm
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>开票</DialogTitle>
          <DialogDescription>确认开票信息</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>发票号码 *</Label>
            <Input
              value={issueData.invoice_no}
              onChange={(e) =>
                setIssueData({ ...issueData, invoice_no: e.target.value })
              }
              placeholder="请输入发票号码"
            />
          </div>
          <div>
            <Label>开票日期 *</Label>
            <Input
              type="date"
              value={issueData.issue_date}
              onChange={(e) =>
                setIssueData({ ...issueData, issue_date: e.target.value })
              }
            />
          </div>
          <div>
            <Label>备注</Label>
            <Textarea
              value={issueData.remark}
              onChange={(e) =>
                setIssueData({ ...issueData, remark: e.target.value })
              }
              placeholder="请输入备注"
              rows={3}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onConfirm}>确认开票</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default IssueInvoiceDialog;
