/** Round numeric values to 2 decimal places for display. */
function fmt(v) {
  if (v === null || v === undefined || v === '' || v === '—') return '—';
  const n = Number(v);
  return isNaN(n) ? String(v) : n.toFixed(2);
}

export default function CostSummary({ session }) {
  const extracted = session?.extracted_data || {};
  const netRmValidation = extracted.net_rm_cost_validation || null;
  const adjustedNetRmCost = extracted.adjusted_net_rm_cost;
  const allowanceApplied = extracted.allowance_applied === true;

  // Display backend-calculated blank weight
  const sheetWeight = fmt(extracted.blank_weight);

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
            <td>Part No.</td>
            <td>{extracted.part_number || '—'}</td>
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
          <tr className="total-cost-section-header">
            <td colSpan={2}><strong>Total Cost</strong></td>
          </tr>
          <tr className="total-cost-row">
            <td colSpan={2}>₹ {fmt(extracted.total_cost)}</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
