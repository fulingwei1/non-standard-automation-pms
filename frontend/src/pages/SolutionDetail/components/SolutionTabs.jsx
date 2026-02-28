import React from 'react';
import { motion } from "framer-motion";
import { Button } from "../../../components/ui/button";
import { fadeIn } from "../../../lib/animations";
import { TABS } from "../constants";

export function SolutionTabs({ activeTab, setActiveTab }) {
    return (
        <motion.div variants={fadeIn}>
            <div className="flex overflow-x-auto custom-scrollbar pb-2 gap-1 border-b border-white/5">
                {TABS.map((tab) => (
                    <Button
                        key={tab.id}
                        variant={activeTab === tab.id ? "default" : "ghost"}
                        size="sm"
                        onClick={() => setActiveTab(tab.id)}
                        className="flex items-center gap-2 whitespace-nowrap"
                    >
                        {(() => { const DynIcon = tab.icon; return <DynIcon className="w-4 h-4"  />; })()}
                        {tab.name}
                    </Button>
                ))}
            </div>
        </motion.div>
    );
}
