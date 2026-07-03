import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ProjectFormStepper, { normalizeProjectFormData } from "../ProjectFormStepper.jsx";
import { projectApi } from "../../../services/api";

vi.mock("framer-motion", () => ({
  motion: new Proxy({}, {
    get: (_, tag) => {
      const Tag = typeof tag === "string" ? tag : "div";
      return ({ children, ...props }) => <Tag {...props}>{children}</Tag>;
    },
  }),
  AnimatePresence: ({ children }) => children,
}));

vi.mock("../../../hooks/useAutoSave", () => ({
  useAutoSave: () => ({
    status: "idle",
    restore: vi.fn(),
    clear: vi.fn(),
    hasDraft: false,
  }),
}));

vi.mock("../../../services/api", () => ({
  projectApi: {
    list: vi.fn(),
    getStats: vi.fn(),
  },
  customerApi: {
    list: vi.fn(),
  },
  orgApi: {
    employees: vi.fn(),
  },
  stageViewsApi: {
    templates: {
      list: vi.fn(),
    },
  },
}));

vi.mock("../../ui/toast", () => ({
  toast: {
    error: vi.fn(),
    info: vi.fn(),
    success: vi.fn(),
  },
}));

describe("ProjectFormStepper", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const { customerApi, orgApi, stageViewsApi } = await import("../../../services/api");
    customerApi.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 107,
            customer_code: "PWB26-CUST-CATL",
            customer_name: "宁德时代演示客户",
          },
        ],
      },
    });
    orgApi.employees.mockResolvedValue({ data: { items: [] } });
    projectApi.getStats.mockResolvedValue({ data: { by_pm: [] } });
    stageViewsApi.templates.list.mockResolvedValue({ data: { items: [] } });
  });

  it("does not reject a new project code when keyword search returns non-exact matches", async () => {
    projectApi.list.mockResolvedValue({
      data: {
        items: [
          {
            id: 1,
            project_code: "DEMO26-PRJ-0001",
            project_name: "现有演示项目",
          },
        ],
      },
    });

    render(
      <ProjectFormStepper
        open
        onOpenChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    const projectCode = "PJ260630999";
    fireEvent.change(screen.getByPlaceholderText("例如: PJ260104001"), {
      target: { value: projectCode },
    });
    fireEvent.blur(screen.getByPlaceholderText("例如: PJ260104001"));
    fireEvent.change(screen.getByPlaceholderText("请输入项目全称"), {
      target: { value: "QA 项目创建验证" },
    });

    await waitFor(() => {
      expect(projectApi.list).toHaveBeenCalled();
    });

    fireEvent.click(screen.getByRole("button", { name: /下一步/ }));

    await waitFor(() => {
      expect(screen.getByPlaceholderText("搜索客户名称或编码")).toBeInTheDocument();
    });
    expect(screen.queryByText("项目编码已存在，请使用其他编码")).not.toBeInTheDocument();
  });

  it("normalizes empty optional fields before submitting to the project API", () => {
    expect(
      normalizeProjectFormData({
        project_code: "PJ260630999",
        project_name: "QA 项目创建验证",
        customer_id: "107",
        pm_id: "",
        template_id: "",
        stage_template_id: "1",
        contract_date: "",
        planned_start_date: "",
        planned_end_date: "",
        contract_amount: "123456.78",
        budget_amount: "",
      }),
    ).toMatchObject({
      customer_id: 107,
      pm_id: null,
      template_id: null,
      stage_template_id: 1,
      contract_date: null,
      planned_start_date: null,
      planned_end_date: null,
      contract_amount: 123456.78,
      budget_amount: 0,
    });
  });
});
