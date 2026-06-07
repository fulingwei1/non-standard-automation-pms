import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import TechnicalParameterManagement from "../TechnicalParameterManagement";

const technicalParameterApiMock = vi.hoisted(() => ({
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  estimateCost: vi.fn(),
}));

vi.mock("../../services/api/technicalParameter", () => ({
  technicalParameterApi: technicalParameterApiMock,
}));

describe("TechnicalParameterManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    technicalParameterApiMock.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 1,
            name: "FCT 标准测试模板",
            code: "FCT-STD-001",
            industry: "CONSUMER",
            test_type: "FCT",
            description: "功能测试参数模板",
            parameters: {
              test_station_count: {
                label: "测试工位数",
                default: 4,
                unit: "个",
              },
            },
          },
        ],
        total: 1,
        page: 1,
      },
    });
  });

  it("renders templates returned by the backend paginated response", async () => {
    render(<TechnicalParameterManagement />);

    await waitFor(() => {
      expect(technicalParameterApiMock.list).toHaveBeenCalledWith({
        keyword: "",
        industry: "",
        test_type: "",
      });
    });

    expect(await screen.findByText("FCT 标准测试模板")).toBeInTheDocument();
    expect(screen.getByText("FCT-STD-001")).toBeInTheDocument();
    expect(screen.getByText("功能测试参数模板")).toBeInTheDocument();
    expect(screen.getByText("测试工位数: 4 个")).toBeInTheDocument();
  });

  it("loads template detail before running cost estimation from a list item", async () => {
    const user = userEvent.setup();
    technicalParameterApiMock.list.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 1,
            name: "FCT 标准测试模板",
            code: "FCT-STD-001",
            industry: "CONSUMER",
            test_type: "FCT",
            description: "功能测试参数模板",
          },
        ],
        total: 1,
        page: 1,
      },
    });
    technicalParameterApiMock.get.mockResolvedValueOnce({
      data: {
        id: 1,
        name: "FCT 标准测试模板",
        code: "FCT-STD-001",
        industry: "CONSUMER",
        test_type: "FCT",
        parameters: {
          test_station_count: {
            label: "测试工位数",
            default: 4,
            unit: "个",
          },
        },
      },
    });

    render(<TechnicalParameterManagement />);

    await screen.findByText("FCT 标准测试模板");
    await user.click(screen.getByTitle("成本估算"));

    await waitFor(() => {
      expect(technicalParameterApiMock.get).toHaveBeenCalledWith(1);
    });
    expect(await screen.findByLabelText("测试工位数 (个)")).toHaveValue(4);
  });

  it("renders backend cost breakdown and total labor hours after estimation", async () => {
    const user = userEvent.setup();
    technicalParameterApiMock.list.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 1,
            name: "FCT 标准测试模板",
            code: "FCT-STD-001",
            industry: "CONSUMER",
            test_type: "FCT",
          },
        ],
        total: 1,
        page: 1,
      },
    });
    technicalParameterApiMock.get.mockResolvedValueOnce({
      data: {
        id: 1,
        name: "FCT 标准测试模板",
        code: "FCT-STD-001",
        industry: "CONSUMER",
        test_type: "FCT",
        parameters: {
          test_station_count: {
            label: "测试工位数",
            default: 4,
            unit: "个",
          },
        },
      },
    });
    technicalParameterApiMock.estimateCost.mockResolvedValueOnce({
      data: {
        total_cost: 82000,
        cost_breakdown: {
          MECHANICAL: { ratio: 0.35, amount: 28700 },
          ELECTRICAL: { ratio: 0.3, amount: 24600 },
        },
        labor_hours: {
          detail: {
            design_hours: 80,
            assembly_hours: 120,
          },
          total: 200,
        },
      },
    });

    render(<TechnicalParameterManagement />);

    await screen.findByText("FCT 标准测试模板");
    await user.click(screen.getByTitle("成本估算"));
    await screen.findByLabelText("测试工位数 (个)");
    await user.click(screen.getByRole("button", { name: /计算成本/ }));

    expect(await screen.findByText("¥8.20万")).toBeInTheDocument();
    expect(screen.getByText("MECHANICAL")).toBeInTheDocument();
    expect(screen.getByText("¥2.87万")).toBeInTheDocument();
    expect(screen.getByText("ELECTRICAL")).toBeInTheDocument();
    expect(screen.getByText("预估 200 小时")).toBeInTheDocument();
  });

  it("loads template detail before editing a list item", async () => {
    const user = userEvent.setup();
    technicalParameterApiMock.list.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: 1,
            name: "FCT 标准测试模板",
            code: "FCT-STD-001",
            industry: "CONSUMER",
            test_type: "FCT",
            description: "功能测试参数模板",
          },
        ],
        total: 1,
        page: 1,
      },
    });
    technicalParameterApiMock.get.mockResolvedValueOnce({
      data: {
        id: 1,
        name: "FCT 标准测试模板",
        code: "FCT-STD-001",
        industry: "CONSUMER",
        test_type: "FCT",
        description: "功能测试参数模板",
        parameters: {
          test_station_count: {
            label: "测试工位数",
            default: 4,
            unit: "个",
          },
        },
        cost_factors: {},
        typical_labor_hours: {},
      },
    });

    render(<TechnicalParameterManagement />);

    await screen.findByText("FCT 标准测试模板");
    await user.click(screen.getByTitle("编辑"));

    await waitFor(() => {
      expect(technicalParameterApiMock.get).toHaveBeenCalledWith(1);
    });
    expect(await screen.findByDisplayValue(/测试工位数/)).toBeInTheDocument();
  });
});
