/**
 * 算法选择器组件
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { FORECAST_ALGORITHMS } from '../../constants';
import { Settings } from 'lucide-react';

const AlgorithmSelector = ({ value, onChange }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          预测算法选择
        </CardTitle>
      </CardHeader>
      <CardContent>
        <RadioGroup value={value} onValueChange={onChange}>
          <div className="space-y-4">
            {Object.entries(FORECAST_ALGORITHMS).map(([key, config]) => (
              <div
                key={key}
                className={`flex items-start gap-3 p-4 rounded-lg border-2 transition-all cursor-pointer hover:border-blue-300 ${
                  value === config.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200'
                }`}
                onClick={() => onChange(config.value)}
              >
                <RadioGroupItem value={config.value} id={key} />
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xl">{config.icon}</span>
                    <Label htmlFor={key} className="font-semibold cursor-pointer">
                      {config.label}
                    </Label>
                    {config.recommended && (
                      <Badge variant="secondary" className="bg-blue-500 text-white">
                        推荐
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">{config.description}</p>
                </div>
              </div>
            ))}
          </div>
        </RadioGroup>
      </CardContent>
    </Card>
  );
};

export default AlgorithmSelector;
