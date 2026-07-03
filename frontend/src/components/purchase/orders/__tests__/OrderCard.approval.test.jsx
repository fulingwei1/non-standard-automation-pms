import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import OrderCard from "../OrderCard";

vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, whileHover, ...props }) => <div {...props}>{children}</div>,
  },
}));

const submittedOrder = {
  id: 101,
  orderNo: "PO-TEST-101",
  supplierName: "测试供应商",
  projectId: 1,
  projectName: "测试项目",
  status: "submitted",
  urgency: "normal",
  buyer: "采购员",
  expectedDate: "2026-07-20",
  totalAmount: 1000,
  receivedCount: 0,
  itemCount: 1,
};

describe("OrderCard purchase order approval actions", () => {
  it("shows visible approve and reject actions for submitted orders", () => {
    // Regression: purchase orders could be submitted but had no visible approve/reject UI.
    // Found by real-browser procurement QA on 2026-07-01.
    // Report: .gstack/qa-reports/procurement-full-crud-sweep-20260701054459.json
    const onApprovalDecision = vi.fn();

    render(
      <OrderCard
        order={submittedOrder}
        onView={vi.fn()}
        onApprovalDecision={onApprovalDecision}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "审批通过" }));
    expect(onApprovalDecision).toHaveBeenCalledWith(submittedOrder, true);

    fireEvent.click(screen.getByRole("button", { name: "审批驳回" }));
    expect(onApprovalDecision).toHaveBeenCalledWith(submittedOrder, false);
  });
});
