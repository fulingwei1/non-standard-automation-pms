import { usePermission } from "../hooks/usePermission";

export default function PresalesWorkbenchRedirect() {
  const { hasPermission, isLoading, isSuperuser } = usePermission();

  if (isLoading) {
    return null;
  }

  if (isSuperuser || hasPermission("presales:task:manage")) {
    return <Navigate to="/presales-manager-dashboard" replace />;
  }

  return <Navigate to="/presales-dashboard" replace />;
}
