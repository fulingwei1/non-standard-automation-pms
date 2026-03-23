import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { productionApi, userApi } from "../../services/api";

const mockNavigate = vi.fn();

vi.mock("../../services/api", () => ({
  productionApi: {
    workshops: {
      list: vi.fn(),
      get: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      getWorkstations: vi.fn(),
      addWorkstation: vi.fn(),
    },
  },
  userApi: {
    list: vi.fn(),
  },
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("WorkshopManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    userApi.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [{ id: 7, name: "张主管" }],
        },
      },
    });

    productionApi.workshops.list.mockResolvedValue({
      data: {
        success: true,
        data: {
          items: [
            {
              id: 1,
              workshop_code: "WS-001",
              workshop_name: "装配车间A",
              workshop_type: "ASSEMBLY",
              manager_name: "张主管",
              worker_count: 25,
              workstation_count: 10,
              capacity_hours: 1000,
              utilization_rate: 85,
              is_active: true,
            },
          ],
        },
      },
    });
  });

  it("renders and loads wrapped workshop data without crashing", async () => {
    render(
      <MemoryRouter>
        <WorkshopManagement />
      </MemoryRouter>,
    );

    expect(screen.getByPlaceholderText("搜索车间编码、名称...")).toHaveValue("");

    await waitFor(() => {
      expect(userApi.list).toHaveBeenCalledWith({ page_size: 1000 });
      expect(productionApi.workshops.list).toHaveBeenCalled();
    });

    expect(screen.getByText("车间管理")).toBeInTheDocument();
    expect(screen.getByText("WS-001")).toBeInTheDocument();
    expect(screen.getByText("装配车间A")).toBeInTheDocument();
  });
});
