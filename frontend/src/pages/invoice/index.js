/**
 * Invoice Page - Barrel exports
 *
 * ARCHITECTURE NOTE:
 * This is the page-level entry point for the invoice management feature.
 * The page is composed in InvoiceManagement.jsx which orchestrates:
 * - Reusable UI components from components/invoice-management/
 * - Page-specific business logic (API calls, state, routing)
 * - Shared constants from lib/constants/finance.js
 *
 * The sub-component re-exports below exist for backward compatibility.
 * New code should import directly from components/invoice-management/.
 */
export { default } from "./InvoiceManagement";
export { default as InvoiceRow } from "./InvoiceRow";
export { default as InvoiceStats } from "./InvoiceStats";
export { default as InvoiceFilters } from "./InvoiceFilters";
export * from "./constants";
