import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import PurchaseRequestDetail from "../PurchaseRequestDetail";
import { purchaseApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  purchaseApi: {
    requests: {
      get: vi.fn(),
      generateOrders: vi.fn(),
    },
  },
}));

vi.mock("../../components/ui/toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/lib/confirmAction", () => ({
  confirmAction: vi.fn(),
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const filtered = Object.fromEntries(
          Object.entries(props).filter(
            ([k]) =>
              ![
                "initial",
                "animate",
                "exit",
                "variants",
                "transition",
                "whileHover",
                "whileTap",
                "whileInView",
                "layout",
                "layoutId",
                "drag",
                "dragConstraints",
                "onDragEnd",
              ].includes(k),
          ),
        );
        const Tag = typeof tag === "string" ? tag : "div";
        return <Tag {...filtered}>{children}</Tag>;
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

const approvedRequest = {
  id: 1,
  request_no: "PR-001",
  status: "APPROVED",
  supplier_id: 9,
  total_amount: 1200,
  auto_po_created: false,
  items: [],
};

describe("PurchaseRequestDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    purchaseApi.requests.get.mockResolvedValue({
      data: { data: approvedRequest },
    });
    purchaseApi.requests.generateOrders.mockResolvedValue({
      data: { code: 200 },
    });
  });

  it("passes the request supplier id when generating purchase orders", async () => {
    render(
      <MemoryRouter initialEntries={["/purchase-requests/1"]}>
        <Routes>
          <Route path="/purchase-requests/:id" element={<PurchaseRequestDetail />} />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: /生成采购订单/ }));

    await waitFor(() => {
      expect(purchaseApi.requests.generateOrders).toHaveBeenCalledWith("1", {
        supplier_id: 9,
      });
    });
  });

  it("disables order generation when the approved request has no supplier", async () => {
    purchaseApi.requests.get.mockResolvedValueOnce({
      data: {
        data: {
          ...approvedRequest,
          supplier_id: null,
          supplier_name: null,
        },
      },
    });

    render(
      <MemoryRouter initialEntries={["/purchase-requests/1"]}>
        <Routes>
          <Route path="/purchase-requests/:id" element={<PurchaseRequestDetail />} />
        </Routes>
      </MemoryRouter>,
    );

    const button = await screen.findByRole("button", { name: /未指定供应商/ });
    expect(button).toBeDisabled();

    fireEvent.click(button);

    expect(purchaseApi.requests.generateOrders).not.toHaveBeenCalled();
  });
});
