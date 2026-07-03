import { describe, expect, it, vi, beforeEach, beforeAll } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";

import CreateFormDialog from "../CreateFormDialog";
import RecordsTable from "../RecordsTable";
import FilterBar from "../FilterBar";
import { acceptanceApi } from "../../../services/api/acceptance";
import { projectApi } from "../../../services/api/projects";

vi.mock("../../../services/api/acceptance", () => ({
  acceptanceApi: {
    templates: {
      list: vi.fn(),
    },
  },
}));

vi.mock("../../../services/api/projects", () => ({
  projectApi: {
    getMachines: vi.fn(),
  },
}));

describe("AcceptanceManagement", () => {
  beforeAll(() => {
    if (!Element.prototype.hasPointerCapture) {
      Element.prototype.hasPointerCapture = () => false;
    }
    if (!Element.prototype.setPointerCapture) {
      Element.prototype.setPointerCapture = () => {};
    }
    if (!Element.prototype.releasePointerCapture) {
      Element.prototype.releasePointerCapture = () => {};
    }
    if (!Element.prototype.scrollIntoView) {
      Element.prototype.scrollIntoView = () => {};
    }
  });

  beforeEach(() => {
    vi.clearAllMocks();
    acceptanceApi.templates.list.mockResolvedValue({
      data: { items: [{ id: 7, template_name: "QA FAT 验收模板", acceptance_type: "FAT" }] },
    });
    projectApi.getMachines.mockResolvedValue({
      data: { items: [{ id: 11, machine_name: "QA 设备 01", machine_no: 1 }] },
    });
  });

  it("creates FAT acceptance records with machine and checklist template context", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue();

    render(
      <CreateFormDialog
        open
        onOpenChange={vi.fn()}
        projects={[{ id: 3, project_name: "QA 验收项目" }]}
        onSubmit={onSubmit}
      />,
    );

    await user.click(screen.getByRole("combobox", { name: /选择项目/i }));
    await user.click(screen.getByRole("option", { name: "QA 验收项目" }));

    await waitFor(() => {
      expect(projectApi.getMachines).toHaveBeenCalledWith("3");
    });
    await user.click(screen.getByRole("combobox", { name: /关联设备/i }));
    await user.click(screen.getByRole("option", { name: /QA 设备 01/i }));

    await waitFor(() => {
      expect(acceptanceApi.templates.list).toHaveBeenCalledWith({
        acceptance_type: "FAT",
        page_size: 200,
      });
    });
    await user.click(screen.getByRole("combobox", { name: /检查模板/i }));
    await user.click(screen.getByRole("option", { name: "QA FAT 验收模板" }));

    await user.type(screen.getByLabelText(/验收标题/i), "QA FAT 验收");
    await user.type(screen.getByLabelText(/计划日期/i), "2035-02-01");
    await user.click(screen.getByRole("button", { name: "创建" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          project_id: "3",
          machine_id: "11",
          template_id: "7",
          acceptance_type: "FAT",
          scheduled_date: "2035-02-01",
        }),
      );
    });
  });

  it("re-enables the create button when submission fails", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockRejectedValue(new Error("submit failed"));

    render(
      <CreateFormDialog
        open
        onOpenChange={vi.fn()}
        projects={[{ id: 3, project_name: "QA 验收项目" }]}
        onSubmit={onSubmit}
      />,
    );

    await user.click(screen.getByRole("combobox", { name: /选择项目/i }));
    await user.click(screen.getByRole("option", { name: "QA 验收项目" }));
    await user.click(screen.getByRole("combobox", { name: /关联设备/i }));
    await user.click(screen.getByRole("option", { name: /QA 设备 01/i }));
    await user.click(screen.getByRole("combobox", { name: /检查模板/i }));
    await user.click(screen.getByRole("option", { name: "QA FAT 验收模板" }));
    await user.type(screen.getByLabelText(/验收标题/i), "QA FAT 验收");
    await user.click(screen.getByRole("button", { name: "创建" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "创建" })).toBeEnabled();
    });
  });

  it("exposes start and execute actions from the records table", async () => {
    const onStart = vi.fn();
    const onExecute = vi.fn();

    render(
      <MemoryRouter>
        <RecordsTable
          loading={false}
          onViewDetail={vi.fn()}
          onStart={onStart}
          onExecute={onExecute}
          filteredRecords={[
            {
              id: 1,
              acceptance_code: "ACC-DRAFT",
              project_name: "草稿项目",
              acceptance_type: "FAT",
              title: "草稿验收",
              status: "draft",
            },
            {
              id: 2,
              acceptance_code: "ACC-RUN",
              project_name: "执行项目",
              acceptance_type: "SAT",
              title: "执行验收",
              status: "in_progress",
            },
          ]}
        />
      </MemoryRouter>,
    );

    await userEvent.click(
      within(screen.getByText("ACC-DRAFT").closest("tr")).getByRole("button", {
        name: /开始验收/i,
      }),
    );
    expect(onStart).toHaveBeenCalledWith(1);

    await userEvent.click(
      within(screen.getByText("ACC-RUN").closest("tr")).getByRole("button", {
        name: /执行验收/i,
      }),
    );
    expect(onExecute).toHaveBeenCalledWith(2);
  });

  it("keeps the empty search input empty instead of showing a fallback word", () => {
    render(
      <FilterBar
        searchText=""
        setSearchText={vi.fn()}
        filters={{ type: "", status: "" }}
        setFilters={vi.fn()}
        onCreate={vi.fn()}
        onRefresh={vi.fn()}
      />,
    );

    expect(screen.getByPlaceholderText(/搜索验收编号/i)).toHaveValue("");
  });
});
