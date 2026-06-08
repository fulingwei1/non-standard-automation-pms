import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, useSearchParams } from "react-router-dom";
import TechnicalParameterManagement from "../TechnicalParameterManagement";

const technicalParameterApiMock = vi.hoisted(() => ({
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn(),
  estimateCost: vi.fn(),
}));

const presaleApiMock = vi.hoisted(() => ({
  solutions: {
    update: vi.fn(),
  },
}));

vi.mock("../../services/api/technicalParameter", () => ({
  technicalParameterApi: technicalParameterApiMock,
}));

vi.mock("../../services/api", () => ({
  presaleApi: presaleApiMock,
}));

function renderPage(initialEntry = "/presales/technical-solutions?tab=parameters") {
  const url = new URL(initialEntry, "http://localhost");
  useSearchParams.mockReturnValue([url.searchParams, vi.fn()]);

  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <TechnicalParameterManagement />
    </MemoryRouter>,
  );
}

describe("TechnicalParameterManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    presaleApiMock.solutions.update.mockResolvedValue({ data: { id: 88 } });
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
    renderPage();

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

  it("passes upstream opportunity ticket and project context when listing templates", async () => {
    renderPage(
      "/presales/technical-solutions?tab=parameters&type=support&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await waitFor(() => {
      expect(technicalParameterApiMock.list).toHaveBeenCalledWith({
        keyword: "",
        industry: "",
        test_type: "",
        opportunity_id: "2",
        ticket_id: "501",
        project_id: "42",
      });
    });
  });

  it("keeps lead context when listing templates from a lead-stage support flow", async () => {
    renderPage(
      "/presales/technical-solutions?tab=parameters&type=support&lead_id=2026&ticket_id=501",
    );

    await waitFor(() => {
      expect(technicalParameterApiMock.list).toHaveBeenCalledWith({
        keyword: "",
        industry: "",
        test_type: "",
        lead_id: "2026",
        ticket_id: "501",
      });
    });
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

    renderPage();

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

    renderPage();

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

  it("keeps upstream context when submitting a technical cost estimate", async () => {
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
        cost_breakdown: {},
        labor_hours: { detail: {}, total: 0 },
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=parameters&type=support&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await screen.findByText("FCT 标准测试模板");
    await user.click(screen.getByTitle("成本估算"));
    await screen.findByLabelText("测试工位数 (个)");
    await user.click(screen.getByRole("button", { name: /计算成本/ }));

    expect(technicalParameterApiMock.estimateCost).toHaveBeenCalledWith({
      template_id: 1,
      parameters: {
        test_station_count: 4,
      },
      opportunity_id: 2,
      ticket_id: 501,
      project_id: 42,
    });
  });

  it("keeps lead context when submitting a technical cost estimate", async () => {
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
        cost_breakdown: {},
        labor_hours: { detail: {}, total: 0 },
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=parameters&type=support&lead_id=2026&ticket_id=501",
    );

    await screen.findByText("FCT 标准测试模板");
    await user.click(screen.getByTitle("成本估算"));
    await screen.findByLabelText("测试工位数 (个)");
    await user.click(screen.getByRole("button", { name: /计算成本/ }));

    expect(technicalParameterApiMock.estimateCost).toHaveBeenCalledWith({
      template_id: 1,
      parameters: {
        test_station_count: 4,
      },
      lead_id: 2026,
      ticket_id: 501,
    });
  });

  it("writes a technical cost estimate back to the current solution", async () => {
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
        template_id: 1,
        total_cost: 82000,
        cost_breakdown: {
          MECHANICAL: { ratio: 0.35, amount: 28700 },
        },
        labor_hours: { detail: {}, total: 200 },
        parameters_used: {
          test_station_count: 4,
        },
      },
    });

    renderPage(
      "/presales/technical-solutions?tab=parameters&type=support&solution_id=88&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await screen.findByText("FCT 标准测试模板");
    await user.click(screen.getByTitle("成本估算"));
    await screen.findByLabelText("测试工位数 (个)");
    await user.click(screen.getByRole("button", { name: /计算成本/ }));
    await user.click(await screen.findByRole("button", { name: "写回当前方案" }));

    expect(presaleApiMock.solutions.update).toHaveBeenCalledWith(88, {
      template_id: 1,
      template_parameters: {
        test_station_count: 4,
      },
      estimated_cost: 82000,
      cost_breakdown: {
        MECHANICAL: { ratio: 0.35, amount: 28700 },
      },
      opportunity_id: 2,
      ticket_id: 501,
      project_id: 42,
      estimated_hours: 200,
    });
    expect(await screen.findByText("已写回当前方案")).toBeInTheDocument();
  });

  it("keeps upstream context when creating a technical parameter template", async () => {
    const user = userEvent.setup();
    technicalParameterApiMock.create.mockResolvedValueOnce({
      data: {
        id: 9,
        name: "EOL 项目测试模板",
        code: "EOL-PRJ-001",
      },
    });

    const { container } = renderPage(
      "/presales/technical-solutions?tab=parameters&type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42",
    );

    await screen.findByText("FCT 标准测试模板");
    await user.click(screen.getByRole("button", { name: "新增模板" }));

    const textInputs = container.querySelectorAll('input[type="text"]');
    await user.type(textInputs[1], "EOL 项目测试模板");
    await user.type(textInputs[2], "EOL-PRJ-001");

    const selects = screen.getAllByRole("combobox");
    await user.selectOptions(selects[2], "INDUSTRIAL");
    await user.selectOptions(selects[3], "EOL");

    await user.click(screen.getByRole("button", { name: "保存" }));

    expect(technicalParameterApiMock.create).toHaveBeenCalledWith({
      name: "EOL 项目测试模板",
      code: "EOL-PRJ-001",
      industry: "INDUSTRIAL",
      test_type: "EOL",
      description: "",
      parameters: {},
      cost_factors: {},
      typical_labor_hours: {},
      lead_id: 2026,
      opportunity_id: 2,
      ticket_id: 501,
      project_id: 42,
    });
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

    renderPage();

    await screen.findByText("FCT 标准测试模板");
    await user.click(screen.getByTitle("编辑"));

    await waitFor(() => {
      expect(technicalParameterApiMock.get).toHaveBeenCalledWith(1);
    });
    expect(await screen.findByDisplayValue(/测试工位数/)).toBeInTheDocument();
  });
});
