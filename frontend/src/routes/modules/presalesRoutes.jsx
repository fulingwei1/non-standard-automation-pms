import { Route, Navigate } from "react-router-dom";

import PresalesWorkstation from "../../pages/PresalesWorkstation";
import PresaleAnalytics from "../../pages/PresaleAnalytics";
import PresalesManagerWorkstation from "../../pages/PresalesManagerWorkstation";
import PresalesWorkbenchRedirect from "../../pages/PresalesWorkbenchRedirect";
import PresalesCostEstimation from "../../pages/PresalesCostEstimation";
import PresalesReviewCenter from "../../pages/PresalesReviewCenter";
import PresaleProposals from "../../pages/PresaleProposals";
import SolutionDetail from "../../pages/SolutionDetail";
import RequirementSurvey from "../../pages/RequirementSurvey";
import BiddingCenter from "../../pages/BiddingCenter";
import PresaleBids from "../../pages/PresaleBids";
import KnowledgeBase from "../../pages/KnowledgeBase";
import PresaleTemplates from "../../pages/PresaleTemplates";
import PresaleTicketBoard from "../../pages/PresaleTicketBoard";

export function PresalesRoutes() {
  return (
    <>
      <Route path="/presales-workbench" element={<PresalesWorkbenchRedirect />} />
      <Route path="/presales-dashboard" element={<PresalesWorkstation />} />
      <Route
        path="/presales-manager-dashboard"
        element={<PresalesManagerWorkstation />}
      />
      <Route path="/presales/technical-solutions" element={<PresalesReviewCenter />} />
      <Route path="/presales/cost-estimation" element={<PresalesCostEstimation />} />
      <Route path="/presales-tasks" element={<PresalesReviewCenter />} />
      <Route path="/presales/assessments" element={<Navigate to="/presales-tasks" replace />} />
      <Route path="/presales/presale-analytics" element={<PresaleAnalytics />} />
      <Route path="/presale-analytics" element={<Navigate to="/presales/presale-analytics" replace />} />
      <Route path="/presales/solutions" element={<PresaleProposals />} />
      <Route path="/solutions" element={<Navigate to="/presales/solutions" replace />} />
      <Route path="/solutions/:id" element={<SolutionDetail />} />
      <Route path="/requirement-survey" element={<Navigate to="/presales/technical-solutions?tab=surveys" replace />} />
      <Route path="/bidding" element={<BiddingCenter />} />
      <Route path="/presales/bids" element={<PresaleBids />} />
      <Route path="/knowledge-base" element={<KnowledgeBase />} />
      <Route path="/presales/templates" element={<PresaleTemplates />} />
      <Route path="/presales/ticket-board" element={<PresaleTicketBoard />} />
      <Route path="/presale-templates" element={<PresaleTemplates />} />
    </>
  );
}
