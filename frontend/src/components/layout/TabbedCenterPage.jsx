import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { usePermission } from "../../hooks/usePermission";

function getValidTab(tabs, tabValue) {
  if ((tabs || []).some((tab) => tab.value === tabValue)) {
    return tabValue;
  }
  return null;
}

export default function TabbedCenterPage({
  title,
  description,
  tabs,
  defaultTab,
  showHeader = true,
}) {
  const normalizedTabs = useMemo(() => (tabs || []).filter(Boolean), [tabs]);
  const { hasPermission, hasAnyPermission } = usePermission();
  const [searchParams, setSearchParams] = useSearchParams();
  const searchTab = searchParams.get("tab");
  const visibleTabs = useMemo(
    () =>
      normalizedTabs.filter((tab) => {
        if (Array.isArray(tab.permissionAny) && tab.permissionAny.length > 0) {
          return hasAnyPermission(tab.permissionAny);
        }
        if (tab.permission) {
          return hasPermission(tab.permission);
        }
        return true;
      }),
    [normalizedTabs, hasAnyPermission, hasPermission],
  );
  const fallbackTab =
    getValidTab(visibleTabs, defaultTab) || visibleTabs[0]?.value || "";
  const [activeTab, setActiveTab] = useState(
    getValidTab(visibleTabs, searchTab) || fallbackTab,
  );

  useEffect(() => {
    setActiveTab(getValidTab(visibleTabs, searchTab) || fallbackTab);
  }, [fallbackTab, searchTab, visibleTabs]);

  const handleTabChange = (value) => {
    const nextParams = new URLSearchParams(searchParams);
    nextParams.set("tab", value);
    setSearchParams(nextParams, { replace: true });
    setActiveTab(value);
  };

  if (!fallbackTab) {
    return (
      <div className="space-y-6">
        {showHeader ? <PageHeader title={title} description={description} /> : null}
        <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-6 text-sm text-slate-400">
          当前账号没有可访问的中心页签。
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {showHeader ? <PageHeader title={title} description={description} /> : null}

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList
          className="grid w-full"
          style={{
            gridTemplateColumns: `repeat(${visibleTabs.length}, minmax(0, 1fr))`,
          }}
        >
          {visibleTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {visibleTabs.map((tab) => (
          <TabsContent key={tab.value} value={tab.value} className="space-y-6">
            {activeTab === tab.value ? tab.render() : null}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
