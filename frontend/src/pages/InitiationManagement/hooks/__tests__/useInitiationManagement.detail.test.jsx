import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { useInitiationManagement } from "../useInitiationManagement";
import { pmoApi } from "../../../../services/api";

vi.mock("../../../../services/api", () => ({
  pmoApi: {
    initiations: {
      list: vi.fn(),
      get: vi.fn(),
    },
  },
}));

describe("useInitiationManagement detail mode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads a single initiation detail when an initiation id is provided", async () => {
    const detail = {
      id: 18,
      project_name: "FCT 测试线立项",
      presale_handover_context: {
        presale_solution: { name: "PMO售前交接方案" },
      },
    };
    pmoApi.initiations.get.mockResolvedValue({ data: detail });
    pmoApi.initiations.list.mockResolvedValue({ data: { items: [], total: 0 } });

    const { result } = renderHook(() => useInitiationManagement("18"));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(pmoApi.initiations.get).toHaveBeenCalledWith("18");
    expect(pmoApi.initiations.list).not.toHaveBeenCalled();
    expect(result.current.initiations).toEqual([detail]);
    expect(result.current.total).toBe(1);
  });
});
