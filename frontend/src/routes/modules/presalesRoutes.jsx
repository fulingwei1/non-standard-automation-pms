import { lazy } from "react";
import { Route, Navigate } from "react-router-dom";

// ---- 懒加载页面组件（售前模块） ----
const PresalesWorkbenchRedirect = lazy(() => import("../../pages/PresalesWorkbenchRedirect"));
const PresalesWorkstation = lazy(() => import("../../pages/PresalesWorkstation"));
const PresalesManagerWorkstation = lazy(() => import("../../pages/PresalesManagerWorkstation"));
const PresalesReviewCenter = lazy(() => import("../../pages/PresalesReviewCenter"));
const PresalesCostEstimation = lazy(() => import("../../pages/PresalesCostEstimation"));
const PresaleAnalytics = lazy(() => import("../../pages/PresaleAnalytics"));
const PresaleProposals = lazy(() => import("../../pages/PresaleProposals"));
const SolutionDetail = lazy(() => import("../../pages/SolutionDetail"));
const BiddingCenter = lazy(() => import("../../pages/BiddingCenter"));
const PresaleBids = lazy(() => import("../../pages/PresaleBids"));
const KnowledgeBase = lazy(() => import("../../pages/KnowledgeBase"));
const PresaleTemplates = lazy(() => import("../../pages/PresaleTemplates"));
const PresaleTicketBoard = lazy(() => import("../../pages/PresaleTicketBoard"));

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
