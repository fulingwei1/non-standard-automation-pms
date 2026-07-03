import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import QualificationManagement from "../QualificationManagement";
import { qualificationApi } from "../../services/api";
import { toast } from "../../components/ui/toast";
import { confirmAction } from "@/lib/confirmAction";

vi.mock("../../services/api", () => ({
  qualificationApi: {
    getLevels: vi.fn(),
    deleteLevel: vi.fn(),
    getModels: vi.fn(),
    getEmployeeQualifications: vi.fn(),
  },
}));

vi.mock("../../components/ui/toast", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock("@/lib/confirmAction", () => ({
  confirmAction: vi.fn(),
}));

vi.mock("../../components/qualification/CompetencyRadarChart", () => ({
  CompetencyRadarChart: ({ data }) => (
    <div data-testid="competency-radar-chart">
      雷达图:{Object.keys(data || {}).join(",")}
    </div>
  ),
}));

vi.mock("framer-motion", () => ({
  motion: new Proxy(
    {},
    {
      get: (_, tag) => ({ children, ...props }) => {
        const filtered = Object.fromEntries(
          Object.entries(props).filter(
            ([k]) =>
              ![
                "initial",
                "animate",
                "exit",
                "variants",
                "transition",
                "whileHover",
                "whileTap",
                "whileInView",
                "layout",
                "layoutId",
                "drag",
                "dragConstraints",
                "onDragEnd",
              ].includes(k),
          ),
        );
        const Tag = typeof tag === "string" ? tag : "div";
        return <Tag {...filtered}>{children}</Tag>;
      },
    },
  ),
  AnimatePresence: ({ children }) => children,
}));

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const levelsResponse = {
  data: {
    code: 200,
    data: {
      items: [
        {
          id: 1,
          level_code: "JUNIOR",
          level_name: "初级",
          level_order: 1,
          role_type: "ENGINEER",
          is_active: true,
        },
      ],
      total: 3,
    },
  },
};

const modelsResponse = {
  data: {
    code: 200,
    data: {
      items: [
        {
          id: 11,
          position_type: "ENGINEER",
          position_subtype: "电气",
          level: { level_name: "高级" },
          level_id: 3,
          is_active: true,
          created_at: "2026-01-05T00:00:00.000Z",
        },
      ],
      total: 12,
    },
  },
};

const employeeResponse = {
  data: {
    code: 200,
    data: {
      items: [
        {
          id: 21,
          employee_id: 1001,
          position_type: "ENGINEER",
          level: {
            level_code: "SENIOR",
            level_name: "高级",
          },
          certified_date: "2026-02-01T00:00:00.000Z",
          status: "APPROVED",
          assessment_details: {
            technical_skills: 88,
            business_skills: 80,
          },
        },
        {
          id: 22,
          employee_id: 1002,
          position_type: "SALES",
          level: {
            level_code: "JUNIOR",
            level_name: "初级",
          },
          certified_date: "2026-02-15T00:00:00.000Z",
          status: "PENDING",
          assessment_details: {
            technical_skills: 70,
            business_skills: 90,
          },
        },
      ],
      total: 21,
    },
  },
};

describe("QualificationManagement", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    confirmAction.mockResolvedValue(true);
    qualificationApi.deleteLevel.mockResolvedValue({ data: { code: 200 } });

    qualificationApi.getLevels.mockImplementation((params) => {
      if (params?.page_size === 1) {
        return Promise.resolve({
          data: { code: 200, data: { total: 3, items: [] } },
        });
      }
      return Promise.resolve(levelsResponse);
    });

    qualificationApi.getModels.mockImplementation((params) => {
      if (params?.page_size === 1) {
        return Promise.resolve({
          data: { code: 200, data: { total: 12, items: [] } },
        });
      }
      return Promise.resolve(modelsResponse);
    });

    qualificationApi.getEmployeeQualifications.mockImplementation((params) => {
      if (params?.page_size === 1 && params?.status === "PENDING") {
        return Promise.resolve({
          data: { code: 200, data: { total: 5, items: [] } },
        });
      }
      return Promise.resolve(employeeResponse);
    });
  });

  function renderPage() {
    return render(
      <MemoryRouter>
        <QualificationManagement />
      </MemoryRouter>,
    );
  }

  it("默认加载等级页并渲染统计卡片", async () => {
    renderPage();

    expect(screen.getAllByText("任职资格管理").length).toBeGreaterThan(0);
    expect(screen.getByText("管理任职资格等级、能力模型和员工认证")).toBeInTheDocument();

    await waitFor(() => {
      expect(qualificationApi.getLevels).toHaveBeenCalledWith({
        page: 1,
        page_size: 100,
        role_type: "",
        is_active: true,
      });
    });

    expect(screen.getByText("等级总数")).toBeInTheDocument();
    expect(screen.getAllByText("能力模型").length).toBeGreaterThan(0);
    expect(screen.getByText("已认证员工")).toBeInTheDocument();
    expect(screen.getByText("待认证")).toBeInTheDocument();
    expect(screen.getByText("初级")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "新建等级" }).length).toBeGreaterThan(0);

    await waitFor(() => {
      expect(qualificationApi.getLevels).toHaveBeenCalledWith({ page: 1, page_size: 1 });
      expect(qualificationApi.getModels).toHaveBeenCalledWith({ page: 1, page_size: 1 });
      expect(qualificationApi.getEmployeeQualifications).toHaveBeenCalledWith({
        page: 1,
        page_size: 1,
        status: "PENDING",
      });
    });
  });

  it("切到能力模型页后加载模型列表并支持新建入口", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("tab", { name: "能力模型" }));

    await waitFor(() => {
      expect(qualificationApi.getModels).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
      });
    });

    expect(screen.getByText("ENGINEER")).toBeInTheDocument();
    expect(screen.getByText("电气")).toBeInTheDocument();
    const createButtons = screen.getAllByRole("button", { name: "新建能力模型" });
    expect(createButtons.length).toBeGreaterThan(0);

    fireEvent.click(createButtons[0]);
    expect(mockNavigate).toHaveBeenCalledWith("/qualifications/models/new");
  });

  it("切到员工认证页后加载员工列表、图表和分页", async () => {
    renderPage();

    fireEvent.click(screen.getByRole("tab", { name: "员工认证" }));

    await waitFor(() => {
      expect(qualificationApi.getEmployeeQualifications).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
      });
    });

    expect(screen.getByText("员工 #1001")).toBeInTheDocument();
    expect(screen.getByText("员工 #1002")).toBeInTheDocument();
    expect(screen.getByText("平均能力维度")).toBeInTheDocument();
    expect(screen.getByText("等级分布统计")).toBeInTheDocument();
    expect(screen.getByText("岗位类型分布")).toBeInTheDocument();
    expect(screen.getByTestId("competency-radar-chart")).toHaveTextContent(
      "雷达图:technical_skills,business_skills",
    );
    expect(screen.getByText(/共 21 条记录，第 1 \/ 3 页/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "认证员工" })).toBeInTheDocument();
  });

  it("删除等级成功时会确认、调用接口并提示成功", async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("初级")).toBeInTheDocument();
    });

    const actionButtons = screen.getAllByRole("button");
    fireEvent.click(actionButtons[actionButtons.length - 1]);

    await waitFor(() => {
      expect(confirmAction).toHaveBeenCalledWith("确定要删除该等级吗？");
      expect(qualificationApi.deleteLevel).toHaveBeenCalledWith(1);
      expect(toast.success).toHaveBeenCalledWith("等级删除成功");
    });
  });

  it("应该处理删除等级失败的情况", async () => {
    // 设置删除API调用失败
    qualificationApi.deleteLevel.mockRejectedValueOnce(new Error("Delete Failed"));
    
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("初级")).toBeInTheDocument();
    });

    const actionButtons = screen.getAllByRole("button");
    fireEvent.click(actionButtons[actionButtons.length - 1]);

    await waitFor(() => {
      expect(confirmAction).toHaveBeenCalledWith("确定要删除该等级吗？");
      expect(qualificationApi.deleteLevel).toHaveBeenCalledWith(1);
      expect(toast.error).toHaveBeenCalledWith("删除失败");
    });
  });

  it("应该处理加载数据失败的情况", async () => {
    // 设置API调用失败
    qualificationApi.getLevels.mockRejectedValueOnce(new Error("Load Failed"));
    
    renderPage();

    // 等待错误处理
    await waitFor(() => {
      expect(qualificationApi.getLevels).toHaveBeenCalled();
    });
  });
});
