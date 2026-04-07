import { lazyLoad } from "../lazyLoad";

const PresalesWorkstation = lazyLoad(() => import("../../pages/PresalesWorkstation"));
const PresaleAnalytics = lazyLoad(() => import("../../pages/PresaleAnalytics"));
const PresalesManagerWorkstation = lazyLoad(() => import("../../pages/PresalesManagerWorkstation"));
const PresalesWorkbenchRedirect = lazyLoad(() => import("../../pages/PresalesWorkbenchRedirect"));
const PresalesCostEstimation = lazyLoad(() => import("../../pages/PresalesCostEstimation"));
const PresalesReviewCenter = lazyLoad(() => import("../../pages/PresalesReviewCenter"));
const PresaleProposals = lazyLoad(() => import("../../pages/PresaleProposals"));
const SolutionDetail = lazyLoad(() => import("../../pages/SolutionDetail"));
const RequirementSurvey = lazyLoad(() => import("../../pages/RequirementSurvey"));
const BiddingCenter = lazyLoad(() => import("../../pages/BiddingCenter"));
const PresaleBids = lazyLoad(() => import("../../pages/PresaleBids"));
const KnowledgeBase = lazyLoad(() => import("../../pages/KnowledgeBase"));
const PresaleTemplates = lazyLoad(() => import("../../pages/PresaleTemplates"));
const PresaleTicketBoard = lazyLoad(() => import("../../pages/PresaleTicketBoard"));

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
