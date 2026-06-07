import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SolutionHeader } from "../SolutionHeader";

const draftSolution = {
  id: 88,
  code: "SOL-20260607-001",
  name: "华南电子FCT方案",
  status: "draft",
  version: "V1.0",
};

describe("SolutionHeader", () => {
  it("submits a draft solution for review from the action menu", async () => {
    const onSubmitReview = vi.fn();
    const user = userEvent.setup();

    render(
      <SolutionHeader
        solution={draftSolution}
        navigate={vi.fn()}
        onSubmitReview={onSubmitReview}
      />,
    );

    const buttons = screen.getAllByRole("button");
    await user.click(buttons[buttons.length - 1]);
    await user.click(await screen.findByText("提交评审"));

    expect(onSubmitReview).toHaveBeenCalledTimes(1);
  });

  it("returns to the filtered presales solution context", async () => {
    const navigate = vi.fn();
    const user = userEvent.setup();

    render(
      <SolutionHeader
        solution={{
          ...draftSolution,
          ticketId: 501,
          opportunityId: 2,
          projectId: 42,
        }}
        navigate={navigate}
      />,
    );

    await user.click(screen.getAllByRole("button")[0]);

    expect(navigate).toHaveBeenCalledWith(
      "/presales/technical-solutions?tab=solutions&type=support&ticket_id=501&opportunity_id=2&project_id=42",
    );
  });
});
