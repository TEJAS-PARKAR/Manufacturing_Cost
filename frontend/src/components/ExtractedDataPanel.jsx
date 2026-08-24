function formatLabel(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatValue(value) {
  if (value === null || value === undefined || value === '') return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (Array.isArray(value)) {
    return value.length ? value.map((item) => formatValue(item)).join(', ') : '—';
  }
  if (typeof value === 'object') {
    return Object.entries(value)
      .map(([key, item]) => `${formatLabel(key)}: ${formatValue(item)}`)
      .join(' | ');
  }
  return String(value);
}

export default function ExtractedDataPanel({ data }) {
  const entries = Object.entries(data || {});

  if (!entries.length) return null;

  return (
    <section className="extracted-data-panel" aria-labelledby="extracted-data-heading">
      <div className="extracted-data-heading-row">
        <div>
          <h3 id="extracted-data-heading">Extracted Costing Data</h3>
          <p>Values read from the submitted costing sheet.</p>
        </div>
        <span className="extracted-data-count">{entries.length} fields</span>
      </div>
      <div className="extracted-data-grid">
        {entries.map(([key, value]) => (
          <div className="extracted-data-item" key={key}>
            <span className="extracted-data-label">{formatLabel(key)}</span>
            <span className="extracted-data-value">{formatValue(value)}</span>
          </div>
        ))}
      </div>
    </section>
  );
}