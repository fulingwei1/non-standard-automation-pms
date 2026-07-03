export const compactQueryParams = (params) =>
  Object.fromEntries(
    Object.entries(params || {}).filter(([, value]) => {
      if (value === "" || value === undefined || value === null) {
        return false;
      }
      if (value === "all") {
        return false;
      }
      return true;
    })
  );
