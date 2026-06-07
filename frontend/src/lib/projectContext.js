const getFirstSearchParam = (searchParams, names) => {
  for (const name of names) {
    const value = searchParams.get(name);
    if (value) {
      return value;
    }
  }
  return null;
};

export const getProjectContextFilters = (searchParams) => {
  const filters = {};
  const projectId = getFirstSearchParam(searchParams, ["project_id", "projectId"]);
  const contractId = getFirstSearchParam(searchParams, ["contract_id", "contractId"]);
  const opportunityId = getFirstSearchParam(searchParams, ["opportunity_id", "opportunityId"]);

  if (projectId) {
    filters.project_id = projectId;
  }
  if (contractId) {
    filters.contract_id = contractId;
  }
  if (opportunityId) {
    filters.opportunity_id = opportunityId;
  }

  return filters;
};

export const hasProjectContextFilters = (filters) =>
  Object.keys(filters || {}).length > 0;

export const mergeProjectContextFilters = (searchParams, params = {}) => ({
  ...params,
  ...getProjectContextFilters(searchParams),
});
