import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SalesRoutes } from "../salesRoutes";
import { defaultNavGroups } from "../../../components/layout/sidebarConfig";

vi.mock("../../../pages/SalesAI/CompetitorAnalysis", () => ({
  default: () => <div>竞品假页面</div>,
}));

function collectItems(groups) {
  return groups.flatMap((group) => group.items || []);
}

describe("sales competitor analysis stopgap", () => {
  it("does not expose the hard-coded competitor analysis menu item", () => {
    const items = collectItems(defaultNavGroups);

    expect(items.map((item) => item.path)).not.toContain("/sales/competitor-analysis");
    expect(items.map((item) => item.name)).not.toContain("对手分析");
  });

  it("does not mount the hard-coded competitor analysis route", async () => {
    render(
      <MemoryRouter initialEntries={["/sales/competitor-analysis"]}>
        <Routes>
          {SalesRoutes()}
          <Route path="*" element={<div>未找到页面</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("未找到页面")).toBeInTheDocument();
    expect(screen.queryByText("竞品假页面")).not.toBeInTheDocument();
  });
});
