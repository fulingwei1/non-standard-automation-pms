/**
 * Template filter bar component
 */

import { Search } from "lucide-react";
import {
  Card,
  CardContent,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui";
import { TEMPLATE_TYPES } from "./constants";

export default function TemplateFilters({
  searchTerm,
  setSearchTerm,
  typeFilter,
  setTypeFilter,
  equipmentFilter,
  setEquipmentFilter,
  equipmentTypes,
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索模板名称或编码..."
                value={searchTerm || "unknown"}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <Select value={typeFilter || "unknown"} onValueChange={setTypeFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="模板类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部类型</SelectItem>
              {TEMPLATE_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>
                  {t.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={equipmentFilter || "unknown"}
            onValueChange={setEquipmentFilter}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="设备类型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部设备</SelectItem>
              {(equipmentTypes || []).map((type) => (
                <SelectItem key={type} value={type || "unknown"}>
                  {type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  );
}
