import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSearchParams } from "react-router-dom";

import DeliveryForm from "../DeliveryForm";
import { businessSupportApi } from "../../../services/api";

vi.mock("../../../services/api", () => ({
  businessSupportApi: {
    deliveryOrders: {
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
    },
    salesOrders: {
      list: vi.fn(),
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

describe("DeliveryForm", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
    businessSupportApi.salesOrders.list.mockResolvedValue({
      data: { code: 200, data: { items: [] } },
    });
  });

  it("blocks standalone creation when no upstream project context is present", () => {
    render(<DeliveryForm onBack={vi.fn()} />);

    expect(screen.getByText("请从项目交付页发起发货计划")).toBeInTheDocument();
    expect(businessSupportApi.salesOrders.list).not.toHaveBeenCalled();
  });

  it("loads project-scoped sales orders and preselects the project order", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("project_id=42&order_id=9"),
      vi.fn(),
    ]);
    businessSupportApi.salesOrders.list.mockResolvedValue({
      data: {
        code: 200,
        data: {
          items: [
            {
              id: 9,
              order_no: "SO-PJ-42",
              customer_name: "项目客户",
              project_id: 42,
              order_amount: "168000.00",
            },
          ],
        },
      },
    });

    render(<DeliveryForm onBack={vi.fn()} />);

    await waitFor(() => {
      expect(businessSupportApi.salesOrders.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
        project_id: "42",
      });
    });
    expect(screen.getByText("生成发货计划")).toBeInTheDocument();
    expect(screen.getByText("计划发货日期")).toBeInTheDocument();
  });

  it("shows the source sales order in edit mode without no-order warning", async () => {
    businessSupportApi.deliveryOrders.get.mockResolvedValue({
      data: {
        code: 200,
        data: {
          id: 7,
          order_id: 9,
          order_no: "SO-PJ-EDIT",
          customer_name: "项目客户",
          delivery_date: "2026-07-18",
          delivery_type: "freight",
          logistics_company: "QA Logistics",
          delivery_amount: "168000.00",
        },
      },
    });

    render(<DeliveryForm id="7" onBack={vi.fn()} />);

    expect(await screen.findByText("编辑发货计划")).toBeInTheDocument();
    expect(screen.getByDisplayValue("SO-PJ-EDIT")).toBeInTheDocument();
    expect(screen.queryByText("当前项目暂无可生成发货计划的销售订单")).not.toBeInTheDocument();
  });
});
