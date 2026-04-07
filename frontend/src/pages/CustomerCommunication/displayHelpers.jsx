import { cn } from "../../lib/utils";
import {
  communicationTypeConfig,
  priorityConfig,
  statusConfig,
  satisfactionConfig,
} from "./constants";

export const getStatusBadge = (status) => {
  const config = statusConfig[status];
  if (!config) {return <Badge variant="secondary">{status}</Badge>;}

  return (
    <Badge variant="secondary" className={cn("border-0", config.bg, config.color)}>
      {config.label}
    </Badge>);

};

export const getPriorityBadge = (priority) => {
  const config = priorityConfig[priority];
  if (!config) {return <Badge variant="secondary">{priority}</Badge>;}

  return (
    <Badge variant="secondary" className={cn("border-0", config.bg, config.color)}>
      {config.label}
    </Badge>);

};

export const getTypeDisplay = (type) => {
  const config = communicationTypeConfig[type];
  if (!config) {return type;}
  const Icon = config.icon;
  return (
    <div className="flex items-center space-x-1">
      <Icon className="h-4 w-4" />
      <span>{config.label}</span>
    </div>);

};

export const getSatisfactionDisplay = (rating) => {
  if (!rating) {return <span className="text-gray-400">未评分</span>;}
  const config = satisfactionConfig[rating];
  if (!config) {return <span>{rating}</span>;}

  return (
    <div className="flex items-center space-x-1">
      <div className="flex">
        {Array.from({ length: 5 }, (_, i) =>
        <Star
          key={i}
          className={cn(
            "h-4 w-4",
            i < config.stars ? "fill-yellow-400 text-yellow-400" : "text-gray-300"
          )} />

        )}
      </div>
      <span className={cn("text-sm", config.color)}>{config.label}</span>
    </div>);

};
