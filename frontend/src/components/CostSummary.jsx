export default function CostSummary({ session }) {
  const extracted = session?.extracted_data || {};

  const rows = [
    ['Material',         extracted.material         ?? '—'],
    ['Material Rate',    extracted.material_rate     ?? '—'],
    ['Thickness',        extracted.thickness         ?? '—'],
    ['Width',            extracted.width             ?? '—'],
    ['Length',           extracted.length            ?? '—'],
    ['Finished Weight',  extracted.finished_weight   ?? '—'],
    ['Scrap Weight',     extracted.scrap_weight      ?? '—'],
    ['RM Cost',          extracted.raw_material_cost ?? '—'],
    ['Conversion Cost',  extracted.conversion_cost   ?? '—'],
    ['Coating Cost',     extracted.coating_cost      ?? '—'],
    ['Total Cost',       extracted.total_cost        ?? '—'],
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
          {rows.map(([param, value]) => (
            <tr key={param}>
              <td>{param}</td>
              <td>{String(value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
