import { Loader2 } from "lucide-react";

const EmptyState = ({ items, loading, icon: Icon, message }) => (
  <>
    {items?.length === 0 && !loading && (
      <div className="text-center py-12 text-slate-400">
        <Icon className="h-12 w-12 mx-auto mb-2" />
        <p>{message}</p>
      </div>
    )}

    {loading && (
      <div className="text-center py-12">
        <Loader2 className="h-8 w-8 mx-auto animate-spin text-primary" />
      </div>
    )}
  </>
);

export default EmptyState;
