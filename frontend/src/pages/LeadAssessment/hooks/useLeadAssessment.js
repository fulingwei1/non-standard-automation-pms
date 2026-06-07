import { useTechnicalAssessment } from "../../TechnicalAssessment/hooks/useTechnicalAssessment";

export function useLeadAssessment(leadId) {
  return useTechnicalAssessment("lead", leadId);
}
