import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import DispatchDetailDialog from "../DispatchDetailDialog";
import DispatchList from "../DispatchList";
import FieldServiceWorkLogDialog from "../FieldServiceWorkLogDialog";
import { validateDispatchData } from "../../../lib/constants/installationDispatch";

const backendOrder = {
  id: 42,
  order_no: "INST-QA-001",
  project_name: "QA交付验收项目",
  machine_name: "QA机台",
  task_type: "INSTALLATION",
  priority: "HIGH",
  status: "PENDING",
  assigned_to_name: "张工",
  task_title: "现场安装调试",
  task_description: "完成现场安装与调试",
  scheduled_date: "2026-07-20",
  estimated_hours: "6.5",
  location: "深圳客户现场",
  customer_phone: "13900000000",
  customer_address: "深圳市南山区",
};

describe("installation dispatch components", () => {
  it("renders backend snake_case fields in the dispatch list", () => {
    render(
      <DispatchList
        orders={[backendOrder]}
        loading={false}
        selectedOrders={new Set()}
        onSelectOrder={vi.fn()}
        onSelectAll={vi.fn()}
        onViewDetail={vi.fn()}
        onAssign={vi.fn()}
        onStart={vi.fn()}
        onUpdateProgress={vi.fn()}
        onComplete={vi.fn()}
      />,
    );

    expect(screen.getByText("INST-QA-001")).toBeInTheDocument();
    expect(screen.getByText("QA交付验收项目")).toBeInTheDocument();
    expect(screen.getByText("张工")).toBeInTheDocument();
    expect(screen.getByText("安装")).toBeInTheDocument();
    expect(screen.getByText("高优先级")).toBeInTheDocument();
    expect(screen.getByText("待派工")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "指派派工单" })).toBeInTheDocument();
  });

  it("shows a start action for assigned dispatch orders", () => {
    render(
      <DispatchList
        orders={[{ ...backendOrder, status: "ASSIGNED" }]}
        loading={false}
        selectedOrders={new Set()}
        onSelectOrder={vi.fn()}
        onSelectAll={vi.fn()}
        onViewDetail={vi.fn()}
        onAssign={vi.fn()}
        onStart={vi.fn()}
        onUpdateProgress={vi.fn()}
        onComplete={vi.fn()}
      />,
    );

    expect(screen.getByText("已派工")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "开始执行" })).toBeInTheDocument();
  });

  it("renders backend snake_case fields in the detail dialog", () => {
    render(
      <DispatchDetailDialog
        open
        onOpenChange={vi.fn()}
        order={backendOrder}
      />,
    );

    expect(screen.getByText("INST-QA-001")).toBeInTheDocument();
    expect(screen.getByText("QA交付验收项目")).toBeInTheDocument();
    expect(screen.getByText("QA机台")).toBeInTheDocument();
    expect(screen.getByText("张工")).toBeInTheDocument();
    expect(screen.getByText("深圳客户现场")).toBeInTheDocument();
  });

  it("validates the backend dispatch create payload shape", () => {
    expect(
      validateDispatchData({
        project_id: "12",
        customer_id: "7",
        task_type: "INSTALLATION",
        task_title: "现场安装调试",
        scheduled_date: "2026-07-20",
      }),
    ).toEqual({ isValid: true, errors: [] });
  });

  it("renders field service work log context from dispatch orders", () => {
    render(
      <FieldServiceWorkLogDialog
        open
        onOpenChange={vi.fn()}
        workLogDate="2026-07-20"
        onWorkLogDateChange={vi.fn()}
        context={{
          work_date: "2026-07-20",
          has_submitted_log: false,
          items: [
            {
              dispatch_order_id: 42,
              order_no: "INST-QA-001",
              status: "IN_PROGRESS",
              task_type: "INSTALLATION",
              task_title: "现场安装调试",
              project_name: "QA交付验收项目",
              machine_name: "QA机台",
              scheduled_date: "2026-07-20",
              progress: 35,
            },
          ],
        }}
        logData={{ today_progress: "", issues_found: "", next_plan: "", work_hours: "" }}
        onLogDataChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByText("今日外出日志")).toBeInTheDocument();
    expect(screen.getByText("INST-QA-001")).toBeInTheDocument();
    expect(screen.getByText("QA交付验收项目 / QA机台")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "提交日志" })).toBeInTheDocument();
  });
});
