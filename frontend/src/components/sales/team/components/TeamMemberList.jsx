/**
 * TeamMemberList - 团队成员列表组件
 * 管理和渲染团队成员卡片列表
 */

import { motion } from "framer-motion";
import { Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../../ui";
import TeamMemberCard from "./TeamMemberCard";

export default function TeamMemberList({
  loading,
  members,
  onViewDetail,
  onNavigatePerformance,
  onNavigateCRM,
}) {
  return (
    <motion.div variants={{ hidden: { opacity: 0 }, visible: { opacity: 1 } }}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-400" />
            团队成员 ({members.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-10 text-slate-400">加载中...</div>
          ) : members.length === 0 ? (
            <div className="text-center py-10 text-slate-500">
              暂无团队成员
            </div>
          ) : (
            <div className="space-y-4">
              {members.map((member, index) => (
                <TeamMemberCard
                  key={member.id}
                  member={member}
                  index={index}
                  onViewDetail={onViewDetail}
                  onNavigatePerformance={onNavigatePerformance}
                  onNavigateCRM={onNavigateCRM}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
