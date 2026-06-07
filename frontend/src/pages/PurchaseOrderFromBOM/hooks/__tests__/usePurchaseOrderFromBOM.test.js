import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSearchParams } from "react-router-dom";
import { bomApi, purchaseApi, supplierApi } from "../../../../services/api";
import { usePurchaseOrderFromBOM } from "../usePurchaseOrderFromBOM";

vi.mock("react-router-dom", () => ({
  useSearchParams: vi.fn(),
}));

vi.mock("../../../../components/ui/toast", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

vi.mock("../../../../services/api", () => ({
  bomApi: {
    list: vi.fn(),
  },
  purchaseApi: {
    orders: {
      createFromBOM: vi.fn(),
    },
  },
  supplierApi: {
    list: vi.fn(),
  },
}));

describe("usePurchaseOrderFromBOM", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSearchParams.mockReturnValue([new URLSearchParams("project_id=42"), vi.fn()]);
    bomApi.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 88,
            bom_no: "BOM-42",
            project_id: 42,
            project_name: "合同转项目",
          },
        ],
      },
    });
    supplierApi.list.mockResolvedValue({
      data: {
        items: [{ id: 7, supplier_name: "默认供应商" }],
      },
    });
    purchaseApi.orders.createFromBOM.mockResolvedValue({
      data: {
        data: {
          bom_id: 88,
          preview: [{ supplier_id: 7, items: [] }],
          created_orders: [{ id: 901 }],
        },
      },
    });
  });

  it("loads released BOMs within the upstream project context and preselects the only match", async () => {
    const { result } = renderHook(() => usePurchaseOrderFromBOM());

    await waitFor(() => {
      expect(bomApi.list).toHaveBeenCalledWith({
        status: "RELEASED",
        page_size: 1000,
        project_id: "42",
      });
    });
    await waitFor(() => {
      expect(result.current.selectedBomId).toBe("88");
    });
  });

  it("keeps project context when generating preview and creating purchase orders", async () => {
    const { result } = renderHook(() => usePurchaseOrderFromBOM());

    await waitFor(() => {
      expect(result.current.selectedBomId).toBe("88");
    });

    await act(async () => {
      await result.current.handleGeneratePreview();
    });

    expect(purchaseApi.orders.createFromBOM).toHaveBeenCalledWith({
      bom_id: 88,
      create_orders: false,
      project_id: "42",
    });

    await act(async () => {
      await result.current.handleCreateOrders();
    });

    expect(purchaseApi.orders.createFromBOM).toHaveBeenLastCalledWith({
      bom_id: 88,
      create_orders: true,
      project_id: "42",
    });
  });
});
