import { Package, Box, Wrench, Settings, Zap, FileText } from "lucide-react";
import { MATERIAL_TYPE } from "../../components/material-readiness";

export const readinessConfigs = {
  ready: { min: 100, label: "齐套", color: "bg-emerald-500" },
  mostly: { min: 80, label: "基本齐套", color: "bg-blue-500" },
  partial: { min: 50, label: "部分齐套", color: "bg-amber-500" },
  shortage: { min: 0, label: "缺料", color: "bg-red-500" },
};

export const TYPE_ICON_MAP = {
  [MATERIAL_TYPE.RAW_MATERIAL]: Package,
  [MATERIAL_TYPE.COMPONENT]: Box,
  [MATERIAL_TYPE.EQUIPMENT]: Wrench,
  [MATERIAL_TYPE.TOOL]: Settings,
  [MATERIAL_TYPE.CONSUMABLE]: Zap,
  [MATERIAL_TYPE.SOFTWARE]: FileText,
  [MATERIAL_TYPE.DOCUMENTATION]: FileText,
};
