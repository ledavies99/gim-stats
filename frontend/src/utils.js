
export function humanizeNumber(value) {
  value = Number(value);
  if (isNaN(value)) return value;
  if (value >= 1_000_000_000_000) return (value / 1_000_000_000_000).toFixed(1) + "T";
  if (value >= 1_000_000_000) return (value / 1_000_000_000).toFixed(1) + "B";
  if (value >= 1_000_000) return (value / 1_000_000).toFixed(1) + "M";
  if (value >= 1000) return (value / 1000).toFixed(1) + "K";
  return value;
}