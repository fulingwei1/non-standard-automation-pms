import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import PresalesReviewCenter from "../PresalesReviewCenter";

const presaleProposalsMock = vi.hoisted(() => vi.fn(({ embedded }) => (
  <div>新方案管理中心 {embedded ? "embedded" : "standalone"}</div>
)));

const setSearchParamsMock = vi.hoisted(() => vi.fn());
const routeState = vi.hoisted(() => ({
  search: "tab=solutions",
}));

vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    useLocation: () => ({
      pathname: "/presales/technical-solutions",
      search: `?${routeState.search}`,
      hash: "",
      state: null,
    }),
    useNavigate: () => vi.fn(),
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

describe("PresalesReviewCenter", () => {
  beforeEach(() => {
    routeState.search = "tab=solutions";
    setSearchParamsMock.mockClear();
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
});
