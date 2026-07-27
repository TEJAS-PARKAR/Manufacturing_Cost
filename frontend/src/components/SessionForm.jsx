import { useState } from 'react';

export default function SessionForm({ onStartSession, loading }) {
  const [employeeId, setEmployeeId] = useState('');
  const [partNumber, setPartNumber] = useState('');
  const [warning, setWarning] = useState('');

  const handleStart = () => {
    if (!employeeId || !partNumber) {
      setWarning('Please enter both Employee ID and Part Number.');
      return;
    }
    setWarning('');
    onStartSession(employeeId, partNumber);
  };

  return (
    <>
      <div className="session-form">
        <div className="form-group">
          <label htmlFor="employee-id">Employee ID</label>
          <input
            id="employee-id"
            type="text"
            placeholder="EMP1001"
            value={employeeId}
            onChange={(e) => setEmployeeId(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label htmlFor="part-number">Part Number</label>
          <input
            id="part-number"
            type="text"
            placeholder="123456789012"
            value={partNumber}
            onChange={(e) => setPartNumber(e.target.value)}
          />
        </div>
      </div>

      {warning && <div className="alert alert-warning">{warning}</div>}

      <button
        className="btn-primary"
        onClick={handleStart}
        disabled={loading}
      >
        {loading ? (
          <span className="spinner-overlay">
            <span className="spinner" />
            Loading session…
          </span>
        ) : (
          'Start / Resume Session'
        )}
      </button>
    </>
  );
}
