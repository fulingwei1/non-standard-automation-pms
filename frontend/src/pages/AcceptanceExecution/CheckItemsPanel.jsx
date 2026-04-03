import { Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { cn, formatDate } from '../../lib/utils';
import { resultStatusConfigs } from './constants';

/**
 * Left panel: grouped check items by category.
 * Clicking an item opens the UpdateItemDialog via onItemClick.
 */
export function CheckItemsPanel({ itemsByCategory, onItemClick, onAddIssue }) {
    return (
        <Card className="md:col-span-2">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle>检查项</CardTitle>
                    <Button variant="outline" size="sm" onClick={onAddIssue}>
                        <Plus className="w-4 h-4 mr-2" />
                        上报问题
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-6">
                    {Object.entries(itemsByCategory).map(([category, categoryItems]) => (
                        <div key={category}>
                            <div className="font-medium mb-3 flex items-center justify-between">
                                <span>{category}</span>
                                <Badge variant="outline">
                                    {(categoryItems || []).filter((i) => i.result_status === 'PASSED').length}
                                    {' '}/ {categoryItems.length}
                                </Badge>
                            </div>
                            <div className="space-y-2">
                                {(categoryItems || []).map((item) => (
                                    <CheckItemRow
                                        key={item.id}
                                        item={item}
                                        onClick={() => onItemClick(item)}
                                    />
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

function CheckItemRow({ item, onClick }) {
    return (
        <div
            className={cn(
                'border rounded-lg p-3 cursor-pointer hover:bg-slate-50 transition-colors',
                item.result_status === 'PASSED' && 'bg-emerald-50 border-emerald-200',
                item.result_status === 'FAILED' && 'bg-red-50 border-red-200',
                item.result_status === 'PENDING' && 'bg-slate-50 border-slate-200',
            )}
            onClick={onClick}
        >
            <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                    <div className="font-medium text-sm">{item.item_name}</div>
                    <div className="text-xs text-slate-500 mt-1">
                        {item.item_code}{' '}
                        {item.is_key_item && (
                            <Badge variant="destructive" className="ml-1">
                                关键项
                            </Badge>
                        )}
                    </div>
                </div>
                <Badge
                    className={resultStatusConfigs[item.result_status]?.color || 'bg-slate-500'}
                >
                    {resultStatusConfigs[item.result_status]?.label || item.result_status}
                </Badge>
            </div>

            {item.acceptance_criteria && (
                <div className="text-xs text-slate-500 mb-1">
                    验收标准: {item.acceptance_criteria}
                </div>
            )}
            {item.standard_value && (
                <div className="text-xs text-slate-500 mb-1">
                    标准值: {item.standard_value}{item.unit && ` ${item.unit}`}
                </div>
            )}
            {item.actual_value && (
                <div className="text-xs font-medium">
                    实际值: {item.actual_value}{item.unit && ` ${item.unit}`}
                </div>
            )}
            {item.checked_at && (
                <div className="text-xs text-slate-400 mt-1">
                    检查时间: {formatDate(item.checked_at)}
                </div>
            )}
        </div>
    );
}
