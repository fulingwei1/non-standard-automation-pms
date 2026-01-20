import React from 'react';
import { motion } from "framer-motion";
import { ArrowLeft, Share2, Download, Edit, MoreHorizontal, Copy, Send, Archive, Trash2 } from "lucide-react";
import { Button } from "../../../components/ui/button";
import { Badge } from "../../../components/ui/badge";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "../../../components/ui/dropdown-menu";
import { cn } from "../../../lib/utils";
import { fadeIn } from "../../../lib/animations";
import { getStatusStyle } from "../constants";

export function SolutionHeader({ solution, navigate }) {
    const statusStyle = getStatusStyle(solution.status);

    return (
        <motion.div variants={fadeIn} className="flex items-center gap-4">
            <Button
                variant="ghost"
                size="icon"
                onClick={() => navigate("/solutions")}
                className="text-slate-400 hover:text-white"
            >
                <ArrowLeft className="w-5 h-5" />
            </Button>
            <div className="flex-1">
                <div className="flex items-center gap-3 mb-1">
                    <Badge className={cn("text-xs", statusStyle.bg)}>
                        {statusStyle.text}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                        {solution.version}
                    </Badge>
                    <span className="text-sm text-slate-500">{solution.code}</span>
                </div>
                <h1 className="text-2xl font-bold text-white">{solution.name}</h1>
            </div>
            <div className="flex items-center gap-2">
                <Button variant="outline" className="flex items-center gap-2">
                    <Share2 className="w-4 h-4" />
                    分享
                </Button>
                <Button variant="outline" className="flex items-center gap-2">
                    <Download className="w-4 h-4" />
                    导出
                </Button>
                <Button className="flex items-center gap-2">
                    <Edit className="w-4 h-4" />
                    编辑
                </Button>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                            <Copy className="w-4 h-4 mr-2" />
                            复制方案
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                            <Send className="w-4 h-4 mr-2" />
                            提交评审
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>
                            <Archive className="w-4 h-4 mr-2" />
                            归档
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-400">
                            <Trash2 className="w-4 h-4 mr-2" />
                            删除
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </motion.div>
    );
}
