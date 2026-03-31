/**
 * Parse a JSON string field, throwing a descriptive error on failure.
 */
export const parseJsonField = (value, _fallback = {}) => {
  try {
    return JSON.parse(value || "{}");
  } catch (error) {
    throw new Error("JSON 字段格式不正确", { cause: error });
  }
};
