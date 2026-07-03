import { describe, expect, it } from "vitest";

import {
  buildTicketClosePayload,
  buildWarrantyProjects,
  getTicketId,
  normalizeDashboardTicket,
} from "../utils";

describe("CustomerServiceDashboard contracts", () => {
  it("builds backend-compatible close payloads and accepts record objects", () => {
    const ticket = { id: 7, solution: "现场更换轴承" };

    expect(getTicketId(ticket)).toBe(7);
    expect(buildTicketClosePayload(ticket)).toEqual({ solution: "现场更换轴承" });
  });

  it("falls back to real warranty service tickets when dashboard has no warranty list", () => {
    const tickets = [
      normalizeDashboardTicket({
        id: 11,
        ticket_no: "ST-11",
        project_name: "EOL测试线",
        customer_name: "客户A",
        problem_type: "WARRANTY",
        problem_desc: "质保期内电机异常",
        status: "CLOSED",
        created_at: "2026-07-01T09:00:00",
        resolved_time: "2026-07-02T10:00:00",
      }),
      normalizeDashboardTicket({
        id: 12,
        ticket_no: "ST-12",
        project_name: "ICT测试线",
        customer_name: "客户B",
        problem_type: "OTHER",
        problem_desc: "普通咨询",
        status: "PENDING",
      }),
    ];

    const projects = buildWarrantyProjects({
      dashboardWarrantyProjects: [],
      tickets,
    });

    expect(projects).toHaveLength(1);
    expect(projects[0]).toMatchObject({
      id: "ticket-11",
      projectName: "EOL测试线",
      customerName: "客户A",
      totalClaims: 1,
      resolvedClaims: 1,
    });
  });
});
