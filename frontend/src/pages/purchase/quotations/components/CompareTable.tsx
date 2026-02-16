/**
 * 报价比较表格组件
 * @component CompareTable
 */

import React from 'react';
import { Crown, Award } from 'lucide-react';
import { Badge } from '../../../../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../../../components/ui/table';
import type { QuotationCompareResponse } from '../../../../types/purchase';

interface CompareTableProps {
  compareData: QuotationCompareResponse;
}

const CompareTable: React.FC<CompareTableProps> = ({ compareData }) => {
  return (
    <div className="space-y-4">
      {/* 物料信息 */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <h3 className="font-bold text-lg">{compareData.material_name}</h3>
        <p className="text-sm text-gray-500">物料编码: {compareData.material_code}</p>
      </div>

      {/* AI推荐 */}
      <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center gap-2 mb-2">
          <Award className="h-5 w-5 text-blue-600" />
          <h4 className="font-medium">AI 推荐</h4>
        </div>
        <p className="text-sm text-gray-700">{compareData.recommendation_reason}</p>
      </div>

      {/* 比价表格 */}
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>供应商</TableHead>
              <TableHead className="text-right">报价单号</TableHead>
              <TableHead className="text-right">单价</TableHead>
              <TableHead className="text-right">起订量</TableHead>
              <TableHead className="text-right">交货期</TableHead>
              <TableHead>付款条件</TableHead>
              <TableHead className="text-center">绩效评级</TableHead>
              <TableHead className="text-right">绩效分</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {compareData.quotations.map((quote) => {
              const isBestPrice = quote.supplier_id === compareData.best_price_supplier_id;
              const isRecommended = quote.supplier_id === compareData.recommended_supplier_id;

              return (
                <TableRow
                  key={quote.id}
                  className={isRecommended ? 'bg-blue-50' : ''}
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {isRecommended && <Crown className="h-4 w-4 text-yellow-600" />}
                      <div>
                        <div className="font-medium">{quote.supplier_name}</div>
                        <div className="text-sm text-gray-500">{quote.supplier_code}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">{quote.quotation_no}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {isBestPrice && <Badge className="bg-green-600 text-white">最低价</Badge>}
                      <span className="font-bold">
                        {quote.currency} {quote.unit_price.toFixed(2)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">{quote.min_order_qty}</TableCell>
                  <TableCell className="text-right">{quote.lead_time_days} 天</TableCell>
                  <TableCell>{quote.payment_terms}</TableCell>
                  <TableCell className="text-center">
                    {quote.performance_rating && (
                      <Badge
                        className={
                          quote.performance_rating === 'A+' || quote.performance_rating === 'A'
                            ? 'bg-green-600 text-white'
                            : quote.performance_rating === 'B'
                            ? 'bg-blue-500 text-white'
                            : quote.performance_rating === 'C'
                            ? 'bg-yellow-500 text-white'
                            : 'bg-red-500 text-white'
                        }
                      >
                        {quote.performance_rating}
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {quote.performance_score?.toFixed(1)}
                  </TableCell>
                  <TableCell>
                    {isRecommended && (
                      <Badge className="bg-blue-600 text-white">AI 推荐</Badge>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default CompareTable;
