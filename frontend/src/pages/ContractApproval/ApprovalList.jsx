import { motion } from "framer-motion";
import { Search } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  Input,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui";
import { fadeIn } from "../../lib/animations";
import { ApprovalListItem } from "./ApprovalListItem";
import { ApprovalHistoryItem } from "./ApprovalHistoryItem";

export function ApprovalList({
  activeTab,
  setActiveTab,
  searchTerm,
  setSearchTerm,
  filteredApprovals,
  pendingApprovals,
  approvalHistory,
  onViewDetail,
}) {
  return (
    <>
      {/* Search bar */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardContent className="p-4">
            <div className="relative">
              <Input
                placeholder="搜索合同、客户或提交人..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Tabbed list */}
      <motion.div variants={fadeIn}>
        <Card>
          <CardHeader>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList>
                <TabsTrigger value="pending">
                  待审批 ({pendingApprovals.length})
                </TabsTrigger>
                <TabsTrigger value="history">
                  审批历史 ({approvalHistory.length})
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsContent value="pending" className="space-y-4">
                {filteredApprovals.map((approval) => (
                  <ApprovalListItem
                    key={approval.id}
                    approval={approval}
                    onViewDetail={onViewDetail}
                  />
                ))}
              </TabsContent>
              <TabsContent value="history" className="space-y-4">
                {filteredApprovals.map((approval) => (
                  <ApprovalHistoryItem key={approval.id} approval={approval} />
                ))}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </motion.div>
    </>
  );
}
