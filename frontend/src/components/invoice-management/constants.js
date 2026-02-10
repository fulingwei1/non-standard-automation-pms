/**
 * Invoice Management Constants - Re-export from shared finance constants
 *
 * ARCHITECTURE NOTE:
 * All invoice/finance constants are defined in lib/constants/finance.js (single source of truth).
 * This file re-exports them so that components/invoice-management/ internal imports still work.
 * Do NOT add new constants here -- add them to lib/constants/finance.js instead.
 */
export {
  statusMap,
 paymentStatusMap,
 statusConfig,
 paymentStatusConfig,
  defaultFormData,
 defaultIssueData,
 defaultPaymentData
} from "../../lib/constants/finance";
