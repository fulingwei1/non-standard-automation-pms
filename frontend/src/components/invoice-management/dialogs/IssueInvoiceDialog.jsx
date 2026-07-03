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
  onIssueDataChange,
  onConfirm,
  onSubmit
}) => {
  const updateIssueData = onIssueDataChange || setIssueData;
  const handleSubmit = onConfirm || onSubmit;
  const updateField = (patch) => {
    updateIssueData?.({ ...issueData, ...patch });
  };

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
                updateField({ invoice_no: e.target.value })
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
                updateField({ issue_date: e.target.value })
              }
            />
          </div>
          <div>
            <Label>备注</Label>
            <Textarea
              value={issueData.remark}
              onChange={(e) =>
                updateField({ remark: e.target.value })
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
          <Button onClick={handleSubmit}>确认开票</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default IssueInvoiceDialog;
