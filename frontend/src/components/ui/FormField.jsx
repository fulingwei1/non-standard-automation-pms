import { forwardRef } from "react";
import { cn } from "../../lib/utils";
import { Input } from "./input";
import { Label } from "./label";
import { AlertCircle } from "lucide-react";

/**
 * Form field component with label, input, and error message
 */
export const FormField = forwardRef(
  (
    { label, name, error, touched, required, className, children, ...props },
    ref,
  ) => {
    const showError = touched && error;

    return (
      <div className={cn("space-y-2", className)}>
        {label && (
          <Label
            htmlFor={name}
            className={cn(
              required && 'after:content-["*"] after:text-red-400 after:ml-1',
            )}
          >
            {label}
          </Label>
        )}
        {children ? (
          children
        ) : (
          <Input
            ref={ref}
            id={name}
            name={name}
            className={cn(
              showError &&
                "border-red-500 focus:border-red-500 focus:ring-red-500",
            )}
            aria-invalid={showError}
            aria-describedby={showError ? `${name}-error` : undefined}
            {...props}
          />
        )}
        {showError && (
          <div
            id={`${name}-error`}
            className="flex items-center gap-1.5 text-sm text-red-400"
            role="alert"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  },
);

FormField.displayName = "FormField";

/**
 * Form field for textarea
 */
export const FormTextarea = forwardRef(
  ({ label, name, error, touched, required, className, ...props }, ref) => {
    const showError = touched && error;

    return (
      <div className={cn("space-y-2", className)}>
        {label && (
          <Label
            htmlFor={name}
            className={cn(
              required && 'after:content-["*"] after:text-red-400 after:ml-1',
            )}
          >
            {label}
          </Label>
        )}
        <textarea
          ref={ref}
          id={name}
          name={name}
          className={cn(
            "flex min-h-[80px] w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2",
            "text-sm text-white placeholder:text-slate-500",
            "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-slate-950",
            "disabled:cursor-not-allowed disabled:opacity-50",
            showError &&
              "border-red-500 focus:border-red-500 focus:ring-red-500",
          )}
          aria-invalid={showError}
          aria-describedby={showError ? `${name}-error` : undefined}
          {...props}
        />
        {showError && (
          <div
            id={`${name}-error`}
            className="flex items-center gap-1.5 text-sm text-red-400"
            role="alert"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  },
);

FormTextarea.displayName = "FormTextarea";

/**
 * Form field for select
 */
export const FormSelect = forwardRef(
  (
    { label, name, error, touched, required, className, children, ...props },
    ref,
  ) => {
    const showError = touched && error;

    return (
      <div className={cn("space-y-2", className)}>
        {label && (
          <Label
            htmlFor={name}
            className={cn(
              required && 'after:content-["*"] after:text-red-400 after:ml-1',
            )}
          >
            {label}
          </Label>
        )}
        <select
          ref={ref}
          id={name}
          name={name}
          className={cn(
            "flex h-10 w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2",
            "text-sm text-white",
            "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-slate-950",
            "disabled:cursor-not-allowed disabled:opacity-50",
            showError &&
              "border-red-500 focus:border-red-500 focus:ring-red-500",
          )}
          aria-invalid={showError}
          aria-describedby={showError ? `${name}-error` : undefined}
          {...props}
        >
          {children}
        </select>
        {showError && (
          <div
            id={`${name}-error`}
            className="flex items-center gap-1.5 text-sm text-red-400"
            role="alert"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  },
);

FormSelect.displayName = "FormSelect";
