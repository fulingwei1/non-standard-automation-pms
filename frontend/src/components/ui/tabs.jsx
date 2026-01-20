import React, { createContext, useContext } from "react";
import { cn } from "../../lib/utils";

const TabsContext = createContext(null);

export function Tabs({ value, onValueChange, children, className }) {
  return (
    <TabsContext.Provider value={{ value, onValueChange }}>
      <div className={cn("w-full", className)}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ children, className }) {
  return (
    <div
      className={cn(
        "inline-flex h-10 items-center justify-center rounded-lg bg-surface-100 p-1 text-slate-400",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function TabsTrigger({ value, children, className }) {
  const { value: selectedValue, onValueChange } = useContext(TabsContext);
  const isActive = selectedValue === value;

  return (
    <button
      onClick={() => onValueChange(value)}
      className={cn(
        "inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        isActive
          ? "bg-surface-50 text-white shadow-sm"
          : "text-slate-400 hover:text-white",
        className,
      )}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, children, className }) {
  const { value: selectedValue } = useContext(TabsContext);

  if (selectedValue !== value) {return null;}

  return <div className={cn("mt-6", className)}>{children}</div>;
}
