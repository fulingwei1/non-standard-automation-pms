import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useSearchParams } from "react-router-dom";
import { useProductionPlanList } from "../useProductionPlanList";
import { productionApi, projectApi } from "../../../../services/api";

vi.mock("react-router-dom", () => ({
  useSearchParams: vi.fn(),
}));

vi.mock("../../../../services/api", () => ({
  productionApi: {
    productionPlans: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      publish: vi.fn(),
    },
    workshops: {
      list: vi.fn(),
    },
  },
  projectApi: {
    list: vi.fn(),
  },
}));

describe("useProductionPlanList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useSearchParams.mockReturnValue([new URLSearchParams(), vi.fn()]);
    projectApi.list.mockResolvedValue({ data: { items: [] } });
    productionApi.workshops.list.mockResolvedValue({ data: { items: [] } });
    productionApi.productionPlans.list.mockResolvedValue({ data: { items: [] } });
  });

  it("scopes production plans and defaults new plans by project context", async () => {
    useSearchParams.mockReturnValue([
      new URLSearchParams("project_id=42"),
      vi.fn(),
    ]);

    const { result } = renderHook(() => useProductionPlanList());

    await waitFor(() => {
      expect(productionApi.productionPlans.list).toHaveBeenCalledWith({
        project_id: "42",
      });
    });

    expect(result.current.filterProject).toBe("42");
    expect(result.current.newPlan.project_id).toBe(42);
  });
});
