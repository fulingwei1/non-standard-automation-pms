/**
 * LeadAssessment page-local constants
 * Shared domain constants (LEAD_SOURCES, LEAD_STATUS, etc.) live in
 * @/lib/constants/leadAssessment and are imported from there.
 */

// ---------------------------------------------------------------------------
// Pre-existing page constants (assessment status / result display configs)
// ---------------------------------------------------------------------------
export const statusConfigs = {
  pending: { label: '待评估', color: 'bg-slate-500' },
  in_progress: { label: '评估中', color: 'bg-blue-500' },
  completed: { label: '已完成', color: 'bg-emerald-500' },
};

export const resultConfigs = {
  qualified: { label: '合格', color: 'bg-emerald-500' },
  unqualified: { label: '不合格', color: 'bg-red-500' },
  pending: { label: '待定', color: 'bg-amber-500' },
};

// ---------------------------------------------------------------------------
// Tab definitions used by index.jsx
// ---------------------------------------------------------------------------
export const TAB_KEYS = {
  OVERVIEW: 'overview',
  LEADS: 'leads',
  ASSESSMENT: 'assessment',
  SCORING: 'scoring',
  FOLLOW_UPS: 'followups',
};

// ---------------------------------------------------------------------------
// Lead field mapping helper (backend → frontend normalisation)
// ---------------------------------------------------------------------------
export const mapLeadFromApi = (lead) => ({
  id: lead.id,
  companyName: lead.company_name || lead.companyName || '',
  contactPerson: lead.contact_person || lead.contactPerson || '',
  position: lead.position || '',
  phone: lead.phone || '',
  email: lead.email || '',
  industry: lead.industry || '',
  companySize: lead.company_size || lead.companySize || '',
  source: lead.source || '',
  status: lead.status?.toLowerCase() || '',
  qualification: lead.qualification?.toLowerCase() || '',
  score: lead.score || 0,
  budget: lead.budget || '',
  authority: lead.authority || '',
  need: lead.need || '',
  timeline: lead.timeline || '',
  address: lead.address || '',
  createdAt: lead.created_at || lead.createdAt || '',
  lastContact: lead.last_contact || lead.lastContact || '',
  description: lead.description || '',
});

// ---------------------------------------------------------------------------
// Follow-up field mapping helper
// ---------------------------------------------------------------------------
export const mapFollowUpFromApi = (fu, lead) => ({
  id: fu.id,
  leadId: lead.id,
  leadCompany: lead.companyName,
  type: fu.type || fu.follow_up_type || 'call',
  description: fu.description || fu.content || '',
  dueDate: fu.due_date || fu.dueDate || '',
  status: fu.status?.toLowerCase() || 'pending',
});
