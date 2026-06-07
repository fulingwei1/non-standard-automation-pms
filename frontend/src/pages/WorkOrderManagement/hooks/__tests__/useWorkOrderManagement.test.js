import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSearchParams } from "react-router-dom";
import { useWorkOrders } from "../useWorkOrders";
import { productionApi, projectApi } from "../../../../services/api";

vi.mock("react-router-dom", () => ({
  useSearchParams: vi.fn(),
}));

vi.mock("../../../../services/api", () => ({
  productionApi: {
    workOrders: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      assign: vi.fn(),
    },
  },
  projectApi: {
    list: vi.fn(),
  },
}));

describe("useWorkOrders", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
    projectApi.list.mockResolvedValue({ data: { items: [] } });
    productionApi.workOrders.list.mockResolvedValue({ data: { items: [] } });
  });

  it("scopes work orders and defaults new work orders by project context", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("project_id=42"),
      vi.fn(),
    ]);

    const { result } = renderHook(() => useWorkOrders());

    await waitFor(() => {
      expect(productionApi.workOrders.list).toHaveBeenCalledWith({
        project_id: "42",
      });
    });

    expect(result.current.filterProject).toBe("42");
    expect(result.current.newOrder.project_id).toBe(42);
  });
});
