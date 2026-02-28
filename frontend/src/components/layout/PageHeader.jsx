import { cn } from "../../lib/utils";
import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "../ui/button";

export function PageHeader({
  title,
  description,
  breadcrumbs,
  actions,
  action,
  className,
}) {
  const resolvedActions = [];

  const appendAction = (item, index) => {
    if (!item) {return;}
    // React element
    if (item?.$$typeof) {
      resolvedActions.push(
        <div key={`page-header-action-${index}`} className="flex items-center">
          {item}
        </div>,
      );
      return;
    }

    // Plain config object
    const {
      label,
      icon: Icon,
      onClick,
      href,
      to,
      variant = "default",
      className: actionClassName,
      disabled,
    } = item;
    if (!label && !Icon) {
      return;
    }

    const button = (
      <Button
        key={`page-header-action-${index}`}
        onClick={onClick}
        variant={variant}
        className={cn("gap-2", actionClassName)}
        disabled={disabled}
      >
        {Icon && <Icon className="h-4 w-4" />}
        {label}
      </Button>
    );

    if (href || to) {
      resolvedActions.push(
        <Link key={`page-header-action-link-${index}`} to={to || href}>
          {button}
        </Link>,
      );
    } else {
      resolvedActions.push(button);
    }
  };

  if (Array.isArray(actions)) {
    (actions || []).forEach((act, idx) => appendAction(act, idx));
  } else if (actions) {
    appendAction(actions, 0);
  } else if (Array.isArray(action)) {
    (action || []).forEach((act, idx) => appendAction(act, idx));
  } else if (action) {
    appendAction(action, 0);
  }

  return (
    <div className={cn("mb-8", className)}>
      {/* Breadcrumbs */}
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav className="flex items-center gap-1 text-sm mb-4">
          {(breadcrumbs || []).map((crumb, index) => (
            <div key={index} className="flex items-center gap-1">
              {index > 0 && <ChevronRight className="h-4 w-4 text-slate-600" />}
              {crumb.href ? (
                <Link
                  to={crumb.href}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  {crumb.label}
                </Link>
              ) : (
                <span className="text-white">{crumb.label}</span>
              )}
            </div>
          ))}
        </nav>
      )}

      {/* Title and Actions */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">
            {title}
          </h1>
          {description && (
            <p className="mt-1 text-sm text-slate-400">{description}</p>
          )}
        </div>
        {resolvedActions.length > 0 && (
          <div className="flex items-center gap-3">{resolvedActions}</div>
        )}
      </div>
    </div>
  );
}

export default PageHeader;
