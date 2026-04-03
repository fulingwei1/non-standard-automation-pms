/**
 * LeadAssessment — page orchestrator
 * Composes sub-components and delegates state to useLeadData.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Tabs, message } from 'antd';
import {
  BarChart3,
  Users,
  Award,
  Target,
  MessageSquare,
} from 'lucide-react';

import {
  LeadOverview,
  LeadList,
  AssessmentForm,
  ScoringEngine,
  FollowUpManager,
} from '../../components/lead-assessment';

import { ASSESSMENT_CRITERIA } from '../../lib/constants/leadAssessment';

import { useLeadData } from './hooks/useLeadData';
import { TAB_KEYS } from './constants';
import PageHeader from './PageHeader';
import FilterBar from './FilterBar';
import LeadModal from './LeadModal';

const LeadAssessment = () => {
  const {
    loading,
    leads,
    filteredLeads,
    followUps,
    overdueFollowUps,
    monthlyStats,
    filters,
    searchText,
    setFilters,
    setSearchText,
    loadData,
    handleDeleteLead,
    handleSaveLead,
    handleConvertLead,
    handleExportLeads,
  } = useLeadData();

  const [activeTab, setActiveTab] = useState(TAB_KEYS.OVERVIEW);
  const [viewLayout, setViewLayout] = useState('grid');
  const [showAssessmentModal, setShowAssessmentModal] = useState(false);
  const [editingLead, setEditingLead] = useState(null);

  // -------------------------------------------------------------------------
  // Local UI handlers
  // -------------------------------------------------------------------------
  const handleCreateLead = () => {
    setEditingLead(null);
    setShowAssessmentModal(true);
  };

  const handleEditLead = (lead) => {
    setEditingLead(lead);
    setShowAssessmentModal(true);
  };

  const handleAssessLead = (lead) => {
    setEditingLead(lead);
    setActiveTab(TAB_KEYS.ASSESSMENT);
  };

  const handleModalSave = (lead) => {
    handleSaveLead(lead);
    setShowAssessmentModal(false);
    setEditingLead(null);
  };

  const handleModalCancel = () => {
    setShowAssessmentModal(false);
    setEditingLead(null);
  };

  const handleFilterChange = (patch) => {
    setFilters((prev) => ({ ...prev, ...patch }));
  };

  // -------------------------------------------------------------------------
  // Tab items
  // -------------------------------------------------------------------------
  const tabItems = [
    {
      key: TAB_KEYS.OVERVIEW,
      label: (
        <span>
          <BarChart3 size={16} />
          概览分析
        </span>
      ),
      children: (
        <LeadOverview
          data={{ leads, followUps, overdueFollowUps, monthlyStats }}
          loading={loading}
          onNavigate={(type) => {
            if (type === 'hot-leads') {
              setFilters((prev) => ({ ...prev, qualification: 'hot' }));
              setActiveTab(TAB_KEYS.LEADS);
            } else if (type === 'follow-ups') {
              setActiveTab(TAB_KEYS.FOLLOW_UPS);
            } else if (type === 'overdue') {
              setFilters((prev) => ({ ...prev, status: 'overdue' }));
              setActiveTab(TAB_KEYS.LEADS);
            }
          }}
        />
      ),
    },
    {
      key: TAB_KEYS.LEADS,
      label: (
        <span>
          <Users size={16} />
          线索列表 ({filteredLeads.length})
        </span>
      ),
      children: (
        <LeadList
          leads={filteredLeads}
          loading={loading}
          onEdit={handleEditLead}
          onDelete={handleDeleteLead}
          onAssess={handleAssessLead}
          onConvert={handleConvertLead}
        />
      ),
    },
    {
      key: TAB_KEYS.ASSESSMENT,
      label: (
        <span>
          <Award size={16} />
          评估表单
        </span>
      ),
      children: (
        <AssessmentForm
          lead={editingLead}
          onSave={(lead) => {
            handleSaveLead(lead);
            setEditingLead(null);
          }}
          onCancel={() => setEditingLead(null)}
        />
      ),
    },
    {
      key: TAB_KEYS.SCORING,
      label: (
        <span>
          <Target size={16} />
          评分引擎
        </span>
      ),
      children: (
        <ScoringEngine
          leads={leads}
          criteria={ASSESSMENT_CRITERIA}
          onReScore={(updatedLeads) => {
            // Surface updated leads back through the hook's setter indirectly
            // by calling loadData; parent state is managed by useLeadData.
            loadData();
            message.success('重新评分完成');
          }}
        />
      ),
    },
    {
      key: TAB_KEYS.FOLLOW_UPS,
      label: (
        <span>
          <MessageSquare size={16} />
          跟进管理
        </span>
      ),
      children: (
        <FollowUpManager
          followUps={[...followUps, ...overdueFollowUps]}
          leads={leads}
          loading={loading}
          onRefresh={loadData}
        />
      ),
    },
  ];

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="lead-assessment-container"
      style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}
    >
      <PageHeader
        viewLayout={viewLayout}
        onViewLayoutChange={setViewLayout}
        onCreateLead={handleCreateLead}
      />

      <FilterBar
        searchText={searchText}
        filters={filters}
        onSearch={setSearchText}
        onFilterChange={handleFilterChange}
      />

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        style={{ marginBottom: '24px' }}
        items={tabItems}
      />

      <LeadModal
        open={showAssessmentModal}
        editingLead={editingLead}
        onSave={handleModalSave}
        onCancel={handleModalCancel}
      />
    </motion.div>
  );
};

export default LeadAssessment;
