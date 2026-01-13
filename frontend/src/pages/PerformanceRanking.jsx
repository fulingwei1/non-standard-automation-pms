/**
 * Performance Ranking - 绩效排行榜
 * Features: 员工排名、部门排名、历史趋势
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Award,
  TrendingUp,
  TrendingDown,
  Users,
  Building2,
  Calendar,
  Medal,
  Loader2,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { performanceApi, pmoApi } from "../services/api";

export default function PerformanceRanking() {
  const [selectedPeriod, setSelectedPeriod] = useState("current");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [employeeRanking, setEmployeeRanking] = useState([]);
  const [departmentRanking, setDepartmentRanking] = useState([]);

  // Fetch ranking data
  useEffect(() => {
    const fetchRankings = async () => {
      setLoading(true);
      setError(null);
      try {
        const myPerfRes = await performanceApi.getMyPerformance();
        if (myPerfRes.data) {
          setEmployeeRanking(myPerfRes.data.employee_ranking || []);
          setDepartmentRanking(myPerfRes.data.department_ranking || []);
        }
      } catch (err) {
        console.error("Failed to load performance ranking:", err);
        setError("加载绩效排名失败");
      } finally {
        setLoading(false);
      }
    };
    fetchRankings();
  }, []);

  const getRankBadge = (rank) => {
    if (rank === 1) return <Medal className="w-6 h-6 text-amber-400" />;
    if (rank === 2) return <Medal className="w-6 h-6 text-slate-300" />;
    if (rank === 3) return <Medal className="w-6 h-6 text-orange-400" />;
    return <span className="text-slate-400 font-bold">#{rank}</span>;
  };

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader title="绩效排行榜" description="员工绩效排名、部门绩效对比" />

      <Tabs defaultValue="employee" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="employee">
            <Users className="w-4 h-4 mr-2" />
            员工排名
          </TabsTrigger>
          <TabsTrigger value="department">
            <Building2 className="w-4 h-4 mr-2" />
            部门排名
          </TabsTrigger>
        </TabsList>

        <TabsContent value="employee" className="space-y-4 mt-6">
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="h-5 w-5 text-amber-400" />
                员工绩效排行榜 TOP 10
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                </div>
              ) : (
                <div className="space-y-3">
                  {employeeRanking.map((employee) => (
                    <motion.div
                      key={employee.rank}
                      variants={fadeIn}
                      className={cn(
                        "flex items-center justify-between p-4 rounded-lg border transition-all",
                        employee.rank <= 3
                          ? "bg-gradient-to-r from-amber-500/10 to-transparent border-amber-500/30"
                          : "bg-slate-800/40 border-slate-700/50 hover:border-slate-600/80",
                      )}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 flex items-center justify-center">
                          {getRankBadge(employee.rank)}
                        </div>
                        <div>
                          <p className="font-medium text-white">
                            {employee.name}
                          </p>
                          <p className="text-xs text-slate-400">
                            {employee.department}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <div className="text-2xl font-bold text-white">
                            {employee.score}
                          </div>
                          <div className="text-xs text-slate-400">绩效分数</div>
                        </div>
                        {employee.change !== 0 && (
                          <div className="w-16 flex items-center justify-center">
                            {employee.change > 0 ? (
                              <div className="flex items-center gap-1 text-emerald-400">
                                <TrendingUp className="w-4 h-4" />
                                <span className="text-sm">
                                  +{employee.change}
                                </span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-1 text-red-400">
                                <TrendingDown className="w-4 h-4" />
                                <span className="text-sm">
                                  {employee.change}
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="department" className="space-y-4 mt-6">
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-blue-400" />
                部门绩效排行榜
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                </div>
              ) : (
                <div className="space-y-3">
                  {departmentRanking.map((dept) => (
                    <motion.div
                      key={dept.rank}
                      variants={fadeIn}
                      className={cn(
                        "flex items-center justify-between p-4 rounded-lg border transition-all",
                        dept.rank === 1
                          ? "bg-gradient-to-r from-amber-500/10 to-transparent border-amber-500/30"
                          : "bg-slate-800/40 border-slate-700/50 hover:border-slate-600/80",
                      )}
                    >
                      <div className="flex items-center gap-4">
                        <div className="w-12 flex items-center justify-center">
                          {getRankBadge(dept.rank)}
                        </div>
                        <div>
                          <p className="font-medium text-white">{dept.name}</p>
                          <p className="text-xs text-slate-400">
                            {dept.employees} 人 · 优秀 {dept.excellent} 人
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-white">
                          {dept.avgScore}
                        </div>
                        <div className="text-xs text-slate-400">平均分数</div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
