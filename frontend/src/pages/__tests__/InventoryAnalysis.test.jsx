import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import InventoryAnalysis from "../InventoryAnalysis";
import { api } from "../../services/api";
import { buildExportData, downloadCsv } from "../InventoryAnalysis/utils";

vi.mock("../../services/api", () => ({
  api: {
    get: vi.fn(),
  },
}));

vi.mock("../InventoryAnalysis/utils", () => ({
  buildExportData: vi.fn(() => [["库存分析报表"]]),
  downloadCsv: vi.fn(),
}));

vi.mock("../InventoryAnalysis/TurnoverRateTab", () => ({
  default: ({ turnoverData }) => (
    <div data-testid="turnover-rate-tab">
      周转率分析内容：{turnoverData?.summary?.turnover_rate ?? "empty"}
    </div>
  ),
}));

vi.mock("../InventoryAnalysis/StaleMaterialsTab", () => ({
  default: ({ staleMaterialsData, staleThreshold, setStaleThreshold, loading }) => (
    <div data-testid="stale-materials-tab">
      <div>呆滞物料内容：{staleMaterialsData?.summary?.stale_count ?? 0}</div>
      <div>当前阈值：{staleThreshold}</div>
      <div>{loading ? "加载中..." : "加载完成"}</div>
      <label htmlFor="stale-threshold">库龄阈值</label>
      <select
        id="stale-threshold"
        aria-label="库龄阈值"
        value={staleThreshold}
        onChange={(e) => setStaleThreshold(Number(e.target.value))}
      >
        <option value={30}>30天</option>
        <option value={60}>60天</option>
        <option value={90}>90天</option>
        <option value={120}>120天</option>
      </select>
    </div>
  ),
}));

vi.mock("../InventoryAnalysis/SafetyStockTab", () => ({
  default: ({ safetyStockData }) => (
    <div data-testid="safety-stock-tab">
      安全库存内容：{safetyStockData?.summary?.compliant_rate ?? "empty"}
    </div>
  ),
}));

vi.mock("../InventoryAnalysis/AbcAnalysisTab", () => ({
  default: ({ abcAnalysisData }) => (
    <div data-testid="abc-analysis-tab">
      ABC分类内容：{abcAnalysisData?.total_materials ?? "empty"}
    </div>
  ),
}));

vi.mock("../InventoryAnalysis/CostOccupancyTab", () => ({
  default: ({ costOccupancyData }) => (
    <div data-testid="cost-occupancy-tab">
      成本占用内容：{costOccupancyData?.summary?.total_inventory_value ?? "empty"}
    </div>
  ),
}));

const turnoverResponse = {
  summary: {
    total_inventory_value: 256000,
    turnover_rate: 3.5,
    turnover_days: 102,
    total_materials: 18,
  },
  category_breakdown: [
    {
      category_name: "电子料",
      inventory_value: 156000,
      material_count: 8,
      value_percentage: 61,
    },
  ],
};

const staleResponse = {
  summary: {
    stale_count: 2,
    stale_value: 56000,
    total_value_with_stock: 320000,
    threshold_days: 90,
  },
  stale_materials: [
    {
      material_code: "MAT-001",
      material_name: "伺服器",
    },
  ],
};

const safetyStockResponse = {
  summary: {
    compliant_rate: 88,
  },
};

const abcAnalysisResponse = {
  total_materials: 42,
};

const costOccupancyResponse = {
  summary: {
    total_inventory_value: 888000,
  },
};

describe("InventoryAnalysis", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    api.get.mockImplementation((url, config) => {
      if (url === "/inventory-analysis/turnover-rate") {
        return Promise.resolve({ data: { data: turnoverResponse } });
      }
      if (url === "/inventory-analysis/stale-materials") {
        return Promise.resolve({
          data: {
            data: {
              ...staleResponse,
              summary: {
                ...staleResponse.summary,
                threshold_days: config?.params?.threshold_days ?? 90,
              },
            },
          },
        });
      }
      if (url === "/inventory-analysis/safety-stock-compliance") {
        return Promise.resolve({ data: { data: safetyStockResponse } });
      }
      if (url === "/inventory-analysis/abc-analysis") {
        return Promise.resolve({ data: { data: abcAnalysisResponse } });
      }
      if (url === "/inventory-analysis/cost-occupancy") {
        return Promise.resolve({ data: { data: costOccupancyResponse } });
      }
      return Promise.reject(new Error(`unexpected url: ${url}`));
    });
  });

  function renderPage() {
    return render(
      <MemoryRouter>
        <InventoryAnalysis />
      </MemoryRouter>,
    );
  }

  it("默认加载周转率页并渲染页面编排", async () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "库存分析" })).toBeInTheDocument();
    expect(screen.getByText("库存周转率、呆滞物料、安全库存全面监控")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "导出报表" })).toBeInTheDocument();

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/inventory-analysis/turnover-rate");
    });

    expect(screen.getByTestId("turnover-rate-tab")).toHaveTextContent("周转率分析内容：3.5");
    expect(screen.queryByTestId("stale-materials-tab")).not.toBeInTheDocument();
  });

  it("切到呆滞物料页后按阈值加载，并在阈值变化时重新请求", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "呆滞物料" }));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/inventory-analysis/stale-materials", {
        params: { threshold_days: 90 },
      });
    });

    expect(screen.getByTestId("stale-materials-tab")).toHaveTextContent("当前阈值：90");

    fireEvent.change(screen.getByLabelText("库龄阈值"), {
      target: { value: "120" },
    });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/inventory-analysis/stale-materials", {
        params: { threshold_days: 120 },
      });
    });

    expect(screen.getByTestId("stale-materials-tab")).toHaveTextContent("当前阈值：120");
  });

  it("切换到其他标签时加载对应分析数据", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("button", { name: "安全库存" }));
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/inventory-analysis/safety-stock-compliance");
    });
    expect(screen.getByTestId("safety-stock-tab")).toHaveTextContent("安全库存内容：88");

    fireEvent.click(screen.getByRole("button", { name: "ABC分类" }));
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/inventory-analysis/abc-analysis");
    });
    expect(screen.getByTestId("abc-analysis-tab")).toHaveTextContent("ABC分类内容：42");

    fireEvent.click(screen.getByRole("button", { name: "成本占用" }));
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/inventory-analysis/cost-occupancy");
    });
    expect(screen.getByTestId("cost-occupancy-tab")).toHaveTextContent("成本占用内容：888000");
  });

  it("导出报表时按当前 tab 数据调用导出工具", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId("turnover-rate-tab")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "导出报表" }));

    expect(buildExportData).toHaveBeenCalledWith(
      "turnover-rate",
      expect.objectContaining({
        turnoverData: turnoverResponse,
        staleMaterialsData: null,
        safetyStockData: null,
        abcAnalysisData: null,
        costOccupancyData: null,
      }),
    );
    expect(downloadCsv).toHaveBeenCalledWith([["库存分析报表"]], "turnover-rate");
  });
});
