// -*- coding: utf-8 -*-
import { RefreshCw, Rocket } from "lucide-react";
import {
  Card,
  CardContent
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { cn } from "../../lib/utils";
import { PRIORITY_CONFIG } from "./constants";

export default function NeedSelector({
  staffingNeeds,
  selectedNeedId,
  setSelectedNeedId,
  selectedNeed,
  loading,
  matching,
  loadStaffingNeeds,
  setMatchingResult,
  handleExecuteMatching
}) {
  return (
    <div className="col-span-4 space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-300">
          选择人员需求
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={loadStaffingNeeds}>
          <RefreshCw
            className={cn("h-4 w-4", loading && "animate-spin")} />
        </Button>
      </div>

      <select
        value={selectedNeedId || ""}
        onChange={(e) => {
          setSelectedNeedId(
            e.target.value ? parseInt(e.target.value) : null
          );
          setMatchingResult(null);
        }}
        className="w-full h-10 px-3 rounded-md border border-white/10 bg-white/5 text-sm">
        <option value="">选择需求...</option>
        {(staffingNeeds || []).map((need) =>
          <option key={need.id} value={need.id}>
            {need.project_name} - {need.role_name} (
            {need.priority})
          </option>
        )}
      </select>

      {selectedNeed &&
        <Card className="border-white/10">
          <CardContent className="pt-4 space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">项目</span>
              <span className="text-white">
                {selectedNeed.project_name}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">角色</span>
              <span className="text-white">
                {selectedNeed.role_name}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">需求人数</span>
              <span className="text-white">
                {selectedNeed.headcount} 人
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">已满足</span>
              <span className="text-white">
                {selectedNeed.filled_count || 0} 人
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">优先级</span>
              <Badge
                className={cn(
                  PRIORITY_CONFIG[selectedNeed.priority]?.
                    color === "red" &&
                    "bg-red-500/20 text-red-400",
                  PRIORITY_CONFIG[selectedNeed.priority]?.
                    color === "orange" &&
                    "bg-orange-500/20 text-orange-400",
                  PRIORITY_CONFIG[selectedNeed.priority]?.
                    color === "blue" &&
                    "bg-blue-500/20 text-blue-400",
                  PRIORITY_CONFIG[selectedNeed.priority]?.
                    color === "green" &&
                    "bg-green-500/20 text-green-400"
                )}>
                {PRIORITY_CONFIG[selectedNeed.priority]?.text}
              </Badge>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">最低分要求</span>
              <span className="text-primary font-medium">
                {
                  PRIORITY_CONFIG[selectedNeed.priority]?.
                    threshold
                }{" "}
                分
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">投入比例</span>
              <span className="text-white">
                {selectedNeed.allocation_pct}%
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">时间范围</span>
              <span className="text-white text-xs">
                {selectedNeed.start_date} ~{" "}
                {selectedNeed.end_date}
              </span>
            </div>
            {selectedNeed.required_skills?.length > 0 &&
              <div>
                <span className="text-slate-400">技能要求</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {(selectedNeed.required_skills || []).map(
                    (skill, idx) =>
                      <Badge
                        key={idx}
                        variant="secondary"
                        className="text-xs">
                        {skill.tag_name} ≥{skill.min_score}
                      </Badge>
                  )}
                </div>
              </div>
            }
          </CardContent>
        </Card>
      }

      <Button
        className="w-full"
        size="lg"
        onClick={handleExecuteMatching}
        disabled={!selectedNeed || matching}>
        {matching ?
          <>
            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            正在匹配...
          </> :
          <>
            <Rocket className="h-4 w-4 mr-2" />
            执行AI智能匹配
          </>
        }
      </Button>
    </div>
  );
}
