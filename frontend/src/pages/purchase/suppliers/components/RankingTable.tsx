/**
 * 供应商排名表格组件
 * @component RankingTable
 */

import React from 'react';
import { Medal } from 'lucide-react';
import { Badge } from '../../../../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../../../components/ui/table';
import type { SupplierRanking } from '../../../../types/purchase';

interface RankingTableProps {
  rankings: SupplierRanking[];
}

const RATING_CONFIG = {
  'A+': { color: 'bg-green-600 text-white', label: 'A+' },
  'A': { color: 'bg-green-500 text-white', label: 'A' },
  'B': { color: 'bg-blue-500 text-white', label: 'B' },
  'C': { color: 'bg-yellow-500 text-white', label: 'C' },
  'D': { color: 'bg-red-500 text-white', label: 'D' },
};

const RankingTable: React.FC<RankingTableProps> = ({ rankings }) => {
  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Medal className="h-5 w-5 text-yellow-500" />;
    if (rank === 2) return <Medal className="h-5 w-5 text-gray-400" />;
    if (rank === 3) return <Medal className="h-5 w-5 text-orange-600" />;
    return null;
  };

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">排名</TableHead>
            <TableHead>供应商</TableHead>
            <TableHead className="text-center">评级</TableHead>
            <TableHead className="text-right">综合得分</TableHead>
            <TableHead className="text-right">准时率</TableHead>
            <TableHead className="text-right">质量率</TableHead>
            <TableHead className="text-right">价格竞争力</TableHead>
            <TableHead className="text-right">响应速度</TableHead>
            <TableHead className="text-right">订单数</TableHead>
            <TableHead className="text-right">总金额</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rankings.map((ranking) => (
            <TableRow
              key={ranking.supplier_id}
              className={ranking.rank <= 3 ? 'bg-blue-50' : ''}
            >
              <TableCell>
                <div className="flex items-center gap-2">
                  {getRankIcon(ranking.rank)}
                  <span className="font-bold">{ranking.rank}</span>
                </div>
              </TableCell>
              <TableCell>
                <div>
                  <div className="font-medium">{ranking.supplier_name}</div>
                  <div className="text-sm text-gray-500">{ranking.supplier_code}</div>
                </div>
              </TableCell>
              <TableCell className="text-center">
                <Badge className={RATING_CONFIG[ranking.rating].color}>
                  {RATING_CONFIG[ranking.rating].label}
                </Badge>
              </TableCell>
              <TableCell className="text-right">
                <span className="font-bold text-blue-600">
                  {ranking.overall_score.toFixed(1)}
                </span>
              </TableCell>
              <TableCell className="text-right">
                {ranking.on_time_delivery_rate.toFixed(1)}%
              </TableCell>
              <TableCell className="text-right">
                {ranking.quality_pass_rate.toFixed(1)}%
              </TableCell>
              <TableCell className="text-right">
                {ranking.price_competitiveness.toFixed(1)}
              </TableCell>
              <TableCell className="text-right">
                {ranking.response_speed_score.toFixed(1)}
              </TableCell>
              <TableCell className="text-right">{ranking.total_orders}</TableCell>
              <TableCell className="text-right">
                ¥{ranking.total_amount.toLocaleString()}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default RankingTable;
