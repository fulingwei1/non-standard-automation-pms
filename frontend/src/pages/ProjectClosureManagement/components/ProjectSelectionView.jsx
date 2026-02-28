import React from "react";
import { motion } from "framer-motion";
import { Search, ArrowRight } from "lucide-react";
import { PageHeader } from "../../../components/layout/PageHeader";
import { Card, CardContent, Input } from "../../../components/ui";
import { staggerContainer } from "../../../lib/animations";

export function ProjectSelectionView({
    projectSearch,
    setProjectSearch,
    projectList,
    onSelectProject
}) {
    return (
        <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
        >
            <PageHeader title="项目结项管理" description="选择项目以进行结项管理" />

            <Card className="max-w-2xl mx-auto">
                <CardContent className="p-6">
                    <div className="mb-4">
                        <Input
                            placeholder="搜索项目名称或编码..."
                            value={projectSearch}
                            onChange={(e) => setProjectSearch(e.target.value)}
                            className="w-full"
                            icon={Search}
                        />
                    </div>

                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {(projectList || []).map((proj) => (
                            <div
                                key={proj.id}
                                onClick={() => onSelectProject(proj.id)}
                                className="p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.06] hover:border-white/10 cursor-pointer transition-all"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="font-medium text-white">
                                            {proj.project_name}
                                        </h3>
                                        <p className="text-sm text-slate-400">
                                            {proj.project_code}
                                        </p>
                                    </div>
                                    <ArrowRight className="h-5 w-5 text-slate-500" />
                                </div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}
