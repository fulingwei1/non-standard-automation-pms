import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ListTodo,
  ChevronRight,
  Users,
  Building2,
  Calendar,
  ArrowUpRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../ui/card";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import { cn } from "../../../lib/utils";
import { getPriorityStyle, getPriorityText } from "./utils";

export default function TodoTasksCard({ tasks, onTaskClick }) {
  return (
    <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5 shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
          <ListTodo className="w-5 h-5 text-primary" />
          待办任务
          <Badge variant="secondary" className="bg-primary/20 text-primary ml-2">
            {tasks.length}
          </Badge>
        </CardTitle>
        <Link to="/presales-tasks">
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-400 hover:text-white"
          >
            查看全部
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </Link>
      </CardHeader>
      <CardContent className="space-y-3">
        {tasks.map((task, index) => (
          <motion.div
            key={task.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="p-3 rounded-lg bg-surface-50/50 border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors group"
            onClick={() => onTaskClick(task)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className={cn("text-xs", task.typeColor)}>
                    {task.type}
                  </Badge>
                  <Badge
                    className={cn("text-xs", getPriorityStyle(task.priority))}
                  >
                    {getPriorityText(task.priority)}
                  </Badge>
                </div>
                <h4 className="text-sm font-medium text-white truncate group-hover:text-primary transition-colors">
                  {task.title}
                </h4>
                <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Users className="w-3 h-3" />
                    {task.source}
                  </span>
                  <span className="flex items-center gap-1">
                    <Building2 className="w-3 h-3" />
                    {task.customer}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-400 flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {task.deadline}
                </p>
                <ArrowUpRight className="w-4 h-4 text-slate-600 group-hover:text-primary transition-colors mt-2 ml-auto" />
              </div>
            </div>
          </motion.div>
        ))}
      </CardContent>
    </Card>
  );
}
