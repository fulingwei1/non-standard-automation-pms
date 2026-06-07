import * as Router from "react-router-dom";

const CONTEXT_PARAM_ALIASES = {
  leadId: "lead_id",
  opportunityId: "opportunity_id",
  ticketId: "ticket_id",
  projectId: "project_id",
  contractId: "contract_id",
};

export function buildPresalesCenterSearch(tab, search) {
  const currentParams = new URLSearchParams(search || "");
  const nextParams = new URLSearchParams();

  nextParams.set("tab", tab);
  currentParams.forEach((value, key) => {
    if (key !== "tab") {
      const nextKey = CONTEXT_PARAM_ALIASES[key] || key;
      if (nextKey !== key && nextParams.has(nextKey)) {
        return;
      }
      nextParams.append(nextKey, value);
    }
  });

  return `?${nextParams.toString()}`;
}

export function PresalesCenterRedirect({ tab }) {
  const location = Router.useLocation();
  const browserSearch =
    typeof window !== "undefined" && window.location.pathname === location.pathname
      ? window.location.search
      : "";
  const search = buildPresalesCenterSearch(tab, location.search || browserSearch);

  return (
    <Router.Navigate
      to={{ pathname: "/presales/technical-solutions", search }}
      replace
    />
  );
}
