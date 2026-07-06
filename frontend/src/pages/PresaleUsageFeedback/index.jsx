// 售前智能体使用反馈页面
import { useState, useEffect } from "react";
import {
  Star, Send, BarChart3, CheckCircle, XCircle, Clock,
  ThumbsUp, ThumbsDown, MessageSquare, TrendingUp,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card, CardContent, CardHeader, CardTitle,
  Button, Input, Textarea, Select,
  Badge, Progress, Alert, AlertDescription,
} from "../../components/ui";
import {
  submitUsageFeedback, listUsageFeedback, usageFeedbackStats,
} from "../../services/api/presaleUsageFeedback";

export default function PresaleUsageFeedbackPage() {
  const [activeTab, setActiveTab] = useState("submit");
  const [feedbackList, setFeedbackList] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // 提交反馈表单状态
  const [formData, setFormData] = useState({
    usage_scenario: "方案生成",
    used: 1,
    outcome: "进行中",
    customer_feedback: "无反馈",
    rating: 4,
    rating_comment: "",
    improvement_suggestion: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // 加载反馈列表和统计
  useEffect(() => {
    loadFeedbackData();
  }, []);

  const loadFeedbackData = async () => {
    setLoading(true);
    try {
      const [listRes, statsRes] = await Promise.all([
        listUsageFeedback(10),
        usageFeedbackStats(),
      ]);
      setFeedbackList(listRes?.items || []);
      setStats(statsRes);
    } catch (e) {
      console.error("加载反馈数据失败:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitSuccess(false);
    try {
      await submitUsageFeedback(formData);
      setSubmitSuccess(true);
      // 重置表单
      setFormData({
        usage_scenario: "方案生成",
        used: 1,
        outcome: "进行中",
        customer_feedback: "无反馈",
        rating: 4,
        rating_comment: "",
        improvement_suggestion: "",
      });
      // 刷新列表
      loadFeedbackData();
      setTimeout(() => setSubmitSuccess(false), 3000);
    } catch (e) {
      console.error("提交反馈失败:", e);
      alert("提交失败: " + (e.message || "未知错误"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="售前智能体使用反馈"
          description="提交AI产出的使用效果，帮助AI持续改进"
        />

        {/* Tab 切换 */}
        <div className="mb-6 flex gap-2">
          <Button
            variant={activeTab === "submit" ? "default" : "outline"}
            onClick={() => setActiveTab("submit")}
          >
            <Send className="h-4 w-4 mr-2" />
            提交反馈
          </Button>
          <Button
            variant={activeTab === "stats" ? "default" : "outline"}
            onClick={() => setActiveTab("stats")}
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            使用统计
          </Button>
        </div>

        {/* 提交反馈表单 */}
        {activeTab === "submit" && (
          <Card>
            <CardHeader>
              <CardTitle>提交使用反馈</CardTitle>
            </CardHeader>
            <CardContent>
              {submitSuccess && (
                <Alert className="mb-4 bg-green-50 border-green-200">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <AlertDescription className="text-green-800">
                    反馈提交成功！感谢帮助AI改进。
                  </AlertDescription>
                </Alert>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                {/* 使用场景 */}
                <div>
                  <label className="block text-sm font-medium mb-2">使用场景</label>
                  <Select
                    value={formData.usage_scenario}
                    onChange={(e) => setFormData({ ...formData, usage_scenario: e.target.value })}
                  >
                    <option value="方案生成">方案生成</option>
                    <option value="验厂资料">验厂资料</option>
                    <option value="销售教练">销售教练</option>
                    <option value="竞争分析">竞争分析</option>
                  </Select>
                </div>

                {/* 是否使用 */}
                <div>
                  <label className="block text-sm font-medium mb-2">是否使用了AI产出</label>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant={formData.used === 1 ? "default" : "outline"}
                      onClick={() => setFormData({ ...formData, used: 1 })}
                    >
                      <ThumbsUp className="h-4 w-4 mr-2" />
                      使用了
                    </Button>
                    <Button
                      type="button"
                      variant={formData.used === 0 ? "default" : "outline"}
                      onClick={() => setFormData({ ...formData, used: 0 })}
                    >
                      <ThumbsDown className="h-4 w-4 mr-2" />
                      没使用
                    </Button>
                  </div>
                </div>

                {/* 使用结果 */}
                <div>
                  <label className="block text-sm font-medium mb-2">使用结果</label>
                  <Select
                    value={formData.outcome}
                    onChange={(e) => setFormData({ ...formData, outcome: e.target.value })}
                  >
                    <option value="成单">成单</option>
                    <option value="未成单">未成单</option>
                    <option value="部分采用">部分采用</option>
                    <option value="进行中">进行中</option>
                  </Select>
                </div>

                {/* 客户反馈 */}
                <div>
                  <label className="block text-sm font-medium mb-2">客户反馈</label>
                  <Select
                    value={formData.customer_feedback}
                    onChange={(e) => setFormData({ ...formData, customer_feedback: e.target.value })}
                  >
                    <option value="接受">接受</option>
                    <option value="拒绝">拒绝</option>
                    <option value="修改">修改</option>
                    <option value="无反馈">无反馈</option>
                  </Select>
                </div>

                {/* 评分 */}
                <div>
                  <label className="block text-sm font-medium mb-2">
                    销售评分：{formData.rating} 分
                  </label>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`h-8 w-8 cursor-pointer ${
                          star <= formData.rating
                            ? "fill-yellow-400 text-yellow-400"
                            : "text-slate-300"
                        }`}
                        onClick={() => setFormData({ ...formData, rating: star })}
                      />
                    ))}
                  </div>
                </div>

                {/* 评分说明 */}
                <div>
                  <label className="block text-sm font-medium mb-2">评分说明（可选）</label>
                  <Textarea
                    value={formData.rating_comment}
                    onChange={(e) => setFormData({ ...formData, rating_comment: e.target.value })}
                    placeholder="为什么给这个评分？AI产出哪里好/哪里不好？"
                    rows={2}
                  />
                </div>

                {/* 改进建议 */}
                <div>
                  <label className="block text-sm font-medium mb-2">改进建议（可选）</label>
                  <Textarea
                    value={formData.improvement_suggestion}
                    onChange={(e) => setFormData({ ...formData, improvement_suggestion: e.target.value })}
                    placeholder="你觉得AI哪里可以改进？有什么具体建议？"
                    rows={3}
                  />
                </div>

                <Button type="submit" disabled={submitting} className="w-full">
                  <Send className="h-4 w-4 mr-2" />
                  {submitting ? "提交中..." : "提交反馈"}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {/* 使用统计 */}
        {activeTab === "stats" && (
          <div className="space-y-6">
            {loading ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                  <p className="text-slate-500">加载中...</p>
                </CardContent>
              </Card>
            ) : stats ? (
              <>
                {/* 核心指标 */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-slate-500">总反馈数</p>
                          <p className="text-2xl font-bold">{stats.total_feedback}</p>
                        </div>
                        <MessageSquare className="h-8 w-8 text-blue-500" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-slate-500">使用率</p>
                          <p className="text-2xl font-bold">{stats.usage_rate}%</p>
                        </div>
                        <CheckCircle className="h-8 w-8 text-green-500" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-slate-500">成单率</p>
                          <p className="text-2xl font-bold">{stats.win_rate}%</p>
                        </div>
                        <TrendingUp className="h-8 w-8 text-purple-500" />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-slate-500">平均评分</p>
                          <p className="text-2xl font-bold">{stats.avg_rating || "-"}</p>
                        </div>
                        <Star className="h-8 w-8 text-yellow-500" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* 按场景统计 */}
                <Card>
                  <CardHeader>
                    <CardTitle>按使用场景</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(stats.by_scenario).map(([scenario, count]) => (
                        <div key={scenario}>
                          <div className="flex justify-between mb-1">
                            <span className="text-sm font-medium">{scenario}</span>
                            <span className="text-sm text-slate-500">{count} 次</span>
                          </div>
                          <Progress value={(count / stats.total_feedback) * 100} />
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* 按结果统计 */}
                <Card>
                  <CardHeader>
                    <CardTitle>按使用结果</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(stats.by_outcome).map(([outcome, count]) => {
                        const icon = outcome === "成单" ? CheckCircle : outcome === "未成单" ? XCircle : Clock;
                        const color = outcome === "成单" ? "text-green-500" : outcome === "未成单" ? "text-red-500" : "text-slate-500";
                        const Icon = icon;
                        return (
                          <div key={outcome} className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Icon className={`h-5 w-5 ${color}`} />
                              <span className="text-sm font-medium">{outcome}</span>
                            </div>
                            <Badge variant="outline">{count} 次</Badge>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>

                {/* 最近反馈 */}
                <Card>
                  <CardHeader>
                    <CardTitle>最近反馈</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {feedbackList.length === 0 ? (
                      <p className="text-center text-slate-500 py-8">暂无反馈</p>
                    ) : (
                      <div className="space-y-3">
                        {feedbackList.map((fb) => (
                          <div key={fb.id} className="border rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline">{fb.usage_scenario}</Badge>
                                <Badge variant={fb.used ? "default" : "secondary"}>
                                  {fb.used ? "已使用" : "未使用"}
                                </Badge>
                              </div>
                              <div className="flex items-center gap-1">
                                {[1, 2, 3, 4, 5].map((star) => (
                                  <Star
                                    key={star}
                                    className={`h-4 w-4 ${
                                      star <= fb.rating
                                        ? "fill-yellow-400 text-yellow-400"
                                        : "text-slate-300"
                                    }`}
                                  />
                                ))}
                              </div>
                            </div>
                            {fb.rating_comment && (
                              <p className="text-sm text-slate-600 mb-2">{fb.rating_comment}</p>
                            )}
                            {fb.improvement_suggestion && (
                              <p className="text-sm text-blue-600">
                                💡 {fb.improvement_suggestion}
                              </p>
                            )}
                            <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                              <span>{fb.submitted_by_name}</span>
                              <span>{fb.created_at?.slice(0, 10)}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-slate-500">暂无统计数据</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
