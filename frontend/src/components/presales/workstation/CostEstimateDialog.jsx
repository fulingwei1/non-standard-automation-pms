import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Calculator, X } from "lucide-react";
import { Button } from "../../ui/button";
import CostEstimateForm from "../CostEstimateForm";

export default function CostEstimateDialog({
  isOpen,
  task,
  onClose,
  onSave,
}) {
  return (
    <AnimatePresence>
      {isOpen && task && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-surface-100 rounded-xl border border-white/10 shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col"
          >
            <div className="flex items-center justify-between p-4 border-b border-white/5">
              <div>
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Calculator className="w-5 h-5 text-primary" />
                  成本估算
                </h3>
                <p className="text-sm text-slate-400 mt-1">{task.title}</p>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="w-5 h-5 text-slate-400" />
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
              <CostEstimateForm
                bidding={{
                  id: task.biddingId,
                  name: task.title,
                  amount: 120,
                }}
                onSave={onSave}
                onCancel={onClose}
              />
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
