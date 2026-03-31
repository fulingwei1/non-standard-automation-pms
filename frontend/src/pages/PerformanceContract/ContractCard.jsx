import { motion } from "framer-motion";
import {
  Plus,
  FileText,
  ChevronDown,
  ChevronUp,
  Send,
  PenTool,
  Calculator,
  Edit2,
  Trash2,
  Target,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
} from "@/components/ui";
import { fadeIn } from "@/lib/animations";
import {
  getStatusConfig,
  getCategoryLabel,
  getScoreColor,
} from "@/services/api/performanceContract";
import { CONTRACT_TYPE_OPTIONS } from "./constants";

export default function ContractCard({
  contract,
  expandedContractId,
  selectedContract,
  onExpandContract,
  onOpenAddItem,
  onSubmitContract,
  onSignContract,
  onOpenEvaluate,
  onOpenEditItem,
  onDeleteItem,
}) {
  const statusConfig = getStatusConfig(contract.status);
  const typeConfig = CONTRACT_TYPE_OPTIONS.find((t) => t.value === contract.contract_type);
  const TypeIcon = typeConfig?.icon || FileText;

  return (
    <motion.div key={contract.id} variants={fadeIn} className="mb-4">
      <Card className="bg-slate-800/50 border-slate-700/50 hover:border-slate-600 transition-colors">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400">
                <TypeIcon size={20} />
              </div>
              <div>
                <CardTitle className="text-lg text-white flex items-center gap-2">
                  {contract.contract_no}
                  <Badge className={statusConfig.color}>{statusConfig.label}</Badge>
                </CardTitle>
                <p className="text-sm text-slate-400 mt-1">
                  {contract.year}年 {contract.department_name || "无部门"}
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onExpandContract(contract)}
              className="text-slate-400 hover:text-white"
            >
              {expandedContractId === contract.id ? (
                <ChevronUp size={18} />
              ) : (
                <ChevronDown size={18} />
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-slate-500">签约人</p>
              <p className="text-white">{contract.signer_name}</p>
              <p className="text-xs text-slate-400">{contract.signer_title}</p>
            </div>
            <div>
              <p className="text-slate-500">对方/上级</p>
              <p className="text-white">{contract.counterpart_name}</p>
              <p className="text-xs text-slate-400">{contract.counterpart_title}</p>
            </div>
            <div>
              <p className="text-slate-500">权重总和</p>
              <p className={`font-medium ${contract.total_weight === 100 ? "text-emerald-400" : "text-amber-400"}`}>
                {contract.total_weight?.toFixed(1) || 0}%
              </p>
            </div>
            <div>
              <p className="text-slate-500">签署日期</p>
              <p className="text-white">{contract.sign_date || "-"}</p>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex gap-2 mt-4 pt-4 border-t border-slate-700/50">
            {contract.status === "draft" && (
              <>
                <Button
                  size="sm"
                  onClick={() => onOpenAddItem(contract)}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Plus size={16} className="mr-1" />
                  添加指标
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onSubmitContract(contract.id)}
                  className="border-emerald-600 text-emerald-400 hover:bg-emerald-600/20"
                >
                  <Send size={16} className="mr-1" />
                  提交审批
                </Button>
              </>
            )}
            {contract.status === "pending_sign" && (
              <>
                <Button
                  size="sm"
                  onClick={() => onSignContract(contract.id, "signer")}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <PenTool size={16} className="mr-1" />
                  签署确认
                </Button>
              </>
            )}
            {contract.status === "active" && (
              <>
                <Button
                  size="sm"
                  onClick={() => onOpenEvaluate(contract)}
                  className="bg-amber-600 hover:bg-amber-700"
                >
                  <Calculator size={16} className="mr-1" />
                  评分
                </Button>
              </>
            )}
            {expandedContractId === contract.id && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => onOpenAddItem(contract)}
                className="border-blue-600 text-blue-400 hover:bg-blue-600/20"
              >
                <Plus size={16} className="mr-1" />
                添加指标
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 展开的详情 */}
      {expandedContractId === contract.id && selectedContract && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="mt-2 p-4 rounded-lg bg-slate-900/50 border border-slate-700/50"
        >
          <h4 className="text-white font-medium mb-3 flex items-center gap-2">
            <Target size={18} className="text-blue-400" />
            指标条目 ({selectedContract.items?.length || 0})
          </h4>
          {selectedContract.items?.length > 0 ? (
            <div className="space-y-2">
              {selectedContract.items.map((item, _idx) => (
                <div
                  key={item.id}
                  className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="text-xs border-slate-600 text-slate-300">
                          {getCategoryLabel(item.category)}
                        </Badge>
                        <span className="text-white font-medium">{item.indicator_name}</span>
                      </div>
                      {item.indicator_description && (
                        <p className="text-sm text-slate-400 mt-1">{item.indicator_description}</p>
                      )}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2 text-xs">
                        <div>
                          <span className="text-slate-500">权重：</span>
                          <span className="text-slate-300">{item.weight}%</span>
                        </div>
                        <div>
                          <span className="text-slate-500">目标值：</span>
                          <span className="text-slate-300">{item.target_value || "-"}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">实际值：</span>
                          <span className="text-slate-300">{item.actual_value || "-"}</span>
                        </div>
                        <div>
                          <span className="text-slate-500">得分：</span>
                          <span className={getScoreColor(item.score)}>{item.score || "-"}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onOpenEditItem(contract, item)}
                        className="h-8 w-8 p-0 text-slate-400 hover:text-blue-400"
                      >
                        <Edit2 size={14} />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onDeleteItem(contract.id, item.id)}
                        className="h-8 w-8 p-0 text-slate-400 hover:text-red-400"
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 text-sm text-center py-4">暂无指标条目</p>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
