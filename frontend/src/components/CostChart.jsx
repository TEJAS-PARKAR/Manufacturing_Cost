import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#1B3A5C', '#E8B300', '#00A86B'];

export default function CostChart({ session }) {
  const extracted = session?.extracted_data || {};
  const rm = parseFloat(extracted.raw_material_cost || 0) || 0;
  const conversion = parseFloat(extracted.conversion_cost || 0) || 0;
  const coating = parseFloat(extracted.coating_cost || 0) || 0;

  if (rm === 0 && conversion === 0 && coating === 0) {
    return null;
  }

  const data = [
    { name: 'Raw Material', value: rm },
    { name: 'Conversion', value: conversion },
    { name: 'Coating', value: coating },
  ];

  return (
    <div className="chart-container">
      <h3 className="section-heading">Cost Breakdown</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={3}
            dataKey="value"
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          >
            {data.map((_, idx) => (
              <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value) => [`₹ ${value.toFixed(2)}`, 'Cost']}
            contentStyle={{ fontFamily: 'Inter', borderRadius: 8, border: '1px solid #e9ecef' }}
          />
          <Legend
            wrapperStyle={{ fontFamily: 'Inter', fontSize: '0.85rem' }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
