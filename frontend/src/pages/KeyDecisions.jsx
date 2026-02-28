import { motion } from "framer-motion";
import { Crown } from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent } from
"../components/ui/card";
import { fadeIn } from "../lib/animations";

export default function KeyDecisions() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader title="决策事项" />
      <div className="container mx-auto px-4 py-6">
        <motion.div variants={fadeIn} initial="hidden" animate="visible">
          <Card>
            <CardContent className="p-12 text-center">
              <Crown className="w-16 h-16 text-slate-500 mx-auto mb-4" />
              <p className="text-slate-400">决策事项功能开发中...</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>);

}