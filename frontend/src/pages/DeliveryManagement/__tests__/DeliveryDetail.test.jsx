import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DeliveryDetail from "../DeliveryDetail";
import { businessSupportApi } from "../../../services/api";

vi.mock("../../../services/api", () => ({
  businessSupportApi: {
    deliveryOrders: {
      get: vi.fn(),
      approve: vi.fn(),
      print: vi.fn(),
      ship: vi.fn(),
      receive: vi.fn(),
    },
  },
}));

vi.mock("../../../components/ui", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    toast: vi.fn(),
  };
});

const pendingDelivery = {
  id: 7,
  delivery_no: "DO-QA-001",
  order_id: 21,
  order_no: "SO-QA-001",
  customer_id: 3,
  customer_name: "QA客户",
  approval_status: "pending",
  delivery_status: "draft",
  delivery_amount: "12000.00",
};

describe("DeliveryDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    businessSupportApi.deliveryOrders.get.mockResolvedValue({
      data: { code: 200, data: pendingDelivery },
    });
  });

  it("shows approval actions and refreshes to printable state after approval", async () => {
    const user = userEvent.setup();
    businessSupportApi.deliveryOrders.approve.mockResolvedValue({
      data: {
        code: 200,
        data: {
          ...pendingDelivery,
          approval_status: "approved",
          delivery_status: "approved",
        },
      },
    });

    render(<DeliveryDetail id="7" onBack={vi.fn()} onEdit={vi.fn()} />);

    expect(await screen.findByRole("button", { name: /审批通过/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /审批驳回/ })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /审批通过/ }));

    await waitFor(() => {
      expect(businessSupportApi.deliveryOrders.approve).toHaveBeenCalledWith("7", {
        approved: true,
        approval_comment: "发货审批通过",
      });
    });
    expect(await screen.findByRole("button", { name: /打印送货单/ })).toBeInTheDocument();
    expect(screen.getByText("已通过")).toBeInTheDocument();
    expect(screen.getByText("已审批")).toBeInTheDocument();
  });
});
