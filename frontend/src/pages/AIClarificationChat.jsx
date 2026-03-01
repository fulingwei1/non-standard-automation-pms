/**
 * AI Clarification Chat Page - AI澄清对话页面
 * 交互式AI澄清对话界面
 */

import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Send,
  Bot,
  User,
  MessageSquare,
  Loader } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Textarea,
  Badge } from
"../components/ui";
import { technicalAssessmentApi } from "../services/api";

export default function AIClarificationChat() {
  const { sourceType, sourceId } = useParams();
  const _navigate = useNavigate();

  const [clarifications, setClarifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [_currentRound, setCurrentRound] = useState(1);
  const [questions, setQuestions] = useState("");
  const [answers, setAnswers] = useState({}); // {questionIndex: answer}

  useEffect(() => {
    loadClarifications();
  }, [sourceType, sourceId]);

  const loadClarifications = async () => {
    try {
      setLoading(true);
      const response = await technicalAssessmentApi.getAIClarifications({
        source_type: sourceType?.toUpperCase(),
        source_id: parseInt(sourceId)
      });
      const items = response.data.items || response.data?.items || response.data || [];
      setClarifications(items);
      if (items?.length > 0) {
        const maxRound = Math.max(...(items || []).map((item) => item.round));
        setCurrentRound(maxRound + 1);
      }
    } catch (error) {
      console.error("加载澄清记录失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateQuestions = async () => {
    if (!questions.trim()) {
      alert("请输入问题");
      return;
    }

    try {
      setSending(true);
      const questionsArray = questions.split("\n").filter((q) => q.trim());
      const questionsJson = JSON.stringify(questionsArray);

      if (sourceType === "lead") {
        await technicalAssessmentApi.createAIClarificationForLead(
          parseInt(sourceId),
          { questions: questionsJson }
        );
      } else {
        await technicalAssessmentApi.createAIClarificationForOpportunity(
          parseInt(sourceId),
          { questions: questionsJson }
        );
      }

      setQuestions("");
      await loadClarifications();
    } catch (error) {
      console.error("创建澄清失败:", error);
      alert("创建失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setSending(false);
    }
  };

  const handleSubmitAnswers = async (clarificationId) => {
    const currentClarification = (clarifications || []).find(
      (c) => c.id === clarificationId
    );
    if (!currentClarification) {return;}

    const questionsArray = JSON.parse(currentClarification.questions);
    const answersArray = (questionsArray || []).map((_, idx) => answers[idx] || "");

    if ((answersArray || []).some((a) => !a.trim())) {
      alert("请回答所有问题");
      return;
    }

    try {
      setSending(true);
      await technicalAssessmentApi.updateAIClarification(clarificationId, {
        answers: JSON.stringify(answersArray)
      });
      setAnswers({});
      await loadClarifications();
    } catch (error) {
      console.error("提交回答失败:", error);
      alert("提交失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return <div className="p-6">加载中...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <PageHeader
        title="AI澄清对话"
        breadcrumbs={[
        { label: "销售管理", path: "/sales" },
        {
          label: sourceType === "lead" ? "线索管理" : "商机管理",
          path:
          sourceType === "lead" ? "/sales/leads" : "/sales/opportunities"
        },
        { label: "AI澄清", path: "" }]
        } />


      <div className="mt-6 space-y-6">
        {/* 澄清记录列表 */}
        {(clarifications || []).map((clarification) => {
          const questionsArray = JSON.parse(clarification.questions || "[]");
          const answersArray = clarification.answers ?
          JSON.parse(clarification.answers) :
          [];
          const hasAnswers = answersArray.length > 0;

          return (
            <Card
              key={clarification.id}
              className="bg-gray-800 border-gray-700">

              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5" />第{" "}
                    {clarification.round} 轮澄清
                  </CardTitle>
                  <Badge
                    className={hasAnswers ? "bg-green-500" : "bg-yellow-500"}>

                    {hasAnswers ? "已回复" : "待回复"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* AI问题 */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-semibold text-gray-400">
                    <Bot className="w-4 h-4" />
                    AI问题
                  </div>
                  <div className="space-y-2 pl-6">
                    {(questionsArray || []).map((question, idx) =>
                    <div key={idx} className="p-3 bg-gray-700 rounded-lg">
                        <div className="text-sm mb-2">
                          {idx + 1}. {question}
                        </div>
                        {hasAnswers ?
                      <div className="mt-2 p-2 bg-gray-600 rounded text-sm">
                            <div className="flex items-center gap-2 mb-1">
                              <User className="w-3 h-3" />
                              <span className="text-xs text-gray-400">
                                回答
                              </span>
                            </div>
                            {answersArray[idx]}
                      </div> :

                      <Textarea
                        className="mt-2 bg-gray-600 border-gray-500 text-white"
                        placeholder="请输入回答..."
                        rows={2}
                        value={answers[idx] || ""}
                        onChange={(e) =>
                        setAnswers({ ...answers, [idx]: e.target.value })
                        } />

                      }
                    </div>
                    )}
                  </div>
                </div>

                {/* 提交按钮 */}
                {!hasAnswers &&
                <Button
                  onClick={() => handleSubmitAnswers(clarification.id)}
                  disabled={sending}
                  className="bg-blue-600 hover:bg-blue-700">

                    {sending ?
                  <Loader className="w-4 h-4 mr-2 animate-spin" /> :

                  <Send className="w-4 h-4 mr-2" />
                  }
                    提交回答
                </Button>
                }
              </CardContent>
            </Card>);

        })}

        {/* 创建新澄清 */}
        <Card className="bg-gray-800 border-gray-700">
          <CardHeader>
            <CardTitle>创建新澄清</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  AI生成的问题（每行一个问题）
                </label>
                <Textarea
                  className="bg-gray-700 border-gray-600 text-white"
                  placeholder="请输入问题，每行一个&#10;例如：&#10;接口协议是否已确定？&#10;节拍要求是否可调整？"
                  rows={6}
                  value={questions || "unknown"}
                  onChange={(e) => setQuestions(e.target.value)} />

              </div>
              <Button
                onClick={handleCreateQuestions}
                disabled={sending || !questions.trim()}
                className="bg-blue-600 hover:bg-blue-700">

                {sending ?
                <Loader className="w-4 h-4 mr-2 animate-spin" /> :

                <Send className="w-4 h-4 mr-2" />
                }
                创建澄清
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>);

}
