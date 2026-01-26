import { Route } from "react-router-dom";

import PresalesWorkstation from "../../pages/PresalesWorkstation";
import PresalesManagerWorkstation from "../../pages/PresalesManagerWorkstation";
import PresalesReviewCenter from "../../pages/PresalesReviewCenter";
import SolutionDetail from "../../pages/SolutionDetail";
import RequirementSurvey from "../../pages/RequirementSurvey";
import BiddingCenter from "../../pages/BiddingCenter";
import KnowledgeBase from "../../pages/KnowledgeBase";

export function PresalesRoutes() {
  return (
    <>
      <Route path="/presales-dashboard" element={<PresalesWorkstation />} />
      <Route
        path="/presales-manager-dashboard"
        element={<PresalesManagerWorkstation />}
      />
      <Route path="/presales-tasks" element={<PresalesReviewCenter />} />
      <Route path="/solutions" element={<PresalesReviewCenter />} />
      <Route path="/solutions/:id" element={<SolutionDetail />} />
      <Route path="/requirement-survey" element={<RequirementSurvey />} />
      <Route path="/bidding" element={<BiddingCenter />} />
      <Route path="/knowledge-base" element={<KnowledgeBase />} />
    </>
  );
}
