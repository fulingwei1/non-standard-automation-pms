import { motion } from "framer-motion";
import {
  Phone,
  Mail,
  MapPin,
  Star,
  TrendingUp,
  TrendingDown,
  Eye,
  Edit,
  Award,
  AlertTriangle,
  Users,
} from "lucide-react";
import { Badge, Button, Progress } from "../../components/ui";
import { cn, formatCurrency } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import { levelConfig, statusConfig } from "./pageConstants";

const SupplierCard = ({ supplier, onView }) => {
  const levelCfg = levelConfig[supplier.level];
  const statusCfg = statusConfig[supplier.status];

  return (
    <motion.div
      variants={fadeIn}
      className="rounded-lg border border-slate-700 bg-slate-800/50 overflow-hidden hover:bg-slate-800/70 transition-all">

      {/* Header */}
      <div className="bg-gradient-to-r from-slate-700 to-slate-800 p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <h3 className="font-semibold text-slate-100 text-lg">
              {supplier.name}
            </h3>
            <p className="text-sm text-slate-400 mt-1">{supplier.category}</p>
          </div>
          <div className="flex flex-col gap-1">
            <Badge className={cn("text-xs", levelCfg.color)}>
              <Award className="w-3 h-3 mr-1" />
              {levelCfg.label}
            </Badge>
            <Badge className={cn("text-xs", statusCfg.color)}>
              {statusCfg.label}
            </Badge>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Contact Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="flex items-center gap-2 text-slate-300">
            <Users className="w-4 h-4 text-slate-500" />
            <span>{supplier.contactPerson}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <Phone className="w-4 h-4 text-slate-500" />
            <span>{supplier.phone}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <Mail className="w-4 h-4 text-slate-500" />
            <span className="truncate">{supplier.email}</span>
          </div>
          <div className="flex items-center gap-2 text-slate-300">
            <MapPin className="w-4 h-4 text-slate-500" />
            <span>{supplier.address}</span>
          </div>
        </div>

        {/* Rating Section */}
        <div className="border-t border-slate-700/50 pt-4">
          <div className="flex items-center justify-between mb-3">
            <p className="font-medium text-slate-100">综合评分</p>
            <div className="flex items-center gap-1">
              {[...Array(5)].map((_, i) =>
              <Star
                key={i}
                className={cn(
                  "w-4 h-4",
                  i < Math.floor(supplier.overallRating) ?
                  "fill-amber-400 text-amber-400" :
                  "text-slate-600"
                )} />

              )}
              <span className="ml-2 text-sm font-semibold text-amber-400">
                {supplier.overallRating.toFixed(1)}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div>
              <p className="text-slate-500 mb-1">质量</p>
              <div className="flex items-center gap-1">
                <Progress
                  value={supplier.ratingDetails.quality * 20}
                  className="flex-1 h-1.5" />

                <span className="font-medium text-slate-300 w-8">
                  {supplier.ratingDetails.quality}
                </span>
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">交期</p>
              <div className="flex items-center gap-1">
                <Progress
                  value={supplier.ratingDetails.delivery * 20}
                  className="flex-1 h-1.5" />

                <span className="font-medium text-slate-300 w-8">
                  {supplier.ratingDetails.delivery}
                </span>
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">服务</p>
              <div className="flex items-center gap-1">
                <Progress
                  value={supplier.ratingDetails.service * 20}
                  className="flex-1 h-1.5" />

                <span className="font-medium text-slate-300 w-8">
                  {supplier.ratingDetails.service}
                </span>
              </div>
            </div>
            <div>
              <p className="text-slate-500 mb-1">价格</p>
              <div className="flex items-center gap-1">
                <Progress
                  value={supplier.ratingDetails.price * 20}
                  className="flex-1 h-1.5" />

                <span className="font-medium text-slate-300 w-8">
                  {supplier.ratingDetails.price}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm border-t border-slate-700/50 pt-4">
          <div>
            <p className="text-slate-500 text-xs mb-1">交期准时率</p>
            <p className="font-semibold text-slate-100 flex items-center gap-1">
              {supplier.onTimeDeliveryRate}%
              {supplier.onTimeDeliveryRate >= 95 ?
              <TrendingUp className="w-4 h-4 text-emerald-400" /> :

              <TrendingDown className="w-4 h-4 text-red-400" />
              }
            </p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">质量合格率</p>
            <p className="font-semibold text-slate-100">
              {supplier.qualityPassRate}%
            </p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">总订单</p>
            <p className="font-semibold text-slate-100">
              {supplier.completedOrders}/{supplier.totalOrders}
            </p>
          </div>
        </div>

        {/* Financial Info */}
        <div className="grid grid-cols-2 gap-3 text-sm border-t border-slate-700/50 pt-4">
          <div>
            <p className="text-slate-500 text-xs mb-1">年度采购额</p>
            <p className="font-semibold text-amber-400">
              {formatCurrency(supplier.annualSpend)}
            </p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">年增长率</p>
            <p
              className={cn(
                "font-semibold",
                supplier.growthRate > 0 ? "text-emerald-400" : "text-red-400"
              )}>

              {supplier.growthRate > 0 ? "+" : ""}
              {supplier.growthRate}%
            </p>
          </div>
        </div>

        {/* Issues or Risk Alert */}
        {(supplier.issues?.length > 0 || supplier.riskLevel !== "low") &&
        <div
          className={cn(
            "rounded-lg p-3 border text-sm",
            supplier.riskLevel === "high" ?
            "bg-red-500/10 border-red-500/30" :
            "bg-amber-500/10 border-amber-500/30"
          )}>

            {supplier.issues?.length > 0 &&
          <div>
                <p
              className={cn(
                "text-xs font-medium mb-2",
                supplier.riskLevel === "high" ?
                "text-red-400" :
                "text-amber-400"
              )}>

                  <AlertTriangle className="w-3 h-3 mr-1 inline" />
                  最近问题
                </p>
                <ul className="space-y-1 text-xs text-slate-300">
                  {supplier.issues.slice(0, 2).map((issue, idx) =>
              <li key={idx} className="flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                      {issue.issue}
              </li>
              )}
                </ul>
          </div>
          }
        </div>
        }

        {/* Action Bar */}
        <div className="flex gap-2 pt-2 border-t border-slate-700/50">
          <Button size="sm" className="flex-1" onClick={() => onView(supplier)}>
            <Eye className="w-4 h-4 mr-1" />
            查看详情
          </Button>
          <Button size="sm" variant="outline">
            <Edit className="w-4 h-4 mr-1" />
            编辑
          </Button>
        </div>
      </div>
    </motion.div>);

};

export default SupplierCard;
