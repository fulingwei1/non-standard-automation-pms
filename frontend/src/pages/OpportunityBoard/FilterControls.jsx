import { motion } from "framer-motion";
import { Search, Plus, Flame } from "lucide-react";
import {
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";
import {
  OPPORTUNITY_PRIORITY_CONFIGS,
  SALES_SOURCE_CONFIGS,
  OPPORTUNITY_TYPE_CONFIGS,
} from "../../components/opportunity-board";

export default function FilterControls({
  searchTerm,
  setSearchTerm,
  selectedPriority,
  setSelectedPriority,
  selectedSource,
  setSelectedSource,
  selectedType,
  setSelectedType,
  selectedOwner,
  setSelectedOwner,
  owners,
  showHotOnly,
  setShowHotOnly,
  hideLost,
  setHideLost,
  onCreateClick,
}) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={fadeIn}
      className="bg-surface-1 rounded-xl border border-border p-4 mb-6">

      <div className="flex flex-col lg:flex-row gap-4 items-center justify-between">
        {/* Search and Filters */}
        <div className="flex-1 flex flex-col lg:flex-row gap-2 items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary" />
            <Input
              placeholder="搜索机会名称、客户..."
              value={searchTerm || "unknown"}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-surface-2 border-border" />

          </div>

          <div className="flex gap-2 flex-wrap">
            <Select value={selectedPriority} onValueChange={setSelectedPriority}>
              <SelectTrigger className="w-32 bg-surface-2 border-border">
                <SelectValue placeholder="优先级" />
              </SelectTrigger>
              <SelectContent className="bg-surface-2 border-border">
                <SelectItem value="all">全部优先级</SelectItem>
                {Object.entries(OPPORTUNITY_PRIORITY_CONFIGS).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={selectedSource} onValueChange={setSelectedSource}>
              <SelectTrigger className="w-32 bg-surface-2 border-border">
                <SelectValue placeholder="来源" />
              </SelectTrigger>
              <SelectContent className="bg-surface-2 border-border">
                <SelectItem value="all">全部来源</SelectItem>
                {Object.entries(SALES_SOURCE_CONFIGS).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-32 bg-surface-2 border-border">
                <SelectValue placeholder="类型" />
              </SelectTrigger>
              <SelectContent className="bg-surface-2 border-border">
                <SelectItem value="all">全部类型</SelectItem>
                {Object.entries(OPPORTUNITY_TYPE_CONFIGS).map(([key, config]) =>
                <SelectItem key={key} value={key}>
                    {config.label}
                </SelectItem>
                )}
              </SelectContent>
            </Select>

            <Select value={selectedOwner} onValueChange={setSelectedOwner}>
              <SelectTrigger className="w-32 bg-surface-2 border-border">
                <SelectValue placeholder="负责人" />
              </SelectTrigger>
              <SelectContent className="bg-surface-2 border-border">
                <SelectItem value="all">全部负责人</SelectItem>
                {(owners || []).map((owner) =>
                <SelectItem key={owner.id} value={owner.id}>
                    {owner.name}
                </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* View Options and Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant={showHotOnly ? "default" : "outline"}
            size="sm"
            onClick={() => setShowHotOnly(!showHotOnly)}
            className="flex items-center gap-1">

            <Flame className={cn("w-4 h-4", showHotOnly && "text-amber-400")} />
            热门
          </Button>
          <Button
            variant={!hideLost ? "default" : "outline"}
            size="sm"
            onClick={() => setHideLost(!hideLost)}>

            {hideLost ? "显示输单" : "隐藏输单"}
          </Button>
          <Button
            onClick={onCreateClick}
            className="bg-accent hover:bg-accent/90">

            <Plus className="w-4 h-4 mr-2" />
            新建机会
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
