/** Round numeric values to 2 decimal places for display. */
function fmt(v) {
  if (v === null || v === undefined || v === '' || v === '—') return '—';
  const n = Number(v);
  return isNaN(n) ? String(v) : n.toFixed(2);
}

function isDisplayable(v) {
  return v !== null && v !== undefined && v !== '' && !(Array.isArray(v) && v.length === 0);
}

function formatCurrency(value) {
  if (!isDisplayable(value)) return null;
  const n = Number(value);
  if (Number.isNaN(n)) return null;
  return `₹ ${n.toFixed(2)}`;
}

function formatPercent(value) {
  if (!isDisplayable(value)) return null;
  const n = Number(value);
  if (Number.isNaN(n)) return null;
  return `${n.toFixed(2)}%`;
}

function formatNumber(value) {
  if (!isDisplayable(value)) return null;
  const n = Number(value);
  if (Number.isNaN(n)) return String(value);
  return n.toFixed(2);
}

function humanizeKey(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\s+/g, ' ')
    .replace(/\b\w/g, (ch) => ch.toUpperCase());
}

const EXCLUDED_KEYS = new Set([
  'employee_id',
  'session_key',
  'status',
  'history',
  'review',
  'revisions',
  'revision',
  'negotiation',
  'sheet_optimization',
  'awaiting_allowance_response',
  'rejection_remark',
  'process_information',
  'missing_fields',
  'part_number',
  'blank_weight',
  'material',
  'material_grade',
  'material_rate',
  'part_length',
  'part_width',
  'part_thickness',
  'sheet_length',
  'sheet_width',
  'sheet_thickness',
  'material_type',
  'gross_weight',
  'finished_weight',
  'scrap_weight',
  'scrap_rate',
  'scrap_recovery',
  'yield_percentage',
  'coating',
  // 'coating_cost',
  'adjusted_net_rm_cost',
  'net_rm_cost_validation',
  'allowance_applied',
  'calculated_net_rm_cost',
  'supplier_net_rm_cost',
]);

const PREFERRED_ORDER = [
  'raw_material_cost',
  'conversion_cost',
  'grinding_chipping_cost',
  'identification_mark_cost',
  'coating_cost',
  'overhead_cost',
  'icc_cost',
  'rejection_cost',
  'rejection_recovery',
  'profit',
  'total_cost',
];

function isCostDrivingKey(key, value) {
  if (EXCLUDED_KEYS.has(key)) return false;
  if (Array.isArray(value) || (typeof value === 'object' && value !== null)) return false;
  if (!isDisplayable(value)) return false;

  const normalized = key.toLowerCase();

  if (normalized.includes('net_rm')) return false;
  if (normalized.includes('process')) return false;
  if (normalized.includes('validation')) return false;
  if (normalized.includes('yield')) return false;
  if (normalized.includes('scrap_recovery')) return false;

  const heuristics = [
    'cost',
    'rate',
    'recovery',
    'profit',
    'coating',
    'conversion',
    'overhead',
    'icc',
    'rejection',
    'allowance',
  ];

  return heuristics.some((term) => normalized.includes(term));
}

export default function CostSummary({ session }) {
  const extracted = session?.extracted_data || {};
  const netRmValidation = extracted.net_rm_cost_validation || null;
  const adjustedNetRmCost = extracted.adjusted_net_rm_cost;
  const allowanceApplied = extracted.allowance_applied === true;

  // Display backend-calculated blank weight
  const sheetWeight = fmt(extracted.blank_weight);

  const costDrivingRows = Object.entries(extracted)
    .filter(([key, value]) => isCostDrivingKey(key, value))
    .map(([key, value]) => {
      const normalizedKey = key.toLowerCase();
      const displayLabel = humanizeKey(key);
      let formattedValue = value;

      if (typeof value === 'number' || typeof value === 'string') {
        const numericValue = Number(value);
        if (!Number.isNaN(numericValue)) {
          const isCurrencyField = normalizedKey.includes('cost') || normalizedKey.includes('rate') || normalizedKey.includes('recovery') || normalizedKey.includes('profit');
          const isPercentField = normalizedKey.includes('yield');
          if (isCurrencyField) formattedValue = `₹ ${numericValue.toFixed(2)}`;
          else if (isPercentField) formattedValue = `${numericValue.toFixed(2)}%`;
          else if (normalizedKey.includes('weight')) formattedValue = numericValue.toFixed(2);
        }
      }

      return { key, label: displayLabel, value: formattedValue };
    })
    .sort((a, b) => {
      const aRank = PREFERRED_ORDER.indexOf(a.key.toLowerCase());
      const bRank = PREFERRED_ORDER.indexOf(b.key.toLowerCase());
      if (aRank !== -1 || bRank !== -1) return (aRank === -1 ? Number.MAX_SAFE_INTEGER : aRank) - (bRank === -1 ? Number.MAX_SAFE_INTEGER : bRank);
      return a.label.localeCompare(b.label);
    });

  const processRows = Array.isArray(extracted.process_information)
    ? extracted.process_information.filter((item) => item && (isDisplayable(item.process) || isDisplayable(item.cost)))
    : [];

  return (
    <div>
      <h3 className="section-heading">Costing Summary</h3>
      <table className="cost-table">
        <thead>
          <tr>
            <th>Parameter</th>
            <th>Value</th>
          </tr>
        </thead>
        <tbody>
          {/* ── Material Info ── */}
          <tr>
            <td>Part Reference</td>
            <td>{session?.part_reference || '—'}</td>
          </tr>
          <tr>
            <td>Material Grade</td>
            <td>{extracted.material_grade || '—'}</td>
          </tr>
          <tr>
            <td>Material Rate</td>
            <td>{fmt(extracted.material_rate)}</td>
          </tr>

          {/* ── Sheet Dimensions ── */}
          <tr className="dimension-section-header">
            <td colSpan={2}><strong>Sheet Dimensions</strong></td>
          </tr>
          <tr>
            <td className="indent">Length</td>
            <td>{fmt(extracted.sheet_length)}</td>
          </tr>
          <tr>
            <td className="indent">Width</td>
            <td>{fmt(extracted.sheet_width)}</td>
          </tr>
          <tr>
            <td className="indent">Thickness</td>
            <td>{fmt(extracted.sheet_thickness ?? extracted.thickness)}</td>
          </tr>
          <tr>
            <td className="indent">Weight (kg)</td>
            <td>{sheetWeight}</td>
          </tr>

          {/* ── Part Dimensions (Shear Size) ── */}
          <tr className="dimension-section-header">
            <td colSpan={2}><strong>Part Dimensions (Shear Size)</strong></td>
          </tr>
          <tr>
            <td className="indent">Length</td>
            <td>{fmt(extracted.part_length ?? extracted.length)}</td>
          </tr>
          <tr>
            <td className="indent">Width</td>
            <td>{fmt(extracted.part_width ?? extracted.width)}</td>
          </tr>
          <tr>
            <td className="indent">Thickness</td>
            <td>{fmt(extracted.part_thickness ?? extracted.thickness)}</td>
          </tr>
          <tr>
            <td className="indent">Gross Weight (kg)</td>
            <td>{fmt(extracted.gross_weight)}</td>
          </tr>
          <tr>
            <td className="indent">Finished Weight (kg)</td>
            <td>{fmt(extracted.finished_weight)}</td>
          </tr>
          <tr>
            <td className="indent">Scrap Weight (kg)</td>
            <td>{fmt(extracted.scrap_weight)}</td>
          </tr>

          {netRmValidation && (
            <>
              <tr className="dimension-section-header net-rm-summary-header">
                <td colSpan={2}><strong>Net RM Cost Validation</strong></td>
              </tr>
              <tr>
                <td className="indent">Supplier Net RM Cost</td>
                <td>{netRmValidation.excel_value != null ? `₹ ${fmt(netRmValidation.excel_value)}` : '—'}</td>
              </tr>
              <tr>
                <td className="indent">Calculated Net RM Cost</td>
                <td>{netRmValidation.calculated_value != null ? `₹ ${fmt(netRmValidation.calculated_value)}` : '—'}</td>
              </tr>
              <tr>
                <td className="indent">Difference</td>
                <td>{netRmValidation.difference != null ? `₹ ${fmt(netRmValidation.difference)}` : '—'}</td>
              </tr>
              <tr>
                <td className="indent">Validation Status</td>
                <td>
                  <span className={`net-rm-summary-status ${netRmValidation.matches === true ? 'matched' : netRmValidation.matches === false ? 'mismatch' : 'pending'}`}>
                    {netRmValidation.matches === true ? '✓ Matched' : netRmValidation.matches === false ? '✕ Mismatch' : 'Not Validated'}
                  </span>
                </td>
              </tr>
              {allowanceApplied && adjustedNetRmCost != null && (
                <tr className="adjusted-net-rm-row">
                  <td className="indent">
                    <span>Adjusted Net RM Cost</span>
                    <small>After cutting / shearing allowance</small>
                  </td>
                  <td>₹ {fmt(adjustedNetRmCost)}</td>
                </tr>
              )}
            </>
          )}
        </tbody>
      </table>

      <div className="extracted-cost-info">
        <h4 className="section-subheading">Cost Driving Components</h4>
        {costDrivingRows.length > 0 ? (
          <table className="cost-table extracted-cost-table">
            <thead>
              <tr>
                <th>Field</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {costDrivingRows.map(({ key, label, value }) => (
                <tr key={key}>
                  <td className="indent">{label}</td>
                  <td>{value ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="section-empty">No cost-driving components extracted from the uploaded Excel.</p>
        )}

      </div>
    </div>
  );
}
