/**
 * 快速扫描按钮组件
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Loader2, Scan } from 'lucide-react';
import { triggerScan } from '@/services/api/shortage';
import { toast } from '@/hooks/use-toast';

const QuickScanButton = ({ onScanComplete }) => {
  const [scanning, setScanning] = useState(false);

  const handleScan = async () => {
    try {
      setScanning(true);
      const response = await triggerScan({ days_ahead: 30 });
      
      toast({
        title: '扫描完成',
        description: `已生成 ${response.data.alerts_generated} 条预警`,
      });
      
      onScanComplete?.(response.data);
    } catch (error) {
      toast({
        title: '扫描失败',
        description: error.message || '请稍后重试',
        variant: 'destructive',
      });
    } finally {
      setScanning(false);
    }
  };

  return (
    <Button
      onClick={handleScan}
      disabled={scanning}
      size="lg"
      className="bg-blue-600 hover:bg-blue-700"
    >
      {scanning ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          扫描中...
        </>
      ) : (
        <>
          <Scan className="mr-2 h-4 w-4" />
          快速扫描 (未来30天)
        </>
      )}
    </Button>
  );
};

export default QuickScanButton;
