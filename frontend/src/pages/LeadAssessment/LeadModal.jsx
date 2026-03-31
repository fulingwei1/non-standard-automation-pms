/**
 * LeadModal
 * Modal wrapper around <AssessmentForm> for creating / editing a lead.
 */

import { Modal } from 'antd';
import { AssessmentForm } from '../../components/lead-assessment';

const LeadModal = ({ open, editingLead, onSave, onCancel }) => (
  <Modal
    title={editingLead ? '编辑线索' : '新建线索'}
    open={open}
    onCancel={onCancel}
    footer={null}
    width={1000}
  >
    <AssessmentForm lead={editingLead} onSave={onSave} onCancel={onCancel} />
  </Modal>
);

export default LeadModal;
