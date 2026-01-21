import React from 'react';
import { cn } from "../../../lib/utils";
import { STATUS_TABS } from "../constants";

export function EmployeeStatusTabs({ activeStatusTab, setActiveStatusTab }) {
    return (
        <div className="flex items-center gap-2 flex-wrap">
            {STATUS_TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeStatusTab === tab.key;
                return (
                    <button
                        key={tab.key}
                        onClick={() => setActiveStatusTab(tab.key)}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-lg border transition-all",
                            isActive
                                ? `${tab.bgColor} border-current ${tab.color}`
                                : "border-white/10 text-slate-400 hover:bg-white/5 hover:text-white",
                        )}
                    >
                        <Icon className="h-4 w-4" />
                        <span className="font-medium">{tab.label}</span>
                    </button>
                );
            })}
        </div>
    );
}
