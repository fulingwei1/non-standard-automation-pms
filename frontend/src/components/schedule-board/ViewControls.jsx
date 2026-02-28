import { Filter, Users } from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { motion } from "framer-motion";
import { fadeIn } from "../../lib/animations";

export default function ViewControls({ viewMode, setViewMode }) {
  const viewModes = [
    { id: "kanban", label: "看板" },
    { id: "gantt", label: "甘特图" },
    { id: "calendar", label: "日历" }
  ];

  return (
    <motion.div variants={fadeIn}>
      <Card className="bg-surface-1/50">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            {/* View Mode Toggle */}
            <div className="flex items-center gap-2">
              {(viewModes || []).map((mode) => (
                <Button
                  key={mode.id}
                  variant={viewMode === mode.id ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode(mode.id)}
                >
                  {mode.label}
                </Button>
              ))}
            </div>

            {/* Filters */}
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-1" />
                筛选
              </Button>
              <Button variant="outline" size="sm">
                <Users className="w-4 h-4 mr-1" />
                资源
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
