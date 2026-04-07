import {
  Clock,
  Send,
  Mail,
  AlertTriangle,
} from "lucide-react";

const STAT_CARD_COMMON = {
  bg: "bg-transparent",
  showDecoration: false,
  cardClassName: "bg-slate-800/50 border-slate-700 hover:border-slate-600 bg-none hover:shadow-none p-4",
  iconWrapperClassName: "p-0 bg-transparent rounded-none",
  iconClassName: "h-8 w-8",
};

const StatCards = ({ counts }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
    <StatCard
      title="待我审批"
      value={counts.pending}
      icon={Clock}
      color="text-amber-400"
      iconColor="text-amber-400/30"
      {...STAT_CARD_COMMON}
    />

    <StatCard
      title="我发起的"
      value={counts.initiated_pending}
      icon={Send}
      color="text-blue-400"
      iconColor="text-blue-400/30"
      {...STAT_CARD_COMMON}
    />

    <StatCard
      title="未读抄送"
      value={counts.unread_cc}
      icon={Mail}
      color="text-purple-400"
      iconColor="text-purple-400/30"
      {...STAT_CARD_COMMON}
    />

    <StatCard
      title="紧急待办"
      value={counts.urgent}
      icon={AlertTriangle}
      color="text-red-400"
      iconColor="text-red-400/30"
      {...STAT_CARD_COMMON}
    />
  </div>
);

export default StatCards;
