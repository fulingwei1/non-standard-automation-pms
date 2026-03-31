/**
 * useLeadData
 * Manages lead list data, follow-ups, monthly stats, filters, and CRUD
 * actions for the LeadAssessment page.
 */

import { useState, useMemo, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { leadApi } from '../../../services/api/sales';
import {
  ASSESSMENT_CRITERIA,
  BUDGET_RANGES,
  DECISION_MAKER_ROLES,
  DEFAULT_FILTERS,
} from '../../../lib/constants/leadAssessment';
import { mapLeadFromApi, mapFollowUpFromApi } from '../constants';

// ---------------------------------------------------------------------------
// Score calculation (pure function, exported for reuse in sub-components)
// ---------------------------------------------------------------------------
export const calculateLeadScore = (lead) => {
  let totalScore = 0;

  const budgetScore =
    (BUDGET_RANGES.find((b) => b.value === lead.budget)?.weight || 0) * 5;
  totalScore += budgetScore * ASSESSMENT_CRITERIA.BUDGET.weight;

  const authorityScore =
    DECISION_MAKER_ROLES[lead.authority?.toUpperCase()]?.weight || 0;
  totalScore += authorityScore * ASSESSMENT_CRITERIA.AUTHORITY.weight;

  const needScore =
    lead.need === 'urgent' ? 5 : lead.need === 'moderate' ? 3 : 1;
  totalScore += needScore * ASSESSMENT_CRITERIA.NEED.weight;

  const timeScore =
    lead.timeline === 'immediate' ? 5 : lead.timeline === 'quarter' ? 3 : 1;
  totalScore += timeScore * ASSESSMENT_CRITERIA.TIMELINE.weight;

  // Simplified competition score (assumed medium competition)
  const competitionScore = 3;
  totalScore += competitionScore * ASSESSMENT_CRITERIA.COMPETITION.weight;

  return Math.round(totalScore);
};

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------
export function useLeadData() {
  const [loading, setLoading] = useState(false);
  const [leads, setLeads] = useState([]);
  const [followUps, setFollowUps] = useState([]);
  const [overdueFollowUps, setOverdueFollowUps] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState({
    growth: 0,
    newLeads: 0,
    convertedLeads: 0,
  });
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [searchText, setSearchText] = useState('');

  // -------------------------------------------------------------------------
  // Data loading
  // -------------------------------------------------------------------------
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const leadsRes = await leadApi.list({
        source: filters.source || undefined,
        status: filters.status || undefined,
        qualification: filters.qualification || undefined,
        industry: filters.industry || undefined,
      });

      const leadsRaw = leadsRes.data?.items || leadsRes.data || [];
      const mappedLeads = (leadsRaw || []).map(mapLeadFromApi);
      setLeads(mappedLeads);

      // Collect follow-ups for first 20 leads to avoid excessive requests
      const allFollowUps = [];
      for (const lead of mappedLeads.slice(0, 20)) {
        try {
          const fuRes = await leadApi.getFollowUps(lead.id);
          const fuRaw = fuRes.data?.items || fuRes.data || [];
          (fuRaw || []).forEach((fu) => {
            allFollowUps.push(mapFollowUpFromApi(fu, lead));
          });
        } catch (_e) {
          // skip individual failures silently
        }
      }

      const now = new Date();
      setFollowUps(
        (allFollowUps || []).filter((fu) => fu.status !== 'overdue'),
      );
      setOverdueFollowUps(
        (allFollowUps || []).filter((fu) => {
          if (fu.status === 'overdue') return true;
          return (
            fu.dueDate &&
            new Date(fu.dueDate) < now &&
            fu.status === 'pending'
          );
        }),
      );

      // Compute month-over-month growth on the client side
      const thisMonth = new Date();
      const lastMonth = new Date(thisMonth);
      lastMonth.setMonth(lastMonth.getMonth() - 1);
      const thisMonthStr = `${thisMonth.getFullYear()}-${String(thisMonth.getMonth() + 1).padStart(2, '0')}`;
      const lastMonthStr = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, '0')}`;

      const thisMonthLeads = (mappedLeads || []).filter((l) =>
        (l.createdAt || '').startsWith(thisMonthStr),
      );
      const lastMonthLeads = (mappedLeads || []).filter((l) =>
        (l.createdAt || '').startsWith(lastMonthStr),
      );
      const convertedLeads = (mappedLeads || []).filter(
        (l) => l.status === 'converted' || l.qualification === 'converted',
      );

      const growth =
        lastMonthLeads.length > 0
          ? ((thisMonthLeads.length - lastMonthLeads.length) /
              lastMonthLeads.length) *
            100
          : 0;

      setMonthlyStats({
        growth: parseFloat(growth.toFixed(1)),
        newLeads: thisMonthLeads.length,
        convertedLeads: convertedLeads.length,
      });
    } catch (_error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // -------------------------------------------------------------------------
  // Derived / filtered leads
  // -------------------------------------------------------------------------
  const filteredLeads = useMemo(() => {
    return (leads || []).filter((lead) => {
      const searchLower = searchText.toLowerCase();
      const matchesSearch =
        !searchText ||
        (lead.companyName || '').toLowerCase().includes(searchLower) ||
        (lead.contactPerson || '').toLowerCase().includes(searchLower) ||
        (lead.phone || '').includes(searchText);

      const matchesSource =
        !filters.source || lead.source === filters.source;
      const matchesStatus =
        !filters.status || lead.status === filters.status;
      const matchesQualification =
        !filters.qualification ||
        lead.qualification === filters.qualification;
      const matchesIndustry =
        !filters.industry || lead.industry === filters.industry;

      return (
        matchesSearch &&
        matchesSource &&
        matchesStatus &&
        matchesQualification &&
        matchesIndustry
      );
    });
  }, [leads, searchText, filters]);

  // -------------------------------------------------------------------------
  // CRUD event handlers
  // -------------------------------------------------------------------------
  const handleDeleteLead = useCallback(
    async (leadId) => {
      try {
        setLoading(true);
        await leadApi.update(leadId, { status: 'INVALID' });
        setLeads((prev) => (prev || []).filter((l) => l.id !== leadId));
        message.success('删除成功');
      } catch (_error) {
        message.error('删除失败');
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  const handleSaveLead = useCallback(
    (lead) => {
      if (lead.id) {
        setLeads((prev) =>
          (prev || []).map((l) =>
            l.id === lead.id
              ? { ...lead, score: calculateLeadScore(lead) }
              : l,
          ),
        );
      } else {
        const newLead = {
          ...lead,
          id: Date.now(),
          score: calculateLeadScore(lead),
          createdAt: new Date().toISOString().split('T')[0],
        };
        setLeads((prev) => [...(prev || []), newLead]);
      }
      loadData();
    },
    [loadData],
  );

  const handleConvertLead = useCallback((lead) => {
    message.success(`正在转化线索: ${lead.companyName}`);
  }, []);

  const handleExportLeads = useCallback((format) => {
    message.success(`正在导出${format}格式线索数据...`);
  }, []);

  return {
    // state
    loading,
    leads,
    filteredLeads,
    followUps,
    overdueFollowUps,
    monthlyStats,
    filters,
    searchText,
    // setters
    setFilters,
    setSearchText,
    // actions
    loadData,
    handleDeleteLead,
    handleSaveLead,
    handleConvertLead,
    handleExportLeads,
  };
}
