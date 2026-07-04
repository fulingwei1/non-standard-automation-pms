const INITIATION_STATUS_PRIORITY = {
  APPROVED: 0,
  SUBMITTED: 1,
  REVIEWING: 1,
  IN_REVIEW: 1,
  DRAFT: 2,
  REJECTED: 3,
  CANCELLED: 4,
};

const getStatusPriority = (status) =>
  INITIATION_STATUS_PRIORITY[String(status || "").toUpperCase()] ?? 2;

const getSortTime = (item) =>
  Date.parse(item?.updated_at || item?.created_at || item?.apply_time || "") || 0;

const firstNonEmpty = (...values) =>
  values.find((value) => value !== undefined && value !== null && value !== "") || "";

const appendIfPresent = (params, key, value) => {
  const normalized = firstNonEmpty(value);
  if (normalized !== "") {
    params.set(key, String(normalized));
  }
};

export const pickExistingInitiationByContractNo = (items, contractNo) => {
  if (!contractNo || !Array.isArray(items)) {
    return null;
  }

  const matches = items.filter(
    (item) => String(item?.contract_no || "") === String(contractNo),
  );

  if (matches.length === 0) {
    return null;
  }

  return matches.sort((left, right) => {
    const priorityDelta =
      getStatusPriority(left.status) - getStatusPriority(right.status);
    if (priorityDelta !== 0) {
      return priorityDelta;
    }
    return getSortTime(right) - getSortTime(left);
  })[0];
};

export const buildContractInitiationPath = (contract = {}) => {
  const contractNo = firstNonEmpty(
    contract.contract_no,
    contract.contractNo,
    contract.contract_code,
    contract.customer_contract_no,
    contract.contract_id,
    contract.id,
  );
  const projectName = firstNonEmpty(
    contract.project_name,
    contract.projectName,
    contract.contract_name,
    contract.contractName,
    contract.title,
    contractNo,
  );
  const customerName = firstNonEmpty(
    contract.customer_name,
    contract.customerName,
    contract.client_name,
    contract.clientName,
    contract.customer?.customer_name,
    contract.customer?.name,
  );
  const contractAmount = firstNonEmpty(
    contract.contract_amount,
    contract.contractAmount,
    contract.total_amount,
    contract.totalAmount,
    contract.value,
    contract.amount,
  );
  const requiredStartDate = firstNonEmpty(
    contract.required_start_date,
    contract.start_date,
    contract.startDate,
    contract.signing_date,
    contract.signed_date,
    contract.signedDate,
  );
  const requiredEndDate = firstNonEmpty(
    contract.required_end_date,
    contract.end_date,
    contract.endDate,
    contract.delivery_deadline,
  );
  const requirementSummary = firstNonEmpty(
    contract.requirement_summary,
    contract.requirementSummary,
    contract.requirement_description,
    contract.requirementDescription,
    contract.scope_of_work,
    contract.scopeOfWork,
    contract.contract_scope,
    contract.contractScope,
    contract.project_scope,
    contract.projectScope,
    contract.technical_requirements,
    contract.technicalRequirements,
    contract.description,
    contract.notes,
  );

  const params = new URLSearchParams({ handoff: "contract" });
  appendIfPresent(params, "project_name", projectName);
  appendIfPresent(params, "customer_name", customerName);
  appendIfPresent(params, "contract_no", contractNo);
  appendIfPresent(params, "contract_amount", contractAmount);
  appendIfPresent(params, "required_start_date", requiredStartDate);
  appendIfPresent(params, "required_end_date", requiredEndDate);
  appendIfPresent(params, "requirement_summary", requirementSummary);
  appendIfPresent(params, "technical_solution_id", contract.technical_solution_id);
  appendIfPresent(params, "estimated_hours", contract.estimated_hours);

  return `/pmo/initiations?${params.toString()}`;
};
