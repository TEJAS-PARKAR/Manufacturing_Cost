/** Round numeric values to 2 decimal places for display. */
function fmt(v) {
  if (v === null || v === undefined || v === '' || v === '—') return '—';
  const n = Number(v);
  return isNaN(n) ? String(v) : n.toFixed(2);
}

export default function CostSummary({ session }) {
  const extracted = session?.extracted_data || {};

  // Compute sheet weight: sheet_l × sheet_w × thickness × 7.85 / 10^6
  const sheetL = parseFloat(extracted.sheet_length || 0);
  const sheetW = parseFloat(extracted.sheet_width || 0);
  const sheetT = parseFloat(extracted.sheet_thickness || extracted.thickness || 0);
  const sheetWeight = sheetL > 0 && sheetW > 0 && sheetT > 0
    ? (sheetL * sheetW * sheetT * 7.85 / 1e6).toFixed(2)
    : '—';

  const costRows = [
    ['RM Cost',          extracted.raw_material_cost],
    ['Conversion Cost',  extracted.conversion_cost],
    ['Coating Cost',     extracted.coating_cost],
    ['Overhead Cost',    extracted.overhead_cost],
    ['ICC Cost',         extracted.icc_cost],
    ['Rejection Cost',   extracted.rejection_cost],
    ['Profit',           extracted.profit],
    ['Packing Cost',     extracted.packing_cost],
    ['Transport Cost',   extracted.transport_cost],
    ['Total Cost',       extracted.total_cost],
  ];

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
            <td>Material No.</td>
            <td>{extracted.material || '—'}</td>
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

          {/* ── Weights ── */}
          <tr>
            <td>Finished Weight</td>
            <td>{fmt(extracted.finished_weight)}</td>
          </tr>
          <tr>
            <td>Scrap Weight</td>
            <td>{fmt(extracted.scrap_weight)}</td>
          </tr>

          {/* ── Cost Components ── */}
          <tr className="dimension-section-header">
            <td colSpan={2}><strong>Cost Components</strong></td>
          </tr>
          {costRows.map(([param, value]) => (
            <tr key={param}>
              <td className="indent">{param}</td>
              <td>{fmt(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
