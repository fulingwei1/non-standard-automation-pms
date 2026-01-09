import { lazy } from 'react'

// Sales Pages
const SalesWorkstation = lazy(() => import('../pages/SalesWorkstation'))
const SalesDirectorWorkstation = lazy(() => import('../pages/SalesDirectorWorkstation'))
const SalesManagerWorkstation = lazy(() => import('../pages/SalesManagerWorkstation'))
const SalesReports = lazy(() => import('../pages/SalesReports'))
const SalesTeam = lazy(() => import('../pages/SalesTeam'))
const SalesTarget = lazy(() => import('../pages/SalesTarget'))
const ContractApproval = lazy(() => import('../pages/ContractApproval'))
const BusinessSupportWorkstation = lazy(() => import('../pages/BusinessSupportWorkstation'))
const CustomerList = lazy(() => import('../pages/CustomerList'))
const Customer360 = lazy(() => import('../pages/Customer360'))
const OpportunityBoard = lazy(() => import('../pages/OpportunityBoard'))
const LeadAssessment = lazy(() => import('../pages/LeadAssessment'))
const QuotationList = lazy(() => import('../pages/QuotationList'))
const ContractList = lazy(() => import('../pages/ContractList'))
const ContractDetail = lazy(() => import('../pages/ContractDetail'))
const SalesProjectTrack = lazy(() => import('../pages/SalesProjectTrack'))
const SalesFunnel = lazy(() => import('../pages/SalesFunnel'))
const BiddingDetail = lazy(() => import('../pages/BiddingDetail'))

// New Sales Module
const LeadManagement = lazy(() => import('../pages/LeadManagement'))
const OpportunityManagement = lazy(() => import('../pages/OpportunityManagement'))
const TechnicalAssessment = lazy(() => import('../pages/TechnicalAssessment'))
const LeadRequirementDetail = lazy(() => import('../pages/LeadRequirementDetail'))
const OpenItemsManagement = lazy(() => import('../pages/OpenItemsManagement'))
const RequirementFreezeManagement = lazy(() => import('../pages/RequirementFreezeManagement'))
const AIClarificationChat = lazy(() => import('../pages/AIClarificationChat'))
const QuoteManagement = lazy(() => import('../pages/QuoteManagement'))
const QuoteCostManagement = lazy(() => import('../pages/QuoteCostManagement'))
const QuoteCostAnalysis = lazy(() => import('../pages/QuoteCostAnalysis'))
const CostTemplateManagement = lazy(() => import('../pages/CostTemplateManagement'))
const PurchaseMaterialCostManagement = lazy(() => import('../pages/PurchaseMaterialCostManagement'))
const FinancialCostUpload = lazy(() => import('../pages/FinancialCostUpload'))
const ContractManagement = lazy(() => import('../pages/ContractManagement'))
const ReceivableManagement = lazy(() => import('../pages/ReceivableManagement'))
const SalesStatistics = lazy(() => import('../pages/SalesStatistics'))
const SalesTemplateCenter = lazy(() => import('../pages/SalesTemplateCenter'))
const CpqConfigurator = lazy(() => import('../pages/CpqConfigurator'))

// Pre-sales Pages
const PresalesWorkstation = lazy(() => import('../pages/PresalesWorkstation'))
const PresalesManagerWorkstation = lazy(() => import('../pages/PresalesManagerWorkstation'))
const PresalesTasks = lazy(() => import('../pages/PresalesTasks'))
const SolutionList = lazy(() => import('../pages/SolutionList'))
const SolutionDetail = lazy(() => import('../pages/SolutionDetail'))
const RequirementSurvey = lazy(() => import('../pages/RequirementSurvey'))
const BiddingCenter = lazy(() => import('../pages/BiddingCenter'))
const KnowledgeBase = lazy(() => import('../pages/KnowledgeBase'))

export const salesRoutes = [
  // Sales Dashboard
  { path: '/sales-dashboard', element: <SalesWorkstation /> },
  { path: '/sales-director-dashboard', element: <SalesDirectorWorkstation /> },
  { path: '/sales-manager-dashboard', element: <SalesManagerWorkstation /> },
  { path: '/sales-reports', element: <SalesReports /> },
  { path: '/sales-team', element: <SalesTeam /> },
  { path: '/sales/targets', element: <SalesTarget /> },
  { path: '/contract-approval', element: <ContractApproval /> },
  { path: '/business-support', element: <BusinessSupportWorkstation /> },
  { path: '/customers', element: <CustomerList /> },
  { path: '/opportunities', element: <OpportunityBoard /> },
  { path: '/lead-assessment', element: <LeadAssessment /> },
  { path: '/quotations', element: <QuotationList /> },
  { path: '/contracts', element: <ContractList /> },
  { path: '/contracts/:id', element: <ContractDetail /> },
  { path: '/sales-projects', element: <SalesProjectTrack /> },
  { path: '/sales-funnel', element: <SalesFunnel /> },
  { path: '/bidding/:id', element: <BiddingDetail /> },

  // New Sales Module
  { path: '/sales/leads', element: <LeadManagement /> },
  { path: '/sales/opportunities', element: <OpportunityManagement /> },
  { path: '/sales/assessments/:sourceType/:sourceId', element: <TechnicalAssessment /> },
  { path: '/sales/leads/:leadId/requirement', element: <LeadRequirementDetail /> },
  { path: '/sales/:sourceType/:sourceId/open-items', element: <OpenItemsManagement /> },
  { path: '/sales/:sourceType/:sourceId/requirement-freezes', element: <RequirementFreezeManagement /> },
  { path: '/sales/:sourceType/:sourceId/ai-clarifications', element: <AIClarificationChat /> },
  { path: '/sales/quotes', element: <QuoteManagement /> },
  { path: '/sales/quotes/:id/cost', element: <QuoteCostManagement /> },
  { path: '/sales/quotes/:id/cost-analysis', element: <QuoteCostAnalysis /> },
  { path: '/sales/cost-templates', element: <CostTemplateManagement /> },
  { path: '/sales/purchase-material-costs', element: <PurchaseMaterialCostManagement /> },
  { path: '/financial-costs', element: <FinancialCostUpload /> },
  { path: '/sales/contracts', element: <ContractManagement /> },
  { path: '/sales/receivables', element: <ReceivableManagement /> },
  { path: '/sales/statistics', element: <SalesStatistics /> },
  { path: '/sales/templates', element: <SalesTemplateCenter /> },
  { path: '/sales/cpq', element: <CpqConfigurator /> },

  // Pre-sales
  { path: '/presales-dashboard', element: <PresalesWorkstation /> },
  { path: '/presales-manager-dashboard', element: <PresalesManagerWorkstation /> },
  { path: '/presales-tasks', element: <PresalesTasks /> },
  { path: '/solutions', element: <SolutionList /> },
  { path: '/solutions/:id', element: <SolutionDetail /> },
  { path: '/requirement-survey', element: <RequirementSurvey /> },
  { path: '/bidding', element: <BiddingCenter /> },
  { path: '/knowledge-base', element: <KnowledgeBase /> },
]
