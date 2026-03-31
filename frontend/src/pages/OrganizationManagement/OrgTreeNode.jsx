import { useState } from "react";
import {
  Plus,
  Edit3,
  Trash2,
  Eye,
  ChevronRight,
  ChevronDown,
  UserCircle,
} from "lucide-react";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "../../components/ui/dropdown-menu";
import { cn } from "../../lib/utils";
import { UNIT_TYPES, getUnitTypeConfig } from "./unitTypeConfig";

export default function OrgTreeNode({ unit, level = 0, onEdit, onView, onDelete, onAddChild, allUnits }) {
  const [expanded, setExpanded] = useState(level < 2);
  const typeConfig = getUnitTypeConfig(unit.unit_type);
  const Icon = typeConfig.icon;

  // 获取可添加的子类型
  const getAvailableChildTypes = () => {
    const typeOrder = ["COMPANY", "BUSINESS_UNIT", "DEPARTMENT", "TEAM"];
    const currentIndex = typeOrder.indexOf(unit.unit_type);
    return UNIT_TYPES.filter((t) => typeOrder.indexOf(t.value) > currentIndex);
  };

  const availableChildTypes = getAvailableChildTypes();

  return (
    <div>
      <div
        className={cn(
          "flex items-center gap-2 p-2 rounded hover:bg-muted/50 group",
          level > 0 && "ml-4"
        )}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
      >
        {unit.children && unit.children?.length > 0 ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 hover:bg-muted rounded"
          >
            {expanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        ) : (
          <div className="w-6" />
        )}
        <Icon className={cn("h-4 w-4", typeConfig.color)} />
        <span className="flex-1 font-medium">{unit.unit_name}</span>
        <Badge variant="outline" className="text-xs font-mono">
          {unit.unit_code}
        </Badge>
        <Badge variant="secondary" className={cn("text-xs", typeConfig.color)}>
          {typeConfig.label}
        </Badge>
        {unit.manager_name && (
          <Badge variant="outline" className="text-xs">
            <UserCircle className="h-3 w-3 mr-1" />
            {unit.manager_name}
          </Badge>
        )}
        <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button variant="ghost" size="sm" onClick={() => onView(unit)}>
            <Eye className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" onClick={() => onEdit(unit)}>
            <Edit3 className="h-4 w-4" />
          </Button>
          {availableChildTypes.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm">
                  <Plus className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                {(availableChildTypes || []).map((childType) => (
                  <DropdownMenuItem
                    key={childType.value}
                    onClick={() => onAddChild(unit, childType.value)}
                  >
                    <childType.icon className={cn("h-4 w-4 mr-2", childType.color)}  />
                    添加{childType.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {!unit.children?.length && (
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
              onClick={() => onDelete(unit)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
      {expanded && unit.children && unit.children?.length > 0 && (
        <div>
          {(unit.children || []).map((child) => (
            <OrgTreeNode
              key={child.id}
              unit={child}
              level={level + 1}
              onEdit={onEdit}
              onView={onView}
              onDelete={onDelete}
              onAddChild={onAddChild}
              allUnits={allUnits}
            />
          ))}
        </div>
      )}
    </div>
  );
}
