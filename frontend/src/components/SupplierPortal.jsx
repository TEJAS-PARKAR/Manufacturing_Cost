import { useState } from 'react';
import StatusBadge from './StatusBadge';
import Stepper from './Stepper';
import MetricCard from './MetricCard';
import CostChart from './CostChart';
import CostSummary from './CostSummary';
import ChatHistory from './ChatHistory';
import ExcelUpload from './ExcelUpload';
import * as api from '../api';

/** Round display value to 2dp */
function fmt(v) {
  if (v === null || v === undefined || v === '' || v === '—') return '—';
  const n = Number(v);
  return isNaN(n) ? String(v) : n.toFixed(2);
}

export default function SupplierPortal({ session, setSession, employeeId, partNumber }) {
  const [uploading, setUploading] = useState(false);
  const [negotiating, setNegotiating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [alert, setAlert] = useState(null);

  // ── Sheet Optimization State ──
  const [showAllowancePrompt, setShowAllowancePrompt] = useState(false);
  const [checkingSheet, setCheckingSheet] = useState(false);
  const [sheetOptResult, setSheetOptResult] = useState(null);

  const extracted = session.extracted_data || {};
  const status = session.status || 'active';

  // Determine if negotiation should be blocked
  const sheetBlocked = sheetOptResult && sheetOptResult.is_optimal === false;

  // ── Excel upload handler ──
  const handleProcessExcel = async (file) => {
    setUploading(true);
    setAlert(null);
    setSheetOptResult(null);
    try {
      const result = await api.uploadExcel(employeeId, partNumber, file);
      setSession(result);
      setAlert({ type: 'success', message: 'Excel data extracted and merged into the session.' });
      // Show cutting allowance question after successful extraction
      setShowAllowancePrompt(true);
    } catch (err) {
      setAlert({ type: 'error', message: `Excel upload failed: ${err.message}` });
    } finally {
      setUploading(false);
    }
  };

  // ── Cutting Allowance Response ──
  const handleAllowanceResponse = async (includesAllowance) => {
    setShowAllowancePrompt(false);
    setCheckingSheet(true);
    setAlert(null);
    try {
      const result = await api.checkSheetOptimization(employeeId, partNumber, includesAllowance);
      setSheetOptResult(result);
      // Refresh session to get updated sheet_optimization data
      const updatedSession = await api.getSessionContext(employeeId, partNumber);
      setSession(updatedSession);
    } catch (err) {
      setAlert({ type: 'error', message: `Sheet optimization check failed: ${err.message}` });
    } finally {
      setCheckingSheet(false);
    }
  };

  // ── Chat / negotiate handler ──
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;
    setNegotiating(true);
    setAlert(null);
    try {
      const result = await api.negotiate(employeeId, partNumber, chatMessage);
      setSession(result.session);
      setChatMessage('');
    } catch (err) {
      setAlert({ type: 'error', message: `Message processing failed: ${err.message}` });
    } finally {
      setNegotiating(false);
    }
  };

  // ── Submit for review handler ──
  const handleSubmitReview = async () => {
    setSubmitting(true);
    setAlert(null);
    try {
      const result = await api.submitForReview(employeeId, partNumber);
      setSession(result);
      setAlert({ type: 'success', message: 'Session submitted to Tata Motors review dashboard!' });
    } catch (err) {
      setAlert({ type: 'error', message: `Submission failed: ${err.message}` });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      {/* ── Session Overview ── */}
      <div className="session-overview-header">
        <h3>Session Overview</h3>
        <StatusBadge status={status} />
      </div>
      <Stepper status={status} />

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

      {alert && <div className={`alert alert-${alert.type}`}>{alert.message}</div>}

      <hr className="section-divider" />

      {/* ── Excel Upload ── */}
      <ExcelUpload onProcess={handleProcessExcel} loading={uploading} />

      {/* ── Cutting Allowance Question ── */}
      {showAllowancePrompt && (
        <div className="allowance-prompt">
          <div className="allowance-prompt-icon">✂️</div>
          <h4>Cutting / Shearing Allowance</h4>
          <p>Do the extracted part dimensions already include cutting/shearing allowance?</p>
          <div className="allowance-prompt-buttons">
            <button
              className="btn-success"
              onClick={() => handleAllowanceResponse(true)}
            >
              Yes, Allowance Included
            </button>
            <button
              className="btn-warning"
              onClick={() => handleAllowanceResponse(false)}
            >
              No, Apply Allowance
            </button>
          </div>
        </div>
      )}

      {/* ── Sheet Optimization Loading ── */}
      {checkingSheet && (
        <div className="alert alert-info">
          <span className="spinner-overlay">
            <span className="spinner" />
            Validating sheet utilization across approved sizes…
          </span>
        </div>
      )}

      {/* ── Sheet Optimization Result ── */}
      {sheetOptResult && !checkingSheet && (
        <div className="sheet-opt-section">
          <h3 className="section-heading">Sheet Utilization Validation</h3>

          {sheetOptResult.is_optimal === true && (
            <div className="sheet-opt-banner optimal">
              <span className="sheet-opt-icon">✅</span>
              <div>
                <strong>Sheet size is optimal.</strong>
                <p>Current sheet ({sheetOptResult.current_sheet}) provides the best utilization.</p>
              </div>
            </div>
          )}

          {sheetOptResult.is_optimal === false && (
            <div className="sheet-opt-banner not-optimal">
              <span className="sheet-opt-icon">⚠️</span>
              <div>
                <strong>Sheet size is NOT optimal.</strong>
                <p>{sheetOptResult.recommendation}</p>
              </div>
            </div>
          )}

          {sheetOptResult.message && sheetOptResult.optimal === null && (
            <div className="alert alert-warning">{sheetOptResult.message}</div>
          )}

          {/* ── Utilization Table ── */}
          {sheetOptResult.all_options && sheetOptResult.all_options.length > 0 && (
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
                {sheetOptResult.all_options.map((opt) => {
                  const isBest = sheetOptResult.best_option &&
                    opt.sheet_size === sheetOptResult.best_option.sheet_size;
                  const isCurrent = opt.sheet_size === sheetOptResult.current_sheet;
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
        </div>
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

      {/* ── Negotiation Chat ── */}
      <h3 className="section-heading">Negotiation Chat</h3>

      {sheetBlocked && (
        <div className="alert alert-error">
          <strong>Negotiation blocked:</strong> The current sheet size is not optimal.
          Please revise the costing sheet using the recommended sheet size before negotiating.
        </div>
      )}

      <ChatHistory history={session.history || []} currentUserRole="supplier" />

      <form className="chat-input-bar" onSubmit={handleSendMessage}>
        <input
          type="text"
          placeholder="Enter supplier demand..."
          value={chatMessage}
          onChange={(e) => setChatMessage(e.target.value)}
          disabled={negotiating || sheetBlocked}
        />
        <button type="submit" disabled={negotiating || !chatMessage.trim() || sheetBlocked}>
          {negotiating ? '…' : 'Send'}
        </button>
      </form>

      <hr className="section-divider" />

      {/* ── Submit for review ── */}
      {status === 'active' && (
        <div>
          <h3 className="section-heading">Submit for Review</h3>
          <div className="alert alert-info">
            Once submitted, your session will be visible to the Tata Motors review dashboard.
          </div>
          <button
            className="btn-primary"
            onClick={handleSubmitReview}
            disabled={submitting || sheetBlocked}
          >
            {submitting ? (
              <span className="spinner-overlay">
                <span className="spinner" />
                Submitting…
              </span>
            ) : (
              'Submit for Tata Motors Review'
            )}
          </button>
        </div>
      )}

      {status === 'submitted_for_review' && (
        <div className="alert alert-info">
          This session has been submitted for Tata Motors review. Awaiting decision.
        </div>
      )}

      {status === 'approved' && (
        <div className="alert alert-success">
          This session has been <strong>approved</strong> by Tata Motors.
        </div>
      )}

      {status === 'rejected' && (
        <div className="alert alert-error">
          This session has been <strong>rejected</strong> by Tata Motors.
        </div>
      )}
    </div>
  );
}
