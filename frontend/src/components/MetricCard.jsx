export default function MetricCard({ label, value, variant = '' }) {
  return (
    <div className={`metric-card ${variant}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}
