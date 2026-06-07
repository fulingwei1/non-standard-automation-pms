import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { TechnicalReviewFilter } from "../TechnicalReviewFilter";

describe("TechnicalReviewFilter", () => {
  it("renders usable select filters for project, review type, and status", () => {
    const setProjectId = vi.fn();
    const setReviewType = vi.fn();
    const setStatus = vi.fn();

    render(
      <TechnicalReviewFilter
        searchKeyword=""
        setSearchKeyword={vi.fn()}
        projectId=""
        setProjectId={setProjectId}
        reviewType=""
        setReviewType={setReviewType}
        status=""
        setStatus={setStatus}
        projectList={[{ id: 11, project_code: "P20260611", project_name: "FCT设备" }]}
        onSearch={vi.fn()}
        onReset={vi.fn()}
        onCreate={vi.fn()}
      />,
    );

    fireEvent.change(screen.getByLabelText("项目"), {
      target: { value: "11" },
    });
    fireEvent.change(screen.getByLabelText("评审类型"), {
      target: { value: "DDR" },
    });
    fireEvent.change(screen.getByLabelText("状态"), {
      target: { value: "IN_PROGRESS" },
    });

    expect(setProjectId).toHaveBeenCalledWith("11");
    expect(setReviewType).toHaveBeenCalledWith("DDR");
    expect(setStatus).toHaveBeenCalledWith("IN_PROGRESS");
  });
});
