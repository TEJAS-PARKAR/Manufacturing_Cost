export default function Sidebar({ portal, onPortalChange, authenticated, username, onLogout }) {
  const captions = {
    Supplier: 'Upload cost sheets, negotiate pricing, and submit for review.',
    'Tata Motors': 'Review supplier quotes, benchmark comparisons, and approve/reject.',
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-title">Portal Access</div>
      <hr />

      <div className="portal-radio-group">
        {['Supplier', 'Tata Motors'].map((p) => (
          <label
            key={p}
            className={`portal-radio-label${portal === p ? ' active' : ''}`}
          >
            <input
              type="radio"
              name="portal"
              value={p}
              checked={portal === p}
              onChange={() => onPortalChange(p)}
            />
            {p}
          </label>
        ))}
      </div>

      <p className="sidebar-caption">{captions[portal]}</p>

      <hr />

      {authenticated && (
        <>
          <div className="sidebar-user-info">
            <div><span>Logged in as:</span> {username}</div>
            <div><span>Portal:</span> {portal}</div>
          </div>
          <button className="btn-logout" onClick={onLogout}>
            Logout
          </button>
        </>
      )}
    </aside>
  );
}
