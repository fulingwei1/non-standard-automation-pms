import { describe, expect, it } from "vitest";

import { buildTechnicalAssessmentPath } from "../salesNavigation";

describe("salesNavigation", () => {
  it("keeps the existing bare technical assessment path", () => {
    expect(buildTechnicalAssessmentPath("lead", 12)).toBe("/sales/assessments/lead/12");
    expect(buildTechnicalAssessmentPath("opportunity", 8)).toBe(
      "/sales/assessments/opportunity/8",
    );
  });

  it("keeps presale and project context when opening an opportunity assessment", () => {
    expect(
      buildTechnicalAssessmentPath("opportunity", 8, {
        assessmentId: 701,
        presaleTicketId: 501,
        leadId: 2026,
        projectId: 42,
      }),
    ).toBe(
      "/sales/assessments/opportunity/8?assessment_id=701&ticket_id=501&lead_id=2026&project_id=42",
    );
  });

  it("accepts backend snake_case context fields", () => {
    expect(
      buildTechnicalAssessmentPath("lead", 12, {
        assessment_id: 702,
        presale_ticket_id: 502,
        project_id: 43,
      }),
    ).toBe("/sales/assessments/lead/12?assessment_id=702&ticket_id=502&project_id=43");
  });
});
