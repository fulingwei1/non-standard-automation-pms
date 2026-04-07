import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

const TAB_QUOTES = "quotes";
const TAB_MARGIN = "margin";
const TAB_TEMPLATES = "templates";

function getTabFromPath(pathname) {
  if (pathname.includes("/templates")) {
    return TAB_TEMPLATES;
  }
  if (pathname.includes("/margin")) {
    return TAB_MARGIN;
  }
  return TAB_QUOTES;
}

function getBasePath(pathname) {
  if (pathname.startsWith("/sales/")) {
    return "/sales";
  }
  return "/cost-quotes";
}

export default function QuoteManagementCenter() {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(getTabFromPath(location.pathname));

  useEffect(() => {
    setActiveTab(getTabFromPath(location.pathname));
  }, [location.pathname]);

  const basePath = getBasePath(location.pathname);
  const tabs = useMemo(
    () => [
      { value: TAB_QUOTES, label: "报价管理", path: `${basePath}/quotes` },
      { value: TAB_MARGIN, label: "毛利分析", path: `${basePath}/margin` },
      { value: TAB_TEMPLATES, label: "报价模板", path: `${basePath}/templates` }
    ],
    [basePath]
  );

  const handleTabChange = (value) => {
    const target = (tabs || []).find((tab) => tab.value === value);
    if (target) {
      navigate(target.path);
      setActiveTab(value);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="报价管理"
        description="统一管理报价与报价模板"
      />

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-3">
          {(tabs || []).map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={TAB_QUOTES} className="space-y-6">
          <QuoteManagement embedded />
        </TabsContent>

        <TabsContent value={TAB_MARGIN} className="space-y-6">
          <MarginAnalysis />
        </TabsContent>

        <TabsContent value={TAB_TEMPLATES} className="space-y-6">
          <SalesTemplateCenter embedded />
        </TabsContent>
      </Tabs>
    </div>
  );
}
