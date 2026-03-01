import { Route, Navigate } from "react-router-dom";

import PresalesWorkstation from "../../pages/PresalesWorkstation";
import PresalesManagerWorkstation from "../../pages/PresalesManagerWorkstation";
import PresalesReviewCenter from "../../pages/PresalesReviewCenter";
import PresaleProposals from "../../pages/PresaleProposals";
import SolutionDetail from "../../pages/SolutionDetail";
import RequirementSurvey from "../../pages/RequirementSurvey";
import BiddingCenter from "../../pages/BiddingCenter";
import PresaleBids from "../../pages/PresaleBids";
import KnowledgeBase from "../../pages/KnowledgeBase";
import PresaleTemplates from "../../pages/PresaleTemplates";

export function PresalesRoutes() {
  return (
    <>
      <Route path="/presales-dashboard" element={<PresalesWorkstation />} />
      <Route
        path="/presales-manager-dashboard"
        element={<PresalesManagerWorkstation />}
      />
      <Route path="/presales-tasks" element={<PresalesReviewCenter />} />
      <Route path="/presale-analytics" element={<Navigate to="/sales/sales-analysis" replace />} />
      <Route path="/solutions" element={<PresaleProposals />} />
      <Route path="/solutions/:id" element={<SolutionDetail />} />
      <Route path="/requirement-survey" element={<RequirementSurvey />} />
      <Route path="/bidding" element={<BiddingCenter />} />
      <Route path="/presales-bids" element={<PresaleBids />} />
      <Route path="/knowledge-base" element={<KnowledgeBase />} />
      <Route path="/presales/templates" element={<PresaleTemplates />} />
      <Route path="/presale-templates" element={<PresaleTemplates />} />
    </>
  );
}
