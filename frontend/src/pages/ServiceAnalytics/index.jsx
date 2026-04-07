import { useServiceAnalytics } from "./hooks/useServiceAnalytics";

export default function ServiceAnalytics() {
  const { analytics, loading, error, period, setPeriod, reload } =
    useServiceAnalytics();

  if (loading && !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="服务数据分析" />
        <div className="container mx-auto px-4 py-6">
          <LoadingCard rows={5} />
        </div>
      </div>
    );
  }

  if (error && !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="服务数据分析" />
        <div className="container mx-auto px-4 py-6">
          <ErrorMessage error={error} onRetry={reload} />
        </div>
      </div>
    );
  }

  if (!analytics) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="服务数据分析"
        description="分析服务数据，了解服务质量和效率"
        actions={
          <AnalyticsToolbar
            analytics={analytics}
            period={period}
            setPeriod={setPeriod}
            loading={loading}
            onRefresh={reload}
          />
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        <ServiceOverview analytics={analytics} />
        <ServiceCharts analytics={analytics} />
        <ServicePerformance analytics={analytics} />
        <ServiceTrends analytics={analytics} />
      </div>
    </div>
  );
}
