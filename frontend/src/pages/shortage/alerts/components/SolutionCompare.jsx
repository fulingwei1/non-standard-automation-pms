/**
 * 方案对比表格组件
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SOLUTION_TYPES, getScoreColor } from '../../constants';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { BarChart } from 'lucide-react';

const SolutionCompare = ({ solutions = [] }) => {
  if (solutions.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart className="h-5 w-5" />
          方案对比
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>方案类型</TableHead>
                <TableHead className="text-center">AI评分</TableHead>
                <TableHead className="text-center">可行性</TableHead>
                <TableHead className="text-center">成本</TableHead>
                <TableHead className="text-center">时间</TableHead>
                <TableHead className="text-center">风险</TableHead>
                <TableHead className="text-right">预计成本</TableHead>
                <TableHead className="text-right">预计交期</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(solutions || []).map((solution) => {
                const solutionType = SOLUTION_TYPES[solution.solution_type] || {};
                
                return (
                  <TableRow 
                    key={solution.id}
                    className={solution.is_recommended ? 'bg-yellow-50' : ''}
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <span>{solutionType.icon}</span>
                        <span className={solutionType.color}>
                          {solutionType.label}
                        </span>
                        {solution.is_recommended && (
                          <Badge variant="secondary" className="bg-yellow-400 text-white">
                            推荐
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <ScoreCell score={solution.ai_score} />
                    </TableCell>
                    <TableCell className="text-center">
                      <ScoreCell score={solution.feasibility_score} />
                    </TableCell>
                    <TableCell className="text-center">
                      <ScoreCell score={solution.cost_score} />
                    </TableCell>
                    <TableCell className="text-center">
                      <ScoreCell score={solution.time_score} />
                    </TableCell>
                    <TableCell className="text-center">
                      <ScoreCell score={solution.risk_score} />
                    </TableCell>
                    <TableCell className="text-right font-semibold text-orange-600">
                      ¥{parseFloat(solution.estimated_cost || 0).toLocaleString()}
                    </TableCell>
                    <TableCell className="text-right font-semibold text-blue-600">
                      {solution.estimated_lead_time} 天
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
};

// 评分单元格组件
const ScoreCell = ({ score }) => {
  const color = getScoreColor(score);
  
  return (
    <span 
      className="font-semibold px-2 py-1 rounded"
      style={{ 
        color,
        backgroundColor: `${color}15`
      }}
    >
      {score}
    </span>
  );
};

export default SolutionCompare;
