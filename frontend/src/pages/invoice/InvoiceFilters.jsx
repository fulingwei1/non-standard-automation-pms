/**
 * InvoiceFilters - Page-level re-export
 *
 * ARCHITECTURE NOTE:
 * The authoritative implementation lives in components/invoice-management/InvoiceFilters.jsx.
 * This file re-exports it for backward compatibility with pages/invoice/ imports.
 * The component accepts both prop naming conventions (see source for details).
 *
 * @deprecated Import from components/invoice-management/InvoiceFilters instead.
 */
export { default } from "../../components/invoice-management/InvoiceFilters";
