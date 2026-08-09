/** Round any numeric value (or ₹-prefixed string) to 2 decimal places. */
function fmt(raw) {
  if (raw === null || raw === undefined || raw === '—') return raw;
  // Handle "₹ 33.666" style strings
  if (typeof raw === 'string') {
    return raw.replace(/(\d+\.\d{3,})/g, (m) => Number(m).toFixed(2));
  }
  if (typeof raw === 'number') return raw.toFixed(2);
  return raw;
}

export default function MetricCard({ label, value, variant = '' }) {
  return (
    <div className={`metric-card ${variant}`}>
      <div className="label">{label}</div>
      <div className="value">{fmt(value)}</div>
    </div>
  );
}
