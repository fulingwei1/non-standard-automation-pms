import * as React from "react";
import { cn } from "../../lib/utils";

const Slider = React.forwardRef(
  (
    {
      className,
      value,
      defaultValue,
      min = 0,
      max = 100,
      step = 1,
      disabled,
      onChange,
      onValueChange,
      ...props
    },
    ref,
  ) => {
    const isControlled = value !== undefined;
    const [internalValue, setInternalValue] = React.useState(
      Array.isArray(defaultValue) ? defaultValue[0] : defaultValue ?? min,
    );

    const resolvedValue = isControlled
      ? Array.isArray(value)
        ? value[0]
        : value
      : internalValue;

    const handleChange = (event) => {
      const next = Number(event.target.value);
      if (!isControlled) {
        setInternalValue(next);
      }
      onValueChange?.([next]);
      onChange?.(event);
    };

    return (
      <div className={cn("flex w-full items-center", className)}>
        <input
          ref={ref}
          type="range"
          min={min}
          max={max}
          step={step}
          disabled={disabled}
          value={resolvedValue ?? min}
          onChange={handleChange}
          className={cn(
            "h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-700/60",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
          {...props}
        />
      </div>
    );
  },
);
Slider.displayName = "Slider";

export { Slider };

