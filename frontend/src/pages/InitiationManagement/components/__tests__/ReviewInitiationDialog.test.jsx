import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ReviewInitiationDialog } from "../ReviewInitiationDialog";

describe("ReviewInitiationDialog", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("blocks approval submit when no project manager is selected", async () => {
    const user = userEvent.setup();
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    const onSubmit = vi.fn();

    render(
      <ReviewInitiationDialog
        open
        mode="approve"
        projectManagers={[]}
        loading={false}
        onOpenChange={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    await user.click(screen.getByRole("button", { name: "审批通过" }));

    expect(alertSpy).toHaveBeenCalledWith("审批通过前必须指定项目经理");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits the selected project manager on approval", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(true);

    render(
      <ReviewInitiationDialog
        open
        mode="approve"
        projectManagers={[{ id: 8, real_name: "项目经理A" }]}
        loading={false}
        onOpenChange={vi.fn()}
        onSubmit={onSubmit}
      />,
    );

    await user.click(screen.getByRole("button", { name: "审批通过" }));

    expect(onSubmit).toHaveBeenCalledWith({
      review_result: "同意立项",
      approved_pm_id: 8,
    });
  });
});
