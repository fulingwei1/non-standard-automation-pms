import { Navigate, useLocation } from "react-router-dom";

export function buildPresalesCenterSearch(tab, search) {
  const currentParams = new URLSearchParams(search || "");
  const nextParams = new URLSearchParams();

  nextParams.set("tab", tab);
  currentParams.forEach((value, key) => {
    if (key !== "tab") {
      nextParams.append(key, value);
    }
  });

  return `?${nextParams.toString()}`;
}

export function PresalesCenterRedirect({ tab }) {
  const location = useLocation();
  const browserSearch =
    typeof window !== "undefined" && window.location.pathname === location.pathname
      ? window.location.search
      : "";
  const search = buildPresalesCenterSearch(tab, location.search || browserSearch);

  return (
    <Navigate
      to={{ pathname: "/presales/technical-solutions", search }}
      replace
    />
  );
}
