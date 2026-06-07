import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PresalesCostEstimation from "../PresalesCostEstimation";
import { presaleApi } from "../../services/api";
import { toast } from "../../components/ui/toast";

const routeState = vi.hoisted(() => ({
  search: "tab=cost&type=support&opportunity_id=2&ticket_id=501&project_id=42",
}));
const navigateSpy = vi.hoisted(() => vi.fn());

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => navigateSpy,
    useSearchParams: () => [new URLSearchParams(routeState.search), vi.fn()],
  };
});

vi.mock("../../services/api", () => ({
  presaleApi: {
    solutions: {
      get: vi.fn(),
      list: vi.fn(),
      update: vi.fn(),
    },
  },
}));

vi.mock("../../components/ui/toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("../../components/presales/CostEstimateForm", () => ({
  default: ({ bidding, onSave, onCancel }) => (
    <div>
      <div>当前方案：{bidding.name}</div>
      <button
        type="button"
        onClick={() =>
          onSave({
            status: "draft",
            costData: {
              estimated_cost: 120000,
              suggested_price: 168000,
              cost_breakdown: {
                mechanical: 55000,
                electrical: 32000,
                software: 18000,
                standard: 12000,
                labor: 26000,
                other: 7000,
                notes: "含夹具、PLC、电控和调试人工",
              },
            },
          })
        }
      >
        保存成本
      </button>
      <button type="button" onClick={onCancel}>
        取消成本
      </button>
    </div>
  ),
}));

function renderPage(
  initialEntry = "/presales/technical-solutions?tab=cost&type=support&opportunity_id=2&ticket_id=501&project_id=42",
) {
  const url = new URL(initialEntry, "http://localhost");
  routeState.search = url.search.replace(/^\?/, "");

  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <PresalesCostEstimation embedded />
    </MemoryRouter>,
  );
}

describe("PresalesCostEstimation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    presaleApi.solutions.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 88,
            name: "ERP 改造售前技术方案",
            suggested_price: 1680000,
          },
        ],
        total: 1,
      },
    });
    presaleApi.solutions.get.mockResolvedValue({
      data: {
        id: 88,
        name: "ERP 改造售前技术方案",
        suggested_price: 1680000,
      },
    });
    presaleApi.solutions.update.mockResolvedValue({ data: { id: 88 } });
  });

  it("loads linked solution context from sales support and project ids", async () => {
    renderPage();

    await waitFor(() => {
      expect(presaleApi.solutions.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 1,
        opportunity_id: "2",
        ticket_id: "501",
        project_id: "42",
      });
    });
    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();
  });

  it("saves cost estimate back to the linked solution", async () => {
    renderPage();

    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "保存成本" }));

    await waitFor(() => {
      expect(presaleApi.solutions.update).toHaveBeenCalledWith(88, {
        estimated_cost: 120000,
        suggested_price: 168000,
        cost_breakdown: {
          mechanical: 55000,
          electrical: 32000,
          software: 18000,
          standard: 12000,
          labor: 26000,
          other: 7000,
          notes: "含夹具、PLC、电控和调试人工",
        },
      });
    });
    expect(toast.success).toHaveBeenCalledWith("成本估算草稿已保存");
  });

  it("loads linked solution by project context when opened from project presales entry", async () => {
    renderPage("/presales/technical-solutions?tab=cost&project_id=42");

    await waitFor(() => {
      expect(presaleApi.solutions.list).toHaveBeenCalledWith({
        page: 1,
        page_size: 1,
        project_id: "42",
      });
    });
    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();
  });

  it("loads the exact solution when opened with solution_id", async () => {
    renderPage(
      "/presales/technical-solutions?tab=cost&solution_id=88&ticket_id=501&opportunity_id=2&project_id=42",
    );

    await waitFor(() => {
      expect(presaleApi.solutions.get).toHaveBeenCalledWith(88);
    });
    expect(presaleApi.solutions.list).not.toHaveBeenCalled();
    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();
    expect(screen.getByText("当前预算参考：¥168万")).toBeInTheDocument();
  });

  it("keeps solution and project context when cancelling embedded estimation", async () => {
    renderPage(
      "/presales/technical-solutions?tab=cost&solution_id=88&ticket_id=501&opportunity_id=2&project_id=42",
    );

    expect(await screen.findByText("当前方案：ERP 改造售前技术方案")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "取消成本" }));

    expect(navigateSpy).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=cost&solution_id=88&ticket_id=501&opportunity_id=2&project_id=42",
    );
  });
});
