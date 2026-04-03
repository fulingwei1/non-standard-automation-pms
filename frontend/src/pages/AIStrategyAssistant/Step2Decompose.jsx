import { motion } from "framer-motion";
import {
  Target,
  Loader2,
  Sparkles,
  Upload,
  ArrowRight,
  ArrowLeft,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Input,
  Textarea,
  Label,
} from "@/components/ui";
import { staggerContainer } from "@/lib/animations";
import { getDimensionLabel, getDimensionColor } from "@/services/api/aiStrategy";

export default function Step2Decompose({
  decomposeInput,
  setDecomposeInput,
  decomposeResult,
  loading,
  onDecompose,
  onApply,
  onPrev,
  onNext,
}) {
  return (
    <motion.div {...staggerContainer} className="space-y-6">
      <Card className="bg-gray-800/50 border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-400" />
            战略信息
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label className="text-gray-300">战略名称</Label>
            <Input
              value={decomposeInput.strategyName}
              onChange={(e) => setDecomposeInput({ ...decomposeInput, strategyName: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white"
              placeholder="如：2026 年高质量发展战略"
            />
          </div>
          <div>
            <Label className="text-gray-300">战略愿景</Label>
            <Textarea
              value={decomposeInput.strategyVision}
              onChange={(e) => setDecomposeInput({ ...decomposeInput, strategyVision: e.target.value })}
              className="bg-gray-900 border-gray-700 text-white min-h-[80px]"
              placeholder="描述战略愿景"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label className="text-gray-300">战略年度</Label>
              <Input
                type="number"
                value={decomposeInput.strategyYear}
                onChange={(e) => setDecomposeInput({ ...decomposeInput, strategyYear: parseInt(e.target.value) })}
                className="bg-gray-900 border-gray-700 text-white"
              />
            </div>
            <div>
              <Label className="text-gray-300">行业</Label>
              <Input
                value={decomposeInput.industry}
                onChange={(e) => setDecomposeInput({ ...decomposeInput, industry: e.target.value })}
                className="bg-gray-900 border-gray-700 text-white"
              />
            </div>
          </div>
          <Button
            onClick={onDecompose}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                AI 分解中...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                AI 战略分解
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {decomposeResult && (
        <motion.div {...staggerContainer} className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">BSC 四维度分解结果</h3>
            <Button onClick={onApply} size="sm" variant="outline">
              <Upload className="w-4 h-4 mr-2" />
              导入系统
            </Button>
          </div>

          {decomposeResult.csfs?.map((csf, csfIndex) => (
            <Card key={csfIndex} className={`border-l-4 ${getDimensionColor(csf.dimension).split(" ")[2]}`}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white flex items-center gap-2">
                    <Badge className={getDimensionColor(csf.dimension)}>
                      {getDimensionLabel(csf.dimension)}
                    </Badge>
                    <span>{csf.name}</span>
                  </CardTitle>
                  <Badge variant="secondary" className="bg-gray-700 text-gray-300">
                    权重：{csf.weight}%
                  </Badge>
                </div>
                <p className="text-sm text-gray-400 mt-2">{csf.description}</p>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {csf.kpis?.map((kpi, kpiIndex) => (
                    <div key={kpiIndex} className="p-3 bg-gray-900/50 rounded-lg border border-gray-700">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium text-blue-300">{kpi.name}</div>
                        <Badge variant="outline" className="text-xs">
                          {kpi.ipooc_type}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-400">{kpi.description}</div>
                      <div className="flex flex-wrap gap-2 mt-2 text-xs">
                        <Badge variant="secondary">目标：{kpi.target_value} {kpi.unit}</Badge>
                        <Badge variant="secondary">基线：{kpi.baseline_value}</Badge>
                        <Badge variant="secondary">方向：{kpi.direction === "UP" ? "↑" : "↓"}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}

          <div className="flex gap-4">
            <Button onClick={onPrev} variant="outline" className="flex-1">
              <ArrowLeft className="w-4 h-4 mr-2" />
              上一步
            </Button>
            <Button onClick={onNext} className="flex-1">
              下一步
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
