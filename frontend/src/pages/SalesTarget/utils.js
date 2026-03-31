import { targetTypeOptions, targetPeriodOptions } from "./constants";

export const parseMeta = (description) => {
  if (!description || !description.includes("[meta]")) {
    return {};
  }
  try {
    const raw = description.split("[meta]")[1];
    return JSON.parse(raw);
  } catch {
    return {};
  }
};

export const buildDescriptionWithMeta = (description, meta) => {
  const base = (description || "").split("[meta]")[0].trim();
  const packed = JSON.stringify(meta);
  return `${base}${base ? " " : ""}[meta]${packed}`;
};

export const generatePeriodValue = (periodType) => {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;

  if (periodType === "MONTHLY") {
    return `${year}-${String(month).padStart(2, "0")}`;
  } else if (periodType === "QUARTERLY") {
    const quarter = Math.ceil(month / 3);
    return `${year}-Q${quarter}`;
  } else if (periodType === "YEARLY") {
    return String(year);
  }
  return "";
};

export const getTargetTypeLabel = (type) => {
  const option = (targetTypeOptions || []).find((opt) => opt.value === type);
  return option?.label || type;
};

export const getTargetPeriodLabel = (period) => {
  const option = (targetPeriodOptions || []).find(
    (opt) => opt.value === period,
  );
  return option?.label || period;
};
