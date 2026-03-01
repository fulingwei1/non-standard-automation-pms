import * as React from "react";

import { cn } from "../../lib/utils";

const RadioGroupContext = React.createContext(null);

const RadioGroup = React.forwardRef(
  (
    { className, value, defaultValue, onValueChange, disabled = false, ...props },
    ref,
  ) => {
    const generatedName = React.useId();
    const [uncontrolledValue, setUncontrolledValue] = React.useState(
      defaultValue ?? "",
    );

    const isControlled = value !== undefined;
    const currentValue = isControlled ? value : uncontrolledValue;

    const handleChange = (nextValue) => {
      if (!isControlled) {setUncontrolledValue(nextValue);}
      onValueChange?.(nextValue);
    };

    return (
      <RadioGroupContext.Provider
        value={{
          name: generatedName,
          value: currentValue,
          onValueChange: handleChange,
          disabled,
        }}
      >
        <div
          ref={ref}
          role="radiogroup"
          className={cn("grid gap-2", className)}
          {...props}
        />
      </RadioGroupContext.Provider>
    );
  },
);
RadioGroup.displayName = "RadioGroup";

const RadioGroupItem = React.forwardRef(
  ({ className, value, id, disabled: itemDisabled = false, ...props }, ref) => {
    const ctx = React.useContext(RadioGroupContext);
    if (!ctx) {
      throw new Error("RadioGroupItem must be used within a RadioGroup");
    }

    const disabled = ctx.disabled || itemDisabled;
    const checked = String(ctx.value) === String(value);

    return (
      <div className="relative flex h-4 w-4 items-center justify-center">
        <input
          ref={ref}
          id={id}
          type="radio"
          name={ctx.name}
          value={value || "unknown"}
          checked={checked}
          disabled={disabled}
          onChange={() => ctx.onValueChange?.(String(value))}
          className="peer sr-only"
          {...props}
        />
        <div
          className={cn(
            "h-4 w-4 rounded-full border border-slate-300 ring-offset-white peer-focus-visible:outline-none peer-focus-visible:ring-2 peer-focus-visible:ring-slate-950 peer-focus-visible:ring-offset-2 peer-disabled:cursor-not-allowed peer-disabled:opacity-50 dark:border-slate-800 dark:ring-offset-slate-950 dark:peer-focus-visible:ring-slate-300",
            className,
          )}
        >
          <div
            className={cn(
              "mx-auto my-auto h-2 w-2 rounded-full bg-slate-900 opacity-0 transition-opacity dark:bg-slate-50",
              checked && "opacity-100",
            )}
          />
        </div>
      </div>
    );
  },
);
RadioGroupItem.displayName = "RadioGroupItem";

export { RadioGroup, RadioGroupItem };

