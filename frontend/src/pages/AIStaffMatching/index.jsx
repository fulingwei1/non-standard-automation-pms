// -*- coding: utf-8 -*-
/**
 * AI智能匹配页面
 * 执行AI匹配算法，展示候选人推荐结果，支持采纳/拒绝操作
 */

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Rocket, History } from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader
} from "../../components/ui/card";
import { cn } from "../../lib/utils";
import { staffMatchingApi } from "../../services/api";
import { confirmAction } from "@/lib/confirmAction";
import { PRIORITY_CONFIG } from "./constants";
import StatsCards from "./StatsCards";
import NeedSelector from "./NeedSelector";
import MatchingResults from "./MatchingResults";
import MatchingHistory from "./MatchingHistory";
import RejectDialog from "./RejectDialog";

export default function AIStaffMatching() {
  const [searchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState("matching");
  const [staffingNeeds, setStaffingNeeds] = useState([]);
  const [selectedNeedId, setSelectedNeedId] = useState(null);
  const [matchingResult, setMatchingResult] = useState(null);
  const [matchingHistory, setMatchingHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [matching, setMatching] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [selectedCandidate, setSelectedCandidate] = useState(null);

  // 从URL参数获取需求ID
  useEffect(() => {
    const needId = searchParams.get("need_id");
    if (needId) {
      setSelectedNeedId(parseInt(needId));
    }
  }, [searchParams]);

  const selectedNeed = (staffingNeeds || []).find((n) => n.id === selectedNeedId);

  // 加载人员需求
  const loadStaffingNeeds = useCallback(async () => {
    setLoading(true);
    try {
      const response = await staffMatchingApi.getStaffingNeeds({
        status: "OPEN,MATCHING",
        page_size: 100
      });
      if (response.data?.items) {
        setStaffingNeeds(response.data.items);
      }
    } catch (error) {
      console.error("加载人员需求失败:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载匹配历史
  const loadMatchingHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const response = await staffMatchingApi.getMatchingHistory({
        page_size: 50
      });
      if (response.data?.items) {
        setMatchingHistory(response.data.items);
      }
    } catch (error) {
      console.error("加载匹配历史失败:", error);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStaffingNeeds();
    loadMatchingHistory();
  }, [loadStaffingNeeds, loadMatchingHistory]);

  // 执行AI匹配
  const handleExecuteMatching = async () => {
    if (!selectedNeed) {return;}

    setMatching(true);
    try {
      const response = await staffMatchingApi.executeMatching(selectedNeed.id, {
        top_n: 10
      });
      if (response.data) {
        setMatchingResult(response.data);
      } else {
        setMatchingResult({
          request_id: "",
          total_candidates: 0,
          qualified_count: 0,
          candidates: [],
          staffing_need_id: selectedNeed.id,
          project_name: selectedNeed.project_name,
          role_name: selectedNeed.role_name,
          priority: selectedNeed.priority,
          priority_threshold: PRIORITY_CONFIG[selectedNeed.priority]?.threshold || 65
        });
      }
    } catch (error) {
      console.error("匹配失败:", error);
      alert("匹配失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setMatching(false);
    }
  };

  // 采纳候选人
  const handleAccept = async (candidate) => {
    if (
      !await confirmAction(
        `确定要采纳 ${candidate.employee_name} 作为该职位的候选人吗？`
      ))
    {return;}

    try {
      await staffMatchingApi.acceptCandidate({
        matching_log_id: candidate.matching_log_id || 1,
        staffing_need_id: matchingResult.staffing_need_id,
        employee_id: candidate.employee_id
      });
      loadStaffingNeeds();
      loadMatchingHistory();
      setMatchingResult((prev) => ({
        ...prev,
        candidates: (prev.candidates || []).filter(
          (c) => c.employee_id !== candidate.employee_id
        )
      }));
    } catch (error) {
      console.error("采纳失败:", error);
      // 演示模式下也移除候选人
      setMatchingResult((prev) => ({
        ...prev,
        candidates: (prev.candidates || []).filter(
          (c) => c.employee_id !== candidate.employee_id
        )
      }));
    }
  };

  // 拒绝候选人
  const handleReject = (candidate) => {
    setSelectedCandidate(candidate);
    setRejectReason("");
    setShowRejectDialog(true);
  };

  const confirmReject = async () => {
    if (!rejectReason.trim()) {return;}

    try {
      await staffMatchingApi.rejectCandidate({
        matching_log_id: selectedCandidate.matching_log_id || 1,
        reject_reason: rejectReason
      });
      loadMatchingHistory();
    } catch (error) {
      console.error("拒绝失败:", error);
    }
    setShowRejectDialog(false);
  };

  // 统计数据
  const stats = {
    openNeeds: (staffingNeeds || []).filter((n) => n.status === "OPEN").length,
    matchingNeeds: (staffingNeeds || []).filter((n) => n.status === "MATCHING").length,
    acceptedCount: (matchingHistory || []).filter((h) => h.is_accepted === true).length,
    totalMatches: matchingHistory.length
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="AI智能人员匹配"
        description="基于6维加权评分算法，智能推荐最优候选人" />

      {/* 统计卡片 */}
      <StatsCards stats={stats} />

      {/* Tab 切换 */}
      <Card>
        <CardHeader className="border-b border-white/10 pb-0">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab("matching")}
              className={cn(
                "flex items-center gap-2 px-4 py-3 border-b-2 transition-colors",
                activeTab === "matching" ?
                  "border-primary text-primary" :
                  "border-transparent text-slate-400 hover:text-slate-300"
              )}>
              <Rocket className="h-4 w-4" />
              执行匹配
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={cn(
                "flex items-center gap-2 px-4 py-3 border-b-2 transition-colors",
                activeTab === "history" ?
                  "border-primary text-primary" :
                  "border-transparent text-slate-400 hover:text-slate-300"
              )}>
              <History className="h-4 w-4" />
              匹配历史
            </button>
          </div>
        </CardHeader>

        <CardContent className="pt-6">
          <AnimatePresence mode="wait">
            {activeTab === "matching" ?
              <motion.div
                key="matching"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}>
                <div className="grid grid-cols-12 gap-6">
                  {/* 左侧：需求选择 */}
                  <NeedSelector
                    staffingNeeds={staffingNeeds}
                    selectedNeedId={selectedNeedId}
                    setSelectedNeedId={setSelectedNeedId}
                    selectedNeed={selectedNeed}
                    loading={loading}
                    matching={matching}
                    loadStaffingNeeds={loadStaffingNeeds}
                    setMatchingResult={setMatchingResult}
                    handleExecuteMatching={handleExecuteMatching}
                  />

                  {/* 右侧：匹配结果 */}
                  <MatchingResults
                    matching={matching}
                    matchingResult={matchingResult}
                    onAccept={handleAccept}
                    onReject={handleReject}
                  />
                </div>
              </motion.div> :

              <MatchingHistory
                matchingHistory={matchingHistory}
                historyLoading={historyLoading}
                loadMatchingHistory={loadMatchingHistory}
              />
            }
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* 拒绝原因对话框 */}
      <RejectDialog
        open={showRejectDialog}
        onOpenChange={setShowRejectDialog}
        selectedCandidate={selectedCandidate}
        rejectReason={rejectReason}
        setRejectReason={setRejectReason}
        onConfirm={confirmReject}
      />
    </div>
  );
}
