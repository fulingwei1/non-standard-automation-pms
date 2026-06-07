import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import PresalesReviewCenter from "../PresalesReviewCenter";

const presaleProposalsMock = vi.hoisted(() => vi.fn(({ embedded }) => (
  <div>新方案管理中心 {embedded ? "embedded" : "standalone"}</div>
)));

const setSearchParamsMock = vi.hoisted(() => vi.fn());
const navigateMock = vi.hoisted(() => vi.fn());
const routeState = vi.hoisted(() => ({
  pathname: "/presales/technical-solutions",
  search: "tab=solutions",
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useLocation: () => ({
      pathname: routeState.pathname,
      search: `?${routeState.search}`,
      hash: "",
      state: null,
    }),
    useNavigate: () => navigateMock,
    useSearchParams: () => [new URLSearchParams(routeState.search), setSearchParamsMock],
  };
});

vi.mock("../RequirementSurvey", () => ({
  default: () => <div>需求调研中心</div>,
}));

vi.mock("../SolutionList", () => ({
  default: () => <div>旧方案列表</div>,
}));

vi.mock("../PresaleProposals", () => ({
  default: presaleProposalsMock,
}));

vi.mock("../PresalesTasks", () => ({
  default: () => <div>工单看板中心</div>,
}));

vi.mock("../TechnicalParameterManagement", () => ({
  default: ({ embedded }) => <div>技术参数模板中心 {embedded ? "embedded" : "standalone"}</div>,
}));

vi.mock("../PresalesCostEstimation", () => ({
  default: ({ embedded }) => <div>成本估算中心 {embedded ? "embedded" : "standalone"}</div>,
}));

vi.mock("../BiddingCenter", () => ({
  default: ({ embedded }) => <div>投标支持中心 {embedded ? "embedded" : "standalone"}</div>,
}));

vi.mock("../PresaleTemplates", () => ({
  default: ({ embedded }) => <div>知识模板中心 {embedded ? "embedded" : "standalone"}</div>,
}));

describe("PresalesReviewCenter", () => {
  beforeEach(() => {
    routeState.pathname = "/presales/technical-solutions";
    routeState.search = "tab=solutions";
    setSearchParamsMock.mockClear();
    navigateMock.mockClear();
    presaleProposalsMock.mockClear();
  });

  it("uses the unified proposal workflow in the technical solutions center", async () => {
    render(<PresalesReviewCenter />);

    expect(screen.getByText(/新方案管理中心 embedded/)).toBeInTheDocument();
    expect(screen.queryByText("旧方案列表")).not.toBeInTheDocument();
    expect(presaleProposalsMock).toHaveBeenCalledWith(
      expect.objectContaining({ embedded: true }),
      undefined,
    );
  });

  it("opens technical parameter templates inside the technical solutions center", () => {
    routeState.search = "tab=parameters";

    render(<PresalesReviewCenter />);

    expect(screen.getByText(/技术参数模板中心 embedded/)).toBeInTheDocument();
    expect(screen.queryByText("工单看板中心")).not.toBeInTheDocument();
  });

  it("opens cost estimation inside the technical solutions center", () => {
    routeState.search = "tab=cost";

    render(<PresalesReviewCenter />);

    expect(screen.getByText(/成本估算中心 embedded/)).toBeInTheDocument();
    expect(screen.queryByText("工单看板中心")).not.toBeInTheDocument();
  });

  it("opens bidding support inside the technical solutions center", () => {
    routeState.search = "tab=bids";

    render(<PresalesReviewCenter />);

    expect(screen.getByText(/投标支持中心 embedded/)).toBeInTheDocument();
    expect(screen.queryByText("工单看板中心")).not.toBeInTheDocument();
  });

  it("opens presales knowledge templates inside the technical solutions center", () => {
    routeState.search = "tab=knowledge";

    render(<PresalesReviewCenter />);

    expect(screen.getByText(/知识模板中心 embedded/)).toBeInTheDocument();
    expect(screen.queryByText("工单看板中心")).not.toBeInTheDocument();
  });

  it("preserves sales support context params when switching center tabs", () => {
    routeState.search = "tab=reviews&type=support&status=pending&lead_id=2026&opportunity_id=2&ticket_id=501";

    render(<PresalesReviewCenter />);

    fireEvent.click(screen.getByText("方案管理"));

    const nextParams = setSearchParamsMock.mock.calls[0][0];
    expect(nextParams.toString()).toBe(
      "tab=solutions&type=support&status=pending&lead_id=2026&opportunity_id=2&ticket_id=501",
    );
  });

  it("keeps sales support context when switching tabs from a legacy presales route", () => {
    routeState.pathname = "/presales/solutions";
    routeState.search = "type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42";

    render(<PresalesReviewCenter />);

    fireEvent.click(screen.getByText("投标支持"));

    expect(navigateMock).toHaveBeenCalledWith(
      "/presales/technical-solutions?type=support&lead_id=2026&opportunity_id=2&ticket_id=501&project_id=42&tab=bids",
    );
  });
});
