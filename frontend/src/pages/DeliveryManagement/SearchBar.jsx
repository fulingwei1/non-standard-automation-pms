/**
 * SearchBar — keyword search card for the delivery list view
 */

import { Search } from "lucide-react";
import { Card, CardContent, Input } from "../../components/ui";

const SearchBar = ({ value, onChange }) => (
  <Card className="mb-4 bg-surface-100/50">
    <CardContent className="p-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          placeholder="搜索订单号、客户名称..."
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          className="pl-10 bg-surface-100 border-white/10 max-w-md"
        />
      </div>
    </CardContent>
  </Card>
);

export default SearchBar;
