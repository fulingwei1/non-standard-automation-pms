import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import TicketTable from "../TicketTable";
import { toTicketModel } from "../utils";

function renderTicketTable(ticket) {
  const noop = vi.fn();

  return render(
    <TicketTable
      filteredTickets={[ticket]}
      searchKeyword=""
      setSearchKeyword={noop}
      statusFilter="all"
      setStatusFilter={noop}
      priorityFilter="all"
      setPriorityFilter={noop}
      selectedTicketId={ticket.id}
      setSelectedTicketId={noop}
      priorityUpdatingId={null}
      flowUpdatingId={null}
      handlePriorityChange={noop}
      handleAdvanceFlow={noop}
      renderFlowActionLabel={() => "接单"}
    />,
  );
}

describe("PresaleTicketBoard PM context", () => {
  it("keeps PM involvement fields from the presale ticket API", () => {
    const model = toTicketModel({
      id: 101,
      title: "大型线体方案评审",
      ticket_no: "PST-101",
      urgency: "HIGH",
      status: "PENDING",
      customer_name: "华南电子",
      applicant_name: "王伟",
      pm_involvement_required: true,
      pm_involvement_risk_level: "高",
      pm_involvement_risk_factors: ["金额高", "交期紧"],
      pm_assigned: true,
      pm_user_id: 7,
      project_id: 42,
      opportunity_id: 501,
    });

    expect(model.pmInvolvementRequired).toBe(true);
    expect(model.pmInvolvementRiskLevel).toBe("高");
    expect(model.pmInvolvementRiskFactors).toEqual(["金额高", "交期紧"]);
    expect(model.pmAssigned).toBe(true);
    expect(model.pmUserId).toBe(7);
    expect(model.projectId).toBe(42);
    expect(model.opportunityId).toBe(501);
  });

  it("shows PM involvement status and risk factors in the ticket table", () => {
    renderTicketTable({
      id: 101,
      ticketNo: "PST-101",
      title: "大型线体方案评审",
      ticketTypeLabel: "方案评审",
      priority: "HIGH",
      status: "PENDING",
      customerName: "华南电子",
      applicantName: "王伟",
      assigneeName: "未指派",
      applyTime: "2026-06-07T09:00:00",
      deadline: "2026-06-12T18:00:00",
      description: "需要项目经理提前参与交期评估",
      pmInvolvementRequired: true,
      pmInvolvementRiskLevel: "高",
      pmInvolvementRiskFactors: ["金额高", "交期紧"],
      pmAssigned: false,
    });

    expect(screen.getByText("需PM介入")).toBeInTheDocument();
    expect(screen.getByText("高风险")).toBeInTheDocument();
    expect(screen.getByText("金额高、交期紧")).toBeInTheDocument();
    expect(screen.getByText("PM未分配")).toBeInTheDocument();
  });
});
