import { lazy } from 'react'

// Customer Service Pages
const CustomerServiceDashboard = lazy(() => import('../pages/CustomerServiceDashboard'))
const ServiceTicketManagement = lazy(() => import('../pages/ServiceTicketManagement'))
const ServiceRecord = lazy(() => import('../pages/ServiceRecord'))
const CustomerCommunication = lazy(() => import('../pages/CustomerCommunication'))
const CustomerSatisfaction = lazy(() => import('../pages/CustomerSatisfaction'))
const ServiceAnalytics = lazy(() => import('../pages/ServiceAnalytics'))
const ServiceKnowledgeBase = lazy(() => import('../pages/ServiceKnowledgeBase'))

export const serviceRoutes = [
  { path: '/customer-service-dashboard', element: <CustomerServiceDashboard /> },
  { path: '/service-tickets', element: <ServiceTicketManagement /> },
  { path: '/service-records', element: <ServiceRecord /> },
  { path: '/customer-communications', element: <CustomerCommunication /> },
  { path: '/customer-satisfaction', element: <CustomerSatisfaction /> },
  { path: '/service-analytics', element: <ServiceAnalytics /> },
  { path: '/service-knowledge-base', element: <ServiceKnowledgeBase /> },
]
