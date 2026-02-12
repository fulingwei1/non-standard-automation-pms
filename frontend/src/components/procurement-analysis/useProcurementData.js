/**
 * 采购分析数据管理自定义 Hook
 * 处理各分析模块的数据获取逻辑
 */
import { useState, useCallback } from 'react';
import { api } from '../../services/api';
import { getDateByRange } from '@/lib/constants/procurementAnalysis';

/**
 * 采购分析数据管理 Hook
 * @param {string} timeRange - 时间范围
 * @returns {object} 数据和加载函数
 */
export function useProcurementData(timeRange) {
  const [loading, setLoading] = useState(false);

  // 各分析模块数据
  const [costTrendData, setCostTrendData] = useState(null);
  const [priceFluctuationData, setPriceFluctuationData] = useState(null);
  const [deliveryPerformanceData, setDeliveryPerformanceData] = useState(null);
  const [requestEfficiencyData, setRequestEfficiencyData] = useState(null);
  const [qualityRateData, setQualityRateData] = useState(null);

  // 获取采购成本趋势
  const loadCostTrend = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/procurement-analysis/cost-trend', {
        params: {
          start_date: getDateByRange(timeRange, 'start'),
          end_date: getDateByRange(timeRange, 'end'),
          group_by: 'month'
        }
      });
      setCostTrendData(response.data?.data || response.data);
    } catch (error) {
      console.error('Failed to load cost trend:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 获取物料价格波动
  const loadPriceFluctuation = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/procurement-analysis/price-fluctuation', {
        params: {
          start_date: getDateByRange(timeRange, 'start'),
          end_date: getDateByRange(timeRange, 'end'),
          limit: 20
        }
      });
      setPriceFluctuationData(response.data?.data || response.data);
    } catch (error) {
      console.error('Failed to load price fluctuation:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 获取供应商交期准时率
  const loadDeliveryPerformance = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/procurement-analysis/delivery-performance', {
        params: {
          start_date: getDateByRange(timeRange, 'start'),
          end_date: getDateByRange(timeRange, 'end')
        }
      });
      setDeliveryPerformanceData(response.data?.data || response.data);
    } catch (error) {
      console.error('Failed to load delivery performance:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 获取采购申请处理时效
  const loadRequestEfficiency = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/procurement-analysis/request-efficiency', {
        params: {
          start_date: getDateByRange(timeRange, 'start'),
          end_date: getDateByRange(timeRange, 'end')
        }
      });
      setRequestEfficiencyData(response.data?.data || response.data);
    } catch (error) {
      console.error('Failed to load request efficiency:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  // 获取物料质量合格率
  const loadQualityRate = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/procurement-analysis/quality-rate', {
        params: {
          start_date: getDateByRange(timeRange, 'start'),
          end_date: getDateByRange(timeRange, 'end')
        }
      });
      setQualityRateData(response.data?.data || response.data);
    } catch (error) {
      console.error('Failed to load quality rate:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  return {
    loading,
    costTrendData,
    priceFluctuationData,
    deliveryPerformanceData,
    requestEfficiencyData,
    qualityRateData,
    loadCostTrend,
    loadPriceFluctuation,
    loadDeliveryPerformance,
    loadRequestEfficiency,
    loadQualityRate,
  };
}
