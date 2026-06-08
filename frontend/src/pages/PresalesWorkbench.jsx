import { Link, useLocation } from "react-router-dom";
import {
  ClipboardList,
  FileText,
  Gauge,
  Layers,
  LineChart,
  Settings,
  Users,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "../components/ui";

const roleEntries = [
  {
    title: "销售协同",
    summary: "商机需求、售前支持申请、方案和 G2 阶段门。",
    to: "/presales/workbench/sales",
    icon: Gauge,
    tag: "商机到方案",
  },
  {
    title: "售前执行",
    summary: "我的工单、需求评估、方案设计、成本估算和交付物。",
    to: "/presales/workbench/execution",
    icon: ClipboardList,
    tag: "评估到交付",
  },
  {
    title: "经理调度",
    summary: "工单池、工程师负荷、超期风险和方案评审。",
    to: "/presales/workbench/manager",
    icon: Users,
    tag: "负荷与风险",
  },
];

const processLinks = [
  { label: "技术方案", to: "/presales/technical-solutions?tab=solutions", icon: FileText },
  { label: "成本估算", to: "/presales/technical-solutions?tab=cost", icon: LineChart },
  { label: "模板库", to: "/presales/technical-solutions?tab=knowledge", icon: Layers },
  { label: "技术参数", to: "/presales/technical-solutions?tab=parameters", icon: Settings },
];

function mergeCurrentSearch(to, currentSearch) {
  if (!currentSearch) {
    return to;
  }

  const [pathname, rawSearch = ""] = to.split("?");
  const nextParams = new URLSearchParams(rawSearch);
  const currentParams = new URLSearchParams(currentSearch);

  currentParams.forEach((value, key) => {
    if (!nextParams.has(key)) {
      nextParams.append(key, value);
    }
  });

  const nextSearch = nextParams.toString();
  return nextSearch ? `${pathname}?${nextSearch}` : pathname;
}

export default function PresalesWorkbench() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-950 px-4 py-5 text-white sm:px-6 sm:py-6">
      <PageHeader
        title="售前技术支持工作台"
        description="商机需求、技术评估、方案成本和经理调度集中处理。"
      />

      <div className="space-y-6">
        <div className="grid gap-4 lg:grid-cols-3">
          {roleEntries.map((entry) => {
            const Icon = entry.icon;
            return (
              <Card key={entry.title} className="border-gray-800 bg-gray-900">
                <CardHeader className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-500/15 text-violet-300">
                      <Icon className="h-5 w-5" />
                    </span>
                    <Badge variant="outline" className="border-gray-700 text-gray-300">
                      {entry.tag}
                    </Badge>
                  </div>
                  <div>
                    <CardTitle className="text-lg text-white">{entry.title}</CardTitle>
                    <p className="mt-2 text-sm leading-6 text-gray-400">{entry.summary}</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <Button asChild className="w-full bg-violet-600 hover:bg-violet-500">
                    <Link to={mergeCurrentSearch(entry.to, location.search)}>进入</Link>
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <Card className="border-gray-800 bg-gray-900">
          <CardHeader>
            <CardTitle className="text-base text-white">常用售前资产</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {processLinks.map((item) => {
                const Icon = item.icon;
                return (
                  <Button
                    key={item.label}
                    asChild
                    variant="outline"
                    className="justify-start border-gray-700 bg-gray-950 text-gray-200 hover:bg-gray-800"
                  >
                    <Link to={mergeCurrentSearch(item.to, location.search)}>
                      <Icon className="mr-2 h-4 w-4" />
                      {item.label}
                    </Link>
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
