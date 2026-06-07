import { Navigate, useLocation } from "react-router-dom";

export function buildProjectManagementCenterSearch(tab, search, targetParams = {}) {
  const currentParams = new URLSearchParams(search || "");
  const nextParams = new URLSearchParams();
  const normalizedTargetParams = targetParams || {};

  nextParams.set("tab", tab);

  Object.entries(normalizedTargetParams).forEach(([key, value]) => {
    if (key !== "tab" && value !== undefined && value !== null && value !== "") {
      nextParams.set(key, value);
    }
  });

  currentParams.forEach((value, key) => {
    if (key !== "tab" && !Object.prototype.hasOwnProperty.call(normalizedTargetParams, key)) {
      nextParams.append(key, value);
    }
  });

  return `?${nextParams.toString()}`;
}

export function ProjectManagementCenterRedirect({ tab, params }) {
  const location = useLocation();
  const browserSearch =
    typeof window !== "undefined" && window.location.pathname === location.pathname
      ? window.location.search
      : "";
  const search = buildProjectManagementCenterSearch(
    tab,
    location.search || browserSearch,
    params,
  );

  return (
    <Navigate
      to={{ pathname: "/project/management-center", search }}
      replace
    />
  );
}
