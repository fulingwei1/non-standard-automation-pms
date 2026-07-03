// 商机阶段配置
export const stageConfig = {
  DISCOVERY: {
    label: "需求澄清",
    color: "bg-blue-500",
    textColor: "text-blue-400"
  },
  QUALIFICATION: {
    label: "需求挖掘",
    color: "bg-emerald-500",
    textColor: "text-emerald-400"
  },
  PROPOSAL: {
    label: "方案/报价中",
    color: "bg-amber-500",
    textColor: "text-amber-400"
  },
  NEGOTIATION: {
    label: "商务谈判",
    color: "bg-purple-500",
    textColor: "text-purple-400"
  },
  CLOSING: {
    label: "成交促成",
    color: "bg-pink-500",
    textColor: "text-pink-400"
  },
  WON: { label: "赢单", color: "bg-green-500", textColor: "text-green-400" },
  LOST: { label: "丢单", color: "bg-red-500", textColor: "text-red-400" }
};

export const isGatePassed = (status) => {
  const normalized = String(status || "").toUpperCase();
  return normalized === "PASS" || normalized === "PASSED";
};
