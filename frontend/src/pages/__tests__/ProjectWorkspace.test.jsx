import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import ProjectWorkspace from "../ProjectWorkspace";
import { projectWorkspaceApi } from "../../services/api";

vi.mock("../../services/api", () => ({
  projectWorkspaceApi: {
    getWorkspace: vi.fn(),
  },
}));

vi.mock("../../components/project/ProjectBonusPanel", () => ({
  default: () => <div>奖金面板</div>,
}));

vi.mock("../../components/project/ProjectMeetingPanel", () => ({
  default: () => <div>会议面板</div>,
}));

vi.mock("../../components/project/ProjectIssuePanel", () => ({
  default: () => <div>问题面板</div>,
}));

vi.mock("../../components/project/SolutionLibrary", () => ({
  default: () => <div>解决方案库</div>,
}));

describe("ProjectWorkspace", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders sales and presale handover context in the overview", async () => {
    projectWorkspaceApi.getWorkspace.mockResolvedValue({
      data: {
        project: {
          id: 1,
          project_name: "FCT整线项目",
          project_code: "PRJ-001",
          lead_id: 2026,
          progress_pct: 20,
          health: "H1",
          contract_amount: 580000,
        },
        team: [],
        tasks: [
          {
            id: 501,
            title: "跟进售前遗留事项：客户样品治具接口图未冻结",
            status: "PENDING",
            task_type: "WORKFLOW",
            source_type: "PRESALE_OPEN_ITEM",
            source_id: 901,
            source_name: "OI-001",
            assignee_name: "王工",
            progress: 0,
            priority: "HIGH",
            category: "PRESALE_HANDOVER",
            tags: ["售前交接", "未闭环事项", "TECHNICAL"],
          },
        ],
        bonus: {},
        meetings: {},
        issues: {},
        solutions: {},
        documents: [],
        handover_context: {
          contract: {
            contract_code: "CT-001",
            total_amount: 580000,
          },
          opportunity: {
            id: 2,
            opp_code: "OPP-001",
            opp_name: "电源测试线商机",
          },
          quote: {
            quote_code: "QT-001",
            version: {
              cost_total: 360000,
              total_price: 580000,
              gross_margin: 37.93,
            },
          },
          presale_solutions: [
            {
              id: 88,
              solution_no: "SOL-001",
              name: "FCT测试方案",
              ticket_id: 91,
              opportunity_id: 2,
              project_id: 1,
              template_parameters: {
                test_station_count: 4,
                cycle_time: { value: 12, unit: "秒" },
                uph: { value: 300, unit: "pcs/h", label: "目标UPH" },
                accuracy: "±0.5%",
                air_pressure: { value: 0.6, unit: "MPa" },
              },
              estimated_cost: 355000,
              suggested_price: 580000,
            },
          ],
          presale_tickets: [
            {
              id: 91,
              ticket_no: "PST-091",
              title: "FCT售前技术支持",
              ticket_type: "SOLUTION",
              status: "COMPLETED",
              assessment_status: "COMPLETED",
              current_assessment_id: 701,
              lead_id: 2026,
              opportunity_id: 2,
              project_id: 1,
              applicant_name: "张销售",
              assignee_name: "王工",
              actual_hours: 18.5,
              pm_involvement_required: true,
              pm_involvement_risk_level: "高",
              pm_involvement_risk_factors: ["金额高", "交期紧"],
              pm_assigned: false,
            },
          ],
          presale_tenders: [
            {
              id: 301,
              ticket_id: 91,
              opportunity_id: 2,
              project_id: 1,
              tender_no: "BID-001",
              tender_name: "FCT整线投标",
              our_bid_amount: 580000,
              total_score: 91.5,
              result: "WON",
              result_reason: "技术评分领先，交付周期满足客户要求",
            },
          ],
          technical_assessment: {
            current: {
              id: 701,
              source_type: "OPPORTUNITY",
              source_id: 2,
              status: "COMPLETED",
              total_score: 82,
              decision: "RECOMMEND",
              presale_ticket_id: 91,
              item_scores: [
                {
                  item_code: "tech_maturity",
                  item_name: "技术成熟度",
                  dimension: "technology",
                  score: 10,
                  max_score: 10,
                  weight: 1,
                },
                {
                  item_code: "delivery_risk",
                  item_name: "交付风险",
                  dimension: "delivery",
                  score: 7,
                  max_score: 10,
                  weight: 1,
                },
              ],
            },
            risks: {
              total: 1,
              items: [
                {
                  id: 801,
                  risk_title: "交期压缩风险",
                  risk_description: "交付周期偏紧，项目启动后需要 PM 提前排产",
                  risk_level: "HIGH",
                  status: "OPEN",
                },
              ],
            },
          },
          open_items: {
            total: 2,
            blocking_count: 1,
            items: [
              {
                id: 901,
                source_type: "OPPORTUNITY",
                source_id: 2,
                item_code: "OI-001",
                item_type: "TECHNICAL",
                description: "客户样品治具接口图未冻结",
                responsible_party: "CUSTOMER",
                responsible_person_name: "王工",
                due_date: "2026-06-15T00:00:00",
                status: "PENDING",
                blocks_quotation: true,
              },
            ],
          },
          initial_plan: {
            total: 3,
            key_count: 2,
            open_count: 3,
            milestones: [
              {
                id: 401,
                milestone_code: "MS-001",
                milestone_name: "项目启动会",
                milestone_type: "GATE",
                planned_date: "2026-06-20",
                status: "PENDING",
                is_key: true,
                stage_code: "S1",
                remark: "确认范围、成本基线和关键交付节奏",
              },
            ],
          },
          baseline_cost: {
            quote_cost_total: 360000,
            presale_estimated_cost: 355000,
          },
          handover_status: {
            ready: false,
            missing: [],
            blockers: ["open_items"],
          },
        },
        downstream_context: {
          engineering: {
            technical_reviews: {
              total: 1,
              open_count: 0,
              items: [
                {
                  review_no: "RV-001",
                  review_name: "PDR设计评审",
                  conclusion: "pass_with_condition",
                },
              ],
            },
            ecns: {
              total: 1,
              open_count: 1,
              items: [
                {
                  ecn_no: "ECN-001",
                  ecn_title: "夹具结构变更",
                  status: "APPROVED",
                },
              ],
            },
          },
          supply_chain: {
            bom: {
              total: 1,
              items: [
                {
                  bom_no: "BOM-001",
                  bom_name: "FCT整线BOM",
                },
              ],
            },
            kitting: {
              kitting_rate: 50,
              shortage_items: 1,
              shortage_details: [
                {
                  material_code: "MAT-001",
                  material_name: "关键气缸",
                  shortage_qty: 7,
                  is_key_item: true,
                },
              ],
            },
          },
          production: {
            plans: {
              total: 1,
              open_count: 1,
              items: [
                {
                  plan_no: "PP-001",
                  plan_name: "整线生产计划",
                  status: "RELEASED",
                  progress: 40,
                },
              ],
            },
            work_orders: {
              total: 2,
              open_count: 1,
              avg_progress: 70,
              items: [
                {
                  work_order_no: "WO-001",
                  task_name: "电气接线",
                  task_type: "ASSEMBLY",
                  status: "IN_PROGRESS",
                  progress: 40,
                },
              ],
            },
          },
          quality: {
            inspections: {
              total: 2,
              failed_count: 1,
              defect_qty: 1,
              items: [
                {
                  inspection_no: "QI-FAIL",
                  inspection_type: "IPQC",
                  inspection_result: "FAIL",
                  defect_type: "接线错误",
                },
              ],
            },
          },
          delivery: {
            schedules: {
              total: 1,
              active_count: 1,
              items: [
                {
                  schedule_no: "PDS-001",
                  schedule_name: "整线交付排产",
                  status: "CONFIRMED",
                },
              ],
            },
            tasks: {
              total: 2,
              open_count: 1,
              conflict_count: 1,
              avg_progress: 65,
            },
          },
          acceptance: {
            orders: {
              total: 1,
              open_count: 1,
              failed_items: 1,
              items: [
                {
                  order_no: "ACC-001",
                  acceptance_type: "FAT",
                  status: "IN_PROGRESS",
                  pass_rate: 60,
                },
              ],
            },
          },
          next_actions: [
            {
              domain: "quality",
              priority: "HIGH",
              title: "处理质检不合格项",
              description: "项目有 1 条质检不合格记录，不良数量 1",
              href: "/quality/inspections?project_id=1",
            },
            {
              domain: "delivery",
              priority: "HIGH",
              title: "解决交付排产冲突",
              description: "项目交付计划中有 1 个任务存在冲突",
              href: "/projects/1/delivery",
            },
          ],
        },
      },
    });

    render(
      <MemoryRouter initialEntries={["/projects/1/workspace"]}>
        <Routes>
          <Route path="/projects/:id/workspace" element={<ProjectWorkspace />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("项目交接包")).toBeInTheDocument();
    expect(screen.getByText("CT-001")).toBeInTheDocument();
    expect(screen.getByText("OPP-001")).toBeInTheDocument();
    expect(screen.getByText("QT-001")).toBeInTheDocument();
    expect(screen.getByText("FCT测试方案")).toBeInTheDocument();
    expect(screen.getByText("PST-091")).toBeInTheDocument();
    expect(screen.getByText("关键技术参数")).toBeInTheDocument();
    expect(screen.getByText("测试工位数")).toBeInTheDocument();
    expect(screen.getByText("4 个")).toBeInTheDocument();
    expect(screen.getByText("节拍时间")).toBeInTheDocument();
    expect(screen.getByText("12 秒")).toBeInTheDocument();
    expect(screen.getByText("目标UPH")).toBeInTheDocument();
    expect(screen.getByText("300 pcs/h")).toBeInTheDocument();
    expect(screen.getByText("还有 1 项，打开售前方案查看全部")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /FCT测试方案/ })).toHaveAttribute(
      "href",
      "/solutions/88?ticket_id=91&lead_id=2026&opportunity_id=2&project_id=1",
    );
    expect(screen.getByRole("link", { name: /PST-091/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=reviews&type=solution&ticket_id=91&lead_id=2026&opportunity_id=2&project_id=1",
    );
    expect(screen.getByText(/18.5 小时/)).toBeInTheDocument();
    expect(screen.getByText("PM提前介入")).toBeInTheDocument();
    expect(screen.getByText("高风险")).toBeInTheDocument();
    expect(screen.getByText("金额高、交期紧")).toBeInTheDocument();
    expect(screen.getByText("PM未分配")).toBeInTheDocument();
    expect(screen.getByText("技术评估")).toBeInTheDocument();
    expect(screen.getByText("82 分")).toBeInTheDocument();
    expect(screen.getByText("评估项得分")).toBeInTheDocument();
    expect(screen.getByText("技术成熟度")).toBeInTheDocument();
    expect(screen.getByText("10 / 10")).toBeInTheDocument();
    expect(screen.getByText("交付风险")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /82 分/ })).toHaveAttribute(
      "href",
      "/sales/assessments/opportunity/2?assessment_id=701&ticket_id=91&lead_id=2026&project_id=1",
    );
    expect(screen.getByText("交期压缩风险")).toBeInTheDocument();
    expect(screen.getByText("未闭环事项")).toBeInTheDocument();
    expect(screen.getByText("2 项未闭环，1 项阻塞报价/交接")).toBeInTheDocument();
    expect(screen.getByText("OI-001")).toBeInTheDocument();
    expect(screen.getByText("客户样品治具接口图未冻结")).toBeInTheDocument();
    expect(screen.getByText(/责任方：CUSTOMER/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /查看未决事项/ })).toHaveAttribute(
      "href",
      "/sales/opportunity/2/open-items",
    );
    expect(screen.getByText("投标结果")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /BID-001/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=bids&type=bidding&tender_id=301&ticket_id=91&lead_id=2026&opportunity_id=2&project_id=1",
    );
    expect(screen.getByText("已中标")).toBeInTheDocument();
    expect(screen.getAllByText(/[¥￥]580,000.00/).length).toBeGreaterThan(0);
    expect(screen.getByText("91.5 分")).toBeInTheDocument();
    expect(screen.getByText("技术评分领先，交付周期满足客户要求")).toBeInTheDocument();
    expect(screen.getByText("初始里程碑")).toBeInTheDocument();
    expect(screen.getByText("项目启动会")).toBeInTheDocument();
    expect(screen.getByText(/共 3 个里程碑/)).toBeInTheDocument();
    expect(screen.getByText(/计划：2026/)).toBeInTheDocument();
    expect(screen.getByText(/[¥￥]360,000.00/)).toBeInTheDocument();
    expect(screen.getByText("后续模块状态")).toBeInTheDocument();
    expect(screen.getByText("RV-001")).toBeInTheDocument();
    expect(screen.getByText("ECN-001")).toBeInTheDocument();
    expect(screen.getByText("BOM-001")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
    expect(screen.getByText(/MAT-001/)).toBeInTheDocument();
    expect(screen.getByText("生产/装配")).toBeInTheDocument();
    expect(screen.getByText("WO-001")).toBeInTheDocument();
    expect(screen.getAllByText("质检").length).toBeGreaterThan(0);
    expect(screen.getByText("QI-FAIL")).toBeInTheDocument();
    expect(screen.getByText("交付排产")).toBeInTheDocument();
    expect(screen.getByText("PDS-001")).toBeInTheDocument();
    expect(screen.getByText("验收")).toBeInTheDocument();
    expect(screen.getByText("ACC-001")).toBeInTheDocument();
    expect(screen.getByText("最近任务")).toBeInTheDocument();
    expect(
      screen.getByText("跟进售前遗留事项：客户样品治具接口图未冻结"),
    ).toBeInTheDocument();
    expect(screen.getByText("售前遗留")).toBeInTheDocument();
    expect(screen.getByText("后续动作")).toBeInTheDocument();
    expect(screen.getByText("处理质检不合格项")).toBeInTheDocument();
    expect(screen.getByText("解决交付排产冲突")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /处理质检不合格项/ })).toHaveAttribute(
      "href",
      "/quality/inspections?project_id=1&ticket_id=91&lead_id=2026&opportunity_id=2",
    );
    expect(screen.getByRole("link", { name: /解决交付排产冲突/ })).toHaveAttribute(
      "href",
      "/projects/1/delivery?ticket_id=91&lead_id=2026&opportunity_id=2&project_id=1",
    );
  });

  it("links feasibility assessment presale tickets to the technical assessment task filter", async () => {
    projectWorkspaceApi.getWorkspace.mockResolvedValue({
      data: {
        project: {
          id: 7,
          project_name: "夹具自动化项目",
          project_code: "PRJ-007",
          lead_id: 2027,
          progress_pct: 10,
          health: "H1",
        },
        team: [],
        tasks: [],
        bonus: {},
        meetings: {},
        issues: {},
        solutions: {},
        documents: [],
        handover_context: {
          opportunity: {
            id: 8,
            opp_code: "OPP-008",
            opp_name: "夹具自动化商机",
          },
          presale_tickets: [
            {
              id: 94,
              ticket_no: "PST-094",
              title: "夹具方案可行性评估",
              ticket_type: "FEASIBILITY_ASSESSMENT",
              status: "PROCESSING",
              assessment_status: "PENDING",
              current_assessment_id: 703,
              lead_id: 2027,
              opportunity_id: 8,
              project_id: 7,
            },
          ],
        },
      },
    });

    render(
      <MemoryRouter initialEntries={["/projects/7/workspace"]}>
        <Routes>
          <Route path="/projects/:id/workspace" element={<ProjectWorkspace />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("项目交接包")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /PST-094/ })).toHaveAttribute(
      "href",
      "/presales/technical-solutions?tab=reviews&type=assessment&ticket_id=94&lead_id=2027&opportunity_id=8&project_id=7",
    );
  });

  it("renders workspace data from formatted unified API responses", async () => {
    const workspacePayload = {
      project: {
        id: 12,
        project_name: "统一响应项目",
        project_code: "PRJ-012",
        progress_pct: 15,
        health: "H1",
        contract_amount: 120000,
      },
      team: [],
      tasks: [],
      bonus: {},
      meetings: {},
      issues: {},
      solutions: {},
      documents: [],
      handover_context: {
        handover_status: {
          ready: true,
          missing: [],
          blockers: [],
        },
      },
      downstream_context: {},
    };

    projectWorkspaceApi.getWorkspace.mockResolvedValue({
      data: {
        success: true,
        data: workspacePayload,
      },
      formatted: workspacePayload,
    });

    render(
      <MemoryRouter initialEntries={["/projects/12/workspace"]}>
        <Routes>
          <Route path="/projects/:id/workspace" element={<ProjectWorkspace />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("统一响应项目")).toBeInTheDocument();
    expect(screen.getByText("PRJ-012")).toBeInTheDocument();
    expect(screen.getByText("项目交接包")).toBeInTheDocument();
  });
});
