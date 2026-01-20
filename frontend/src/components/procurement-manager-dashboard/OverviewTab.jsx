import { TabsContent } from "../../components/ui";
import RecentApprovalsCard from "./RecentApprovalsCard";
import TeamOverviewCard from "./TeamOverviewCard";
import KeyMetricsCard from "./KeyMetricsCard";

export default function OverviewTab({ stats, recentApprovals }) {
  return (
    <TabsContent value="overview" className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <RecentApprovalsCard approvals={recentApprovals} />
        <TeamOverviewCard stats={stats} />
      </div>
      <KeyMetricsCard />
    </TabsContent>
  );
}
