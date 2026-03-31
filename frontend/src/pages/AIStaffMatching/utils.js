// -*- coding: utf-8 -*-
import { RECOMMENDATION_CONFIG } from "./constants";

// 获取得分颜色
export const getScoreColor = (score) => {
  if (score >= 85) {return "text-green-400";}
  if (score >= 70) {return "text-blue-400";}
  if (score >= 55) {return "text-yellow-400";}
  return "text-red-400";
};

// 获取推荐类型徽章样式
export const getRecommendationBadge = (type) => {
  const config = RECOMMENDATION_CONFIG[type] || RECOMMENDATION_CONFIG.WEAK;
  const colors = {
    green: "bg-green-500/20 text-green-400 border-green-500/30",
    blue: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    yellow: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    red: "bg-red-500/20 text-red-400 border-red-500/30"
  };
  return colors[config.color] || colors.red;
};
