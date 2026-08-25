import { useState, useEffect } from 'react';
import StatusBadge from './StatusBadge';
import MetricCard from './MetricCard';
import CostChart from './CostChart';
import CostSummary from './CostSummary';
import ChatHistory from './ChatHistory';
import * as api from '../api';
import { fmt } from '../utils';

const REJECT_REASONS = [
  'Cost Above Benchmark',
  'Material Rate Too High',
  'Conversion Cost Too High',
  'Commercial Terms Not Acceptable',
  'Incomplete Cost Sheet',
  'Other',
];

export default function TataPortal({ employeeId, partNumber }) {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [approving, setApproving] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [rejectReason, setRejectReason] = useState(REJECT_REASONS[0]);
  const [alert, setAlert] = useState(null);

  // ── Session Discovery State ──
  const [sessionsList, setSessionsList] = useState([]);
  const [loadingList, setLoadingList] = useState(false);

  const fetchSessionsList = async () => {
    setLoadingList(true);
    try {
      const list = await api.listSessions();
      setSessionsList(list || []);
    } catch (err) {
      console.warn('Could not fetch sessions list:', err);
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    fetchSessionsList();
  }, []);

  // ── Load review dashboard ──
  const handleLoadDashboard = async (targetEmpId, targetPartNum) => {
    const emp = targetEmpId || employeeId;
    const part = targetPartNum || partNumber;
    if (!emp || !part) return;

    setLoading(true);
    setAlert(null);
    try {
      const result = await api.getReviewDashboard(emp, part);
      setDashboard(result);
    } catch (err) {
      setAlert({ type: 'error', message: `Review lookup failed: ${err.message}` });
    } finally {
      setLoading(false);
    }
  };

  // ── Approve ──
  const handleApprove = async () => {
    setApproving(true);
    setAlert(null);
    try {
      await api.approveSession(employeeId, partNumber);
      setAlert({ type: 'success', message: 'Offer Approved Successfully!' });
      // Reload dashboard & list
      const refreshed = await api.getReviewDashboard(employeeId, partNumber);
      setDashboard(refreshed);
      fetchSessionsList();
    } catch (err) {
      setAlert({ type: 'error', message: `Approval failed: ${err.message}` });
    } finally {
      setApproving(false);
    }
  };

  // ── Reject ──
  const handleReject = async () => {
    setRejecting(true);
    setAlert(null);
    try {
      await api.rejectSession(employeeId, partNumber, rejectReason);
      setAlert({ type: 'success', message: 'Offer Rejected.' });
      const refreshed = await api.getReviewDashboard(employeeId, partNumber);
      setDashboard(refreshed);
      fetchSessionsList();
    } catch (err) {
      setAlert({ type: 'error', message: `Rejection failed: ${err.message}` });
    } finally {
      setRejecting(false);
    }
  };

  return (
    <div>
      <h3 className="section-heading">Tata Motors Review Dashboard</h3>
      <p style={{ color: '#6C757D', fontSize: '0.85rem', marginBottom: '1rem' }}>
        Review supplier sessions, benchmark comparisons, and approve/reject final inputs.
      </p>

      {/* ── Sessions Discovery List ── */}
      <div style={{ marginBottom: '1.5rem', background: '#F8F9FA', border: '1px solid #E9ECEF', borderRadius: '8px', padding: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <strong style={{ fontSize: '0.95rem' }}>Available Supplier Sessions</strong>
          <button
            className="btn-secondary"
            onClick={fetchSessionsList}
            disabled={loadingList}
            style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem' }}
          >
            {loadingList ? 'Refreshing…' : '🔄 Refresh List'}
          </button>
        </div>

        {sessionsList.length === 0 ? (
          <p style={{ fontSize: '0.85rem', color: '#6C757D', margin: 0 }}>
            {loadingList ? 'Loading available sessions…' : 'No active sessions found. Enter credentials above or refresh.'}
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="sheet-util-table" style={{ margin: 0 }}>
              <thead>
                <tr>
                  <th>Supplier ID</th>
                  <th>Part Number</th>
                  <th>Material</th>
                  <th>Total Cost</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {sessionsList.map((s, idx) => (
                  <tr key={idx}>
                    <td><strong>{s.employee_id}</strong></td>
                    <td>{s.part_number}</td>
                    <td>{s.material || '—'}</td>
                    <td>{s.total_cost ? `₹ ${fmt(s.total_cost)}` : '—'}</td>
                    <td><StatusBadge status={s.status} /></td>
                    <td>
                      <button
                        className="btn-primary"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => handleLoadDashboard(s.employee_id, s.part_number)}
                        disabled={loading}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
        <button className="btn-primary" onClick={() => handleLoadDashboard()} disabled={loading || !employeeId || !partNumber}>
          {loading ? (
            <span className="spinner-overlay">
              <span className="spinner" />
              Loading review dashboard…
            </span>
          ) : (
            'Load Review Dashboard (From Input)'
          )}
        </button>
      </div>

      {alert && <div className={`alert alert-${alert.type}`}>{alert.message}</div>}

      {dashboard && (() => {
        const session = dashboard.session || {};
        const extracted = session.extracted_data || {};
        const benchmark = dashboard.benchmark_comparison || {};
        const negotiation = session.negotiation || {};
        const sheetOpt = session.sheet_optimization || {};
        const status = session.status || 'active';

        return (
          <>
            <hr className="section-divider" />

            {/* ── Session Overview ── */}
            <div className="session-overview-header">
              <h3>Session Overview</h3>
              <StatusBadge status={status} />
            </div>

            <div className="metric-grid">
              <MetricCard label="Part Number" value={session.part_number || '—'} />
              <MetricCard label="Material No." value={extracted.material || '—'} />
              <MetricCard label="Material Rate" value={`₹ ${fmt(extracted.material_rate)}`} variant="accent" />
              <MetricCard
                label="Total Cost"
                value={extracted.total_cost ? `₹ ${fmt(extracted.total_cost)}` : '—'}
                variant="success"
              />
            </div>

            {session.missing_fields && session.missing_fields.length > 0 ? (
              <div className="alert alert-warning">
                Missing Fields: <strong>{session.missing_fields.join(', ')}</strong>
              </div>
            ) : (
              <div className="alert alert-success">All mandatory fields available.</div>
            )}


            {/* ── Sheet Optimization Result (if available) ── */}
            {sheetOpt && sheetOpt.is_optimal !== undefined && (
              <>
                <hr className="section-divider" />
                <h3 className="section-heading">Sheet Utilization Validation</h3>
                {sheetOpt.is_optimal === true && (
                  <div className="sheet-opt-banner optimal">
                    <span className="sheet-opt-icon">✅</span>
                    <div>
                      <strong>Sheet size is optimal.</strong>
                      <p>Current sheet ({sheetOpt.current_sheet}) provides the best utilization.</p>
                    </div>
                  </div>
                )}
                {sheetOpt.is_optimal === false && (
                  <div className="sheet-opt-banner not-optimal">
                    <span className="sheet-opt-icon">⚠️</span>
                    <div>
                      <strong>Sheet size is NOT optimal.</strong>
                      <p>{sheetOpt.recommendation}</p>
                    </div>
                  </div>
                )}

                {sheetOpt.all_options && sheetOpt.all_options.length > 0 && (
                  <table className="sheet-util-table">
                    <thead>
                      <tr>
                        <th>Sheet Size (mm)</th>
                        <th>Parts / Sheet</th>
                        <th>Weight / Part (kg)</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sheetOpt.all_options.map((opt) => {
                        const isBest = sheetOpt.best_option &&
                          opt.sheet_size === sheetOpt.best_option.sheet_size;
                        const isCurrent = opt.sheet_size === sheetOpt.current_sheet;
                        return (
                          <tr key={opt.sheet_size} className={isBest ? 'best-row' : ''}>
                            <td>{opt.sheet_size}</td>
                            <td>{opt.num_parts}</td>
                            <td>{fmt(opt.weight_per_part)}</td>
                            <td>
                              {isBest && <span className="badge badge-optimal">✓ Optimal</span>}
                              {isCurrent && !isBest && <span className="badge badge-current">Current</span>}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </>
            )}

            {/* ── Cost chart + summary ── */}
            {extracted.total_cost && (
              <>
                <hr className="section-divider" />
                <div className="cost-split">
                  <CostChart session={session} />
                  <CostSummary session={session} />
                </div>
              </>
            )}

            <hr className="section-divider" />

            {/* ── Benchmark Comparison ── */}
            <h3 className="section-heading">Benchmark Comparison</h3>
            <div className="metric-grid-3">
              <MetricCard
                label="Supplier Rate"
                value={`₹ ${fmt(benchmark.supplier_material_rate)}`}
              />
              <MetricCard
                label="Benchmark Rate"
                value={`₹ ${fmt(benchmark.internal_benchmark_rate)}`}
                variant="accent"
              />
              <MetricCard
                label="Variance"
                value={`₹ ${fmt(benchmark.variance)}`}
                variant={(benchmark.variance || 0) <= 0 ? 'success' : 'danger'}
              />
            </div>

            {/* ── Recommendation ── */}
            {benchmark.recommendation === 'accept' && (
              <div className="rec-accept">RECOMMENDATION: ACCEPT</div>
            )}
            {benchmark.recommendation === 'review' && (
              <div className="rec-review">RECOMMENDATION: REVIEW</div>
            )}
            {benchmark.recommendation !== 'accept' && benchmark.recommendation !== 'review' && (
              <div className="rec-negotiate">RECOMMENDATION: NEGOTIATE FURTHER</div>
            )}

            <hr className="section-divider" />

            {/* ── Negotiation Analysis ── */}
            <h3 className="section-heading">Negotiation Analysis</h3>
            <div className="metric-grid-3">
              <MetricCard
                label="Supplier Quote"
                value={`₹ ${fmt(negotiation.supplier_quote)}`}
              />
              <MetricCard
                label="Expected Cost"
                value={`₹ ${fmt(negotiation.predicted_cost)}`}
                variant="accent"
              />
              <MetricCard
                label="Variance %"
                value={`${fmt(negotiation.variance)}%`}
                variant={(negotiation.variance || 0) <= 5 ? 'success' : 'danger'}
              />
            </div>

            <div className="alert alert-info">
              <strong>AI Recommendation:</strong>{' '}
              {typeof negotiation.ai_recommendation === 'string'
                ? negotiation.ai_recommendation.toUpperCase()
                : negotiation.ai_recommendation || '—'}
            </div>
            <div className="alert alert-success">
              <strong>Suggested Counter Offer:</strong> ₹{fmt(negotiation.counter_offer)}
            </div>

            <hr className="section-divider" />

            {/* ── Chat History ── */}
            <h3 className="section-heading">Negotiation History</h3>
            <ChatHistory history={session.history || []} currentUserRole="tata" />

            <hr className="section-divider" />

            {/* ── Buyer Actions ── */}
            {status === 'submitted_for_review' && (
              <>
                <h3 className="section-heading">Buyer Actions</h3>
                <div className="buyer-actions">
                  <div className="buyer-action-card">
                    <h4>Approve Quotation</h4>
                    <p className="caption">Approving will finalize the cost inputs for procurement.</p>
                    <button className="btn-success" onClick={handleApprove} disabled={approving}>
                      {approving ? (
                        <span className="spinner-overlay">
                          <span className="spinner" />
                          Approving…
                        </span>
                      ) : (
                        'Approve Quotation'
                      )}
                    </button>
                  </div>
                  <div className="buyer-action-card">
                    <h4>Reject Quotation</h4>
                    <div className="form-group" style={{ marginBottom: '1rem' }}>
                      <label htmlFor="reject-reason">Rejection Reason</label>
                      <select
                        id="reject-reason"
                        className="form-select"
                        value={rejectReason}
                        onChange={(e) => setRejectReason(e.target.value)}
                      >
                        {REJECT_REASONS.map((r) => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    </div>
                    <button className="btn-danger" onClick={handleReject} disabled={rejecting}>
                      {rejecting ? (
                        <span className="spinner-overlay">
                          <span className="spinner" />
                          Rejecting…
                        </span>
                      ) : (
                        'Reject Quotation'
                      )}
                    </button>
                  </div>
                </div>
              </>
            )}

            {status === 'approved' && (
              <div className="alert alert-success">
                This quotation has been <strong>approved</strong>. No further actions needed.
              </div>
            )}

            {status === 'rejected' && (
              <div className="alert alert-error">
                This quotation has been <strong>rejected</strong>.
              </div>
            )}
          </>
        );
      })()}
    </div>
  );
}
