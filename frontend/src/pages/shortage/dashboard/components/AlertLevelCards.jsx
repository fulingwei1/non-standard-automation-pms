/**
 * 预警级别统计卡片组件
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { ALERT_LEVELS } from '../../constants';

const AlertLevelCards = ({ stats = {}, onLevelClick }) => {
  const levels = ['URGENT', 'CRITICAL', 'WARNING', 'INFO'];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {(levels || []).map((level) => {
        const config = ALERT_LEVELS[level];
        const count = stats[level] || 0;

        return (
          <Card
            key={level}
            className={`cursor-pointer hover:shadow-lg transition-shadow ${config.borderColor} border-2`}
            onClick={() => onLevelClick?.(level)}
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{config.icon}</span>
                    <h3 className={`font-semibold ${config.textColor}`}>
                      {config.label}
                    </h3>
                  </div>
                  <p className="text-3xl font-bold mb-1" style={{ color: config.color }}>
                    {count}
                  </p>
                  <p className="text-xs text-gray-500">{config.description}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    响应时间: {config.responseTime}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default AlertLevelCards;
