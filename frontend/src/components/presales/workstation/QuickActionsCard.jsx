import React from "react";
import { Link } from "react-router-dom";
import { Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";
import { cn } from "../../../lib/utils";

export default function QuickActionsCard({ actions }) {
  return (
    <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-400" />
          快捷操作
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3">
        {(actions || []).map((action) => (
          <Link key={action.name} to={action.path}>
            <div
              className={cn(
                "p-3 rounded-lg bg-gradient-to-br cursor-pointer",
                "hover:scale-105 transition-transform",
                action.color
              )}
            >
              <action.icon className="w-5 h-5 text-white mb-2"  />
              <p className="text-sm font-medium text-white">{action.name}</p>
            </div>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
