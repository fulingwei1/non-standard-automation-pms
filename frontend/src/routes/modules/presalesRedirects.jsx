import * as Router from "react-router-dom";

const CONTEXT_PARAM_ALIASES = {
  leadId: "lead_id",
  opportunityId: "opportunity_id",
  ticketId: "ticket_id",
  projectId: "project_id",
  contractId: "contract_id",
};

function copyNormalizedSearchParams(search, initialParams = {}) {
  const currentParams = new URLSearchParams(search || "");
  const nextParams = new URLSearchParams();

  Object.entries(initialParams).forEach(([key, value]) => {
    nextParams.set(key, value);
  });

  currentParams.forEach((value, key) => {
    if (key in initialParams) {
      return;
    }

    const nextKey = CONTEXT_PARAM_ALIASES[key] || key;
    if (nextKey !== key && nextParams.has(nextKey)) {
      return;
    }
    nextParams.append(nextKey, value);
  });

  const nextSearch = nextParams.toString();
  return nextSearch ? `?${nextSearch}` : "";
}

export function buildPresalesCenterSearch(tab, search) {
  return copyNormalizedSearchParams(search, { tab });
}

export function buildPresalesWorkbenchSearch(search) {
  return copyNormalizedSearchParams(search);
}

function getRedirectSearch(location) {
  const browserSearch =
    typeof window !== "undefined" && window.location.pathname === location.pathname
      ? window.location.search
      : "";
  return location.search || browserSearch;
}

export function PresalesCenterRedirect({ tab }) {
  const location = Router.useLocation();
  const search = buildPresalesCenterSearch(tab, getRedirectSearch(location));

  return (
    <Router.Navigate
      to={{ pathname: "/presales/technical-solutions", search }}
      replace
    />
  );
}

export function PresalesWorkbenchRedirect() {
  const location = Router.useLocation();
  const search = buildPresalesWorkbenchSearch(getRedirectSearch(location));

  return (
    <Router.Navigate
      to={{ pathname: "/presales/workbench", search }}
      replace
    />
  );
}
