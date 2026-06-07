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
