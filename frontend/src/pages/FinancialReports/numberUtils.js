export const toFiniteNumber = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
};

export const safePercent = (value, total) => {
  const denominator = toFiniteNumber(total);
  if (denominator <= 0) {return 0;}
  return toFiniteNumber(value) / denominator * 100;
};
