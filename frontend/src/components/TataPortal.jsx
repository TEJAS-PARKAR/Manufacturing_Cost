import { useState } from 'react';
import StatusBadge from './StatusBadge';
import Stepper from './Stepper';
import MetricCard from './MetricCard';
import CostChart from './CostChart';
import CostSummary from './CostSummary';
import ChatHistory from './ChatHistory';
import * as api from '../api';

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

  // ── Load review dashboard ──
  const handleLoadDashboard = async () => {
    setLoading(true);
    setAlert(null);
    try {
      const result = await api.getReviewDashboard(employeeId, partNumber);
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
      // Reload dashboard
      const refreshed = await api.getReviewDashboard(employeeId, partNumber);
      setDashboard(refreshed);
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

      <button className="btn-primary" onClick={handleLoadDashboard} disabled={loading}>
        {loading ? (
          <span className="spinner-overlay">
            <span className="spinner" />
            Loading review dashboard…
          </span>
        ) : (
          'Load Review Dashboard'
        )}
      </button>

      {alert && <div className={`alert alert-${alert.type}`}>{alert.message}</div>}

      {dashboard && (() => {
        const session = dashboard.session || {};
        const extracted = session.extracted_data || {};
        const benchmark = dashboard.benchmark_comparison || {};
        const negotiation = session.negotiation || {};
        const status = session.status || 'active';

        return (
          <>
            <hr className="section-divider" />

            {/* ── Session Overview ── */}
            <div className="session-overview-header">
              <h3>Session Overview</h3>
              <StatusBadge status={status} />
            </div>
            <Stepper status={status} />

            <div className="metric-grid">
              <MetricCard label="Part Number" value={session.part_number || '—'} />
              <MetricCard label="Material" value={extracted.material || '—'} />
              <MetricCard label="Material Rate" value={`₹ ${extracted.material_rate || '—'}`} variant="accent" />
              <MetricCard
                label="Total Cost"
                value={extracted.total_cost ? `₹ ${Math.round(extracted.total_cost * 100) / 100}` : '—'}
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
                value={`₹ ${benchmark.supplier_material_rate || 0}`}
              />
              <MetricCard
                label="Benchmark Rate"
                value={`₹ ${benchmark.internal_benchmark_rate || 0}`}
                variant="accent"
              />
              <MetricCard
                label="Variance"
                value={`₹ ${benchmark.variance || 0}`}
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
                value={`₹ ${negotiation.supplier_quote || 0}`}
              />
              <MetricCard
                label="Expected Cost"
                value={`₹ ${negotiation.predicted_cost || 0}`}
                variant="accent"
              />
              <MetricCard
                label="Variance %"
                value={`${negotiation.variance || 0}%`}
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
              <strong>Suggested Counter Offer:</strong> ₹{negotiation.counter_offer || '—'}
            </div>

            <hr className="section-divider" />

            {/* ── Chat History ── */}
            <h3 className="section-heading">Negotiation History</h3>
            <ChatHistory history={session.history || []} />

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
