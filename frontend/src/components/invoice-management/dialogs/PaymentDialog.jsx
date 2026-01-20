import React from "react";
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
import { formatCurrency } from "../../../lib/utils";

const PaymentDialog = ({
  open,
  onOpenChange,
  paymentData,
  setPaymentData,
  selectedInvoice,
  onConfirm
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>记录收款</DialogTitle>
          <DialogDescription>
            发票: {selectedInvoice?.id}
            <br />
            待收金额:{" "}
            {formatCurrency(
              (selectedInvoice?.totalAmount || 0) -
                (selectedInvoice?.paidAmount || 0)
            )}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>收款金额 *</Label>
            <Input
              type="number"
              value={paymentData.paid_amount}
              onChange={(e) =>
                setPaymentData({
                  ...paymentData,
                  paid_amount: e.target.value
                })
              }
              placeholder="请输入收款金额"
            />
          </div>
          <div>
            <Label>收款日期 *</Label>
            <Input
              type="date"
              value={paymentData.paid_date}
              onChange={(e) =>
                setPaymentData({ ...paymentData, paid_date: e.target.value })
              }
            />
          </div>
          <div>
            <Label>备注</Label>
            <Textarea
              value={paymentData.remark}
              onChange={(e) =>
                setPaymentData({ ...paymentData, remark: e.target.value })
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
          <Button onClick={onConfirm}>确认收款</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default PaymentDialog;
