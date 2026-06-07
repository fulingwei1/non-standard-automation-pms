import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import MaterialDemandSummary from "../MaterialDemandSummary";
import OutsourcingOrderList from "../OutsourcingOrderList";
import { materialDemandApi, outsourcingApi, projectApi } from "../../services/api";

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useSearchParams: () => [new URLSearchParams("project_id=42"), vi.fn()],
  };
});

vi.mock("../../services/api", () => ({
  materialDemandApi: {
    list: vi.fn(),
    getVsStock: vi.fn(),
    generatePR: vi.fn(),
  },
  outsourcingApi: {
    orders: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
    },
  },
  projectApi: {
    list: vi.fn(),
  },
}));

function renderWithRouter(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("Downstream specialty project context", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(window, "alert").mockImplementation(() => {});
    projectApi.list.mockResolvedValue({ data: { items: [] } });
    materialDemandApi.list.mockResolvedValue({ data: { items: [] } });
    materialDemandApi.generatePR.mockResolvedValue({ data: { id: 1 } });
    outsourcingApi.orders.list.mockResolvedValue({ data: { items: [] } });
  });

  it("passes project context to material demand loading and purchase request generation", async () => {
    renderWithRouter(<MaterialDemandSummary />);

    await waitFor(() => {
      expect(materialDemandApi.list).toHaveBeenCalledWith({
        project_id: "42",
      });
    });

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page_size: 1000,
        project_id: "42",
      });
    });

    fireEvent.click(screen.getByRole("button", { name: /生成采购需求/ }));
    fireEvent.click(screen.getByRole("button", { name: /^生成$/ }));

    await waitFor(() => {
      expect(materialDemandApi.generatePR).toHaveBeenCalledWith({
        project_ids: "42",
      });
    });
  });

  it("passes project context to outsourcing order loading and project candidates", async () => {
    renderWithRouter(<OutsourcingOrderList />);

    await waitFor(() => {
      expect(outsourcingApi.orders.list).toHaveBeenCalledWith({
        project_id: "42",
      });
    });

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalledWith({
        page_size: 1000,
        project_id: "42",
      });
    });
  });
});
