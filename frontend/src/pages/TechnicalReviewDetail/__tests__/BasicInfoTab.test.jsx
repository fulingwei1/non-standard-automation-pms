import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { BasicInfoTab } from "../BasicInfoTab";

const baseFormData = {
  review_type: "PDR",
  review_name: "自动化线方案评审",
  project_id: "",
  scheduled_date: "2026-06-07T10:00",
  location: "会议室A",
  meeting_type: "ONSITE",
  host_id: "",
  presenter_id: "",
  recorder_id: "",
};

describe("BasicInfoTab", () => {
  it("renders usable select fields for creating a technical review", () => {
    const updateField = vi.fn();

    render(
      <BasicInfoTab
        isNew
        review={null}
        formData={baseFormData}
        updateField={updateField}
        projects={[{ id: 7, project_code: "P20260607", project_name: "新能源测试线" }]}
        users={[{ id: 3, real_name: "张工", username: "zhanggong" }]}
      />,
    );

    fireEvent.change(screen.getByLabelText("评审类型"), {
      target: { value: "DDR" },
    });
    fireEvent.change(screen.getByLabelText("关联项目"), {
      target: { value: "7" },
    });
    fireEvent.change(screen.getByLabelText("主持人"), {
      target: { value: "3" },
    });

    expect(updateField).toHaveBeenCalledWith("review_type", "DDR");
    expect(updateField).toHaveBeenCalledWith("project_id", "7");
    expect(updateField).toHaveBeenCalledWith("host_id", "3");
  });
});
