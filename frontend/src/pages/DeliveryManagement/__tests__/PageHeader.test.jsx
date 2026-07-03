import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import PageHeader from "../PageHeader";

describe("DeliveryManagement PageHeader", () => {
  it("does not expose standalone delivery creation from the global list", () => {
    render(
      <PageHeader
        canCreateFromProject={false}
        onNew={vi.fn()}
        onRefresh={vi.fn()}
        onExport={vi.fn()}
      />,
    );

    expect(screen.queryByRole("button", { name: /创建发货单/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /生成发货计划/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /刷新/ })).toBeInTheDocument();
  });

  it("shows project-scoped delivery plan generation when project context exists", () => {
    render(
      <PageHeader
        canCreateFromProject
        onNew={vi.fn()}
        onRefresh={vi.fn()}
        onExport={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /生成发货计划/ })).toBeInTheDocument();
  });
});
