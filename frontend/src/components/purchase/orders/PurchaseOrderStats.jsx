/**
 * PurchaseOrderStats - 采购订单统计概览组件
 * 显示订单总数、待处理、延期、总金额等关键指标
 */

import { Package, Clock, AlertTriangle, DollarSign } from "lucide-react";
import { Card, CardContent } from "../../../ui";
import { formatOrderAmount } from "./purchaseOrderConstants";

export default function PurchaseOrderStats({ stats = {}, loading = false }) {
  const {
    total = 0,
    pending = 0,
    delayed = 0,
    totalAmount = 0,
  } = stats;

  const statCards = [
    {
      title: "总订单",
      value: total,
      icon: Package,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/30",
    },
    {
      title: "待收货",
      value: pending,
      icon: Clock,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/30",
    },
    {
      title: "已延期",
      value: delayed,
      icon: AlertTriangle,
      color: "text-red-400",
      bgColor: "bg-red-500/10",
      borderColor: "border-red-500/30",
    },
    {
      title: "总金额",
      value: formatOrderAmount(totalAmount),
      icon: DollarSign,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/30",
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="bg-slate-800/50 border border-slate-700/50 animate-pulse">
            <CardContent className="p-4">
              <div className="h-16 bg-slate-700/50 rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        return (
          <Card
            key={index}
            className={`bg-slate-800/50 border ${stat.borderColor} hover:border-opacity-50 transition-all`}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm text-slate-400 mb-1">{stat.title}</p>
                  <p className={`text-2xl font-bold text-white`}>
                    {stat.value}
                  </p>
                </div>
                <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
