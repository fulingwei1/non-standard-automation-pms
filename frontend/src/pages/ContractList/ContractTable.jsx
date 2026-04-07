import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { statusConfig } from "./constants";

function ContractRow({ contract, onClick }) {
  const statusConf = statusConfig[contract.status] || statusConfig.draft;
  const paymentProgress =
    contract.totalAmount > 0
      ? (contract.paidAmount / contract.totalAmount) * 100
      : 0;

  return (
    <tr
      onClick={() => onClick(contract)}
      className="border-b border-white/5 hover:bg-surface-100 cursor-pointer transition-colors"
    >
      <td className="p-4">
        <div>
          <div className="font-medium text-white">{contract.name}</div>
          <div className="text-xs text-slate-500">{contract.id}</div>
        </div>
      </td>
      <td className="p-4 text-sm text-slate-400">{contract.customerShort}</td>
      <td className="p-4 text-right">
        <span className="font-medium text-amber-400">
          ¥{(contract.totalAmount / 10000).toFixed(0)}万
        </span>
      </td>
      <td className="p-4">
        <div className="flex items-center gap-2">
          <Progress value={paymentProgress} className="w-20 h-2" />
          <span className="text-xs text-slate-400">
            {paymentProgress.toFixed(0)}%
          </span>
        </div>
      </td>
      <td className="p-4 text-sm text-slate-400">
        {contract.signDate || "-"}
      </td>
      <td className="p-4 text-sm text-slate-400">
        {contract.deliveryDate || "-"}
      </td>
      <td className="p-4">
        <Badge
          className={cn(
            "text-xs",
            statusConf.textColor,
            "bg-transparent border-0"
          )}
        >
          <div
            className={cn("w-2 h-2 rounded-full mr-1", statusConf.color)}
          />
          {statusConf.label}
        </Badge>
      </td>
      <td className="p-4">
        <div className="flex justify-center gap-1">
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Eye className="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </td>
    </tr>
  );
}

export default function ContractTable({
  contracts,
  onContractClick,
  onCreateClick,
}) {
  return (
    <motion.div variants={fadeIn}>
      <Card>
        <CardContent className="p-0">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left p-4 text-sm font-medium text-slate-400">
                  合同
                </th>
                <th className="text-left p-4 text-sm font-medium text-slate-400">
                  客户
                </th>
                <th className="text-right p-4 text-sm font-medium text-slate-400">
                  合同金额
                </th>
                <th className="text-center p-4 text-sm font-medium text-slate-400">
                  回款进度
                </th>
                <th className="text-left p-4 text-sm font-medium text-slate-400">
                  签约日期
                </th>
                <th className="text-left p-4 text-sm font-medium text-slate-400">
                  交付日期
                </th>
                <th className="text-left p-4 text-sm font-medium text-slate-400">
                  状态
                </th>
                <th className="text-center p-4 text-sm font-medium text-slate-400">
                  操作
                </th>
              </tr>
            </thead>
            <tbody>
              {(contracts || []).map((contract) => (
                <ContractRow
                  key={contract.id}
                  contract={contract}
                  onClick={onContractClick}
                />
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {contracts.length === 0 && (
        <div className="text-center py-16">
          <FileSignature className="w-12 h-12 mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">暂无合同</h3>
          <p className="text-slate-400 mb-4">没有找到符合条件的合同</p>
          <Button onClick={onCreateClick}>
            <Plus className="w-4 h-4 mr-2" />
            新建合同
          </Button>
        </div>
      )}
    </motion.div>
  );
}
