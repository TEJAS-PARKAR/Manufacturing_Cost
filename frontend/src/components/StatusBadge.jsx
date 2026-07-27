const STATUS_MAP = {
  active:               { label: 'Active',               className: 'status-active' },
  submitted_for_review: { label: 'Submitted for Review', className: 'status-submitted' },
  approved:             { label: 'Approved',             className: 'status-approved' },
  rejected:             { label: 'Rejected',             className: 'status-rejected' },
};

export default function StatusBadge({ status }) {
  const { label, className } = STATUS_MAP[status] || { label: 'Pending', className: 'status-pending' };
  return <span className={`status-badge ${className}`}>{label}</span>;
}
