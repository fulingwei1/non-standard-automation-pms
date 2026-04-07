import {
  getMaterialStatusColor,
  getMaterialStatusLabel,
  getReadinessStatusColor,
  getReadinessStatusLabel,
  getPriorityColor,
  getPriorityLevelLabel,
} from "../../components/material-readiness";
import { TYPE_ICON_MAP } from "./constants";

export function getStatusBadge(status) {
  return (
    <Badge
      variant="secondary"
      className="border-0"
      style={{
        backgroundColor: getMaterialStatusColor(status) + "20",
        color: getMaterialStatusColor(status),
      }}
    >
      {getMaterialStatusLabel(status)}
    </Badge>
  );
}

export function getReadinessBadge(status) {
  return (
    <Badge
      variant="secondary"
      className="border-0"
      style={{
        backgroundColor: getReadinessStatusColor(status) + "20",
        color: getReadinessStatusColor(status),
      }}
    >
      {getReadinessStatusLabel(status)}
    </Badge>
  );
}

export function getPriorityBadge(priority) {
  return (
    <Badge
      variant="secondary"
      className="border-0"
      style={{
        backgroundColor: getPriorityColor(priority) + "20",
        color: getPriorityColor(priority),
      }}
    >
      {getPriorityLevelLabel(priority)}
    </Badge>
  );
}

export function getTypeIcon(type) {
  const Icon = TYPE_ICON_MAP[type] || TYPE_ICON_MAP[Object.keys(TYPE_ICON_MAP)[0]];
  return <Icon className="h-4 w-4" />;
}
