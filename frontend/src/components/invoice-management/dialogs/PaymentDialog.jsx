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
  onPaymentDataChange,
  selectedInvoice,
  invoiceLabel,
  pendingAmount,
  amountStep,
  amountMin,
  amountMax,
  amountPlaceholder,
  dateMax,
  showPaymentMethod = false,
  showBankAccount = false,
  formatAmount,
  onConfirm,
  onSubmit,
  children
}) => {
  const updatePaymentData = onPaymentDataChange || setPaymentData;
  const pendingValue =
    pendingAmount !== undefined && pendingAmount !== null
      ? pendingAmount
      : (selectedInvoice?.totalAmount || 0) - (selectedInvoice?.paidAmount || 0);
  const displayInvoice = invoiceLabel ?? selectedInvoice?.id ?? "-";
  const formatValue = formatAmount || formatCurrency;
  const handleConfirm = onConfirm || onSubmit;

  const updateField = (patch) => {
    if (!updatePaymentData) {return;}
    updatePaymentData({ ...paymentData, ...patch });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>记录收款</DialogTitle>
          <DialogDescription>
            发票: {displayInvoice}
            <br />
            待收金额:{" "}
            {formatValue(Number(pendingValue || 0))}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>收款金额 *</Label>
            <Input
              type="number"
              step={amountStep}
              min={amountMin}
              max={amountMax}
              value={paymentData?.paid_amount ?? ""}
              onChange={(e) =>
                updateField({ paid_amount: e.target.value })
              }
              placeholder={amountPlaceholder || "请输入收款金额"}
            />
          </div>
          <div>
            <Label>收款日期 *</Label>
            <Input
              type="date"
              value={paymentData?.paid_date ?? ""}
              onChange={(e) =>
                updateField({ paid_date: e.target.value })
              }
              max={dateMax}
            />
          </div>
          {showPaymentMethod && (
            <div>
              <Label>收款方式</Label>
              <Input
                value={paymentData?.payment_method ?? ""}
                onChange={(e) =>
                  updateField({ payment_method: e.target.value })
                }
                placeholder="如：银行转账、现金等"
              />
            </div>
          )}
          {showBankAccount && (
            <div>
              <Label>收款账户</Label>
              <Input
                value={paymentData?.bank_account ?? ""}
                onChange={(e) =>
                  updateField({ bank_account: e.target.value })
                }
                placeholder="收款银行账户"
              />
            </div>
          )}
          <div>
            <Label>备注</Label>
            <Textarea
              value={paymentData?.remark ?? ""}
              onChange={(e) =>
                updateField({ remark: e.target.value })
              }
              placeholder="请输入备注"
              rows={3}
            />
          </div>
          {children}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={() => handleConfirm?.()}>确认收款</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default PaymentDialog;
