import { useState, useEffect } from 'react';
import StatusBadge from './StatusBadge';
import MetricCard from './MetricCard';
import CostChart from './CostChart';
import CostSummary from './CostSummary';
import ChatHistory from './ChatHistory';
import ExcelUpload from './ExcelUpload';
import ExtractedDataPanel from './ExtractedDataPanel';
import * as api from '../api';

/** Round display value to 2dp */
function fmt(v) {
  if (v === null || v === undefined || v === '' || v === '—') return '—';
  const n = Number(v);
  return isNaN(n) ? String(v) : n.toFixed(2);
}

/** Workflow steps for the gated flow */
const WORKFLOW_STEPS = [
  { key: 'upload', label: 'Upload Costing Sheet', icon: '📄' },
  { key: 'allowance', label: 'Cutting Allowance', icon: '✂️' },
  { key: 'validation', label: 'Sheet Validation', icon: '✅' },
  { key: 'negotiate', label: 'Negotiate', icon: '💬' },
];

function getWorkflowStep(session, showAllowancePrompt) {
  const extracted = session.extracted_data || {};
  const sheetOpt = session.sheet_optimization || {};
  const awaiting = session.awaiting_allowance_response;

  if (extracted.total_cost == null) return 'upload';
  if (awaiting || showAllowancePrompt) return 'allowance';
  if (!sheetOpt.is_optimal && sheetOpt.is_optimal !== true) return 'validation';
  return 'negotiate';
}

export default function SupplierPortal({ session, setSession, employeeId, partNumber }) {
  const [uploading, setUploading] = useState(false);
  const [negotiating, setNegotiating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [reopening, setReopening] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [alert, setAlert] = useState(null);

  // ── Sheet Optimization State ──
  const [showAllowancePrompt, setShowAllowancePrompt] = useState(false);
  const [checkingSheet, setCheckingSheet] = useState(false);
  const [sheetOptResult, setSheetOptResult] = useState(null);

  const extracted = session.extracted_data || {};
  const status = session.status || 'active';
  const sheetOpt = session.sheet_optimization || {};

  // ── Restore state from session on mount / session change ──
  useEffect(() => {
    if (session.awaiting_allowance_response && extracted.total_cost) {
      setShowAllowancePrompt(true);
    } else {
      setShowAllowancePrompt(false);
    }

    if (sheetOpt && sheetOpt.is_optimal !== undefined) {
      setSheetOptResult(sheetOpt);
    } else {
      setSheetOptResult(null);
    }
  }, [session.session_key, session.awaiting_allowance_response, sheetOpt.is_optimal]);

  // ── Derive blocking state from SESSION data (not just local state) ──
  const needsExcelUpload = extracted.total_cost == null;
  const awaitingAllowance = session.awaiting_allowance_response === true;
  const sheetNotValidated = !sheetOpt || sheetOpt.is_optimal === undefined;
  const sheetNotOptimal = sheetOpt && sheetOpt.is_optimal === false;
  const isRejected = status === 'rejected';

  const chatBlocked = needsExcelUpload || awaitingAllowance || (extracted.total_cost != null && sheetNotValidated) || sheetNotOptimal || isRejected;

  // Determine which blocking message to show
  const getBlockingMessage = () => {
    if (isRejected) return { icon: '🚫', text: 'Session was rejected by Tata Motors. Please reopen the session to continue negotiation.' };
    if (needsExcelUpload) return { icon: '📄', text: 'Please upload a costing Excel sheet to begin the negotiation process.' };
    if (awaitingAllowance) return { icon: '✂️', text: 'Please answer the cutting allowance question above before proceeding.' };
    if (extracted.total_cost && sheetNotValidated) return { icon: '📋', text: 'Sheet optimization must be validated. Please answer the cutting allowance question.' };
    if (sheetNotOptimal) return { icon: '⚠️', text: 'Sheet size is not optimal. Please upload the revised costing sheet using the recommended sheet size.' };
    return null;
  };

  const currentStep = getWorkflowStep(session, showAllowancePrompt);

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

  // ── Reopen after rejection ──
  const handleReopenSession = async () => {
    setReopening(true);
    setAlert(null);
    try {
      const result = await api.reopenSession(employeeId, partNumber);
      setSession(result);
      setSheetOptResult(null);
      setAlert({ type: 'success', message: 'Session reopened for re-negotiation. Please upload a revised costing sheet.' });
    } catch (err) {
      setAlert({ type: 'error', message: `Reopen failed: ${err.message}` });
    } finally {
      setReopening(false);
    }
  };

  const blockingMsg = getBlockingMessage();

  return (
    <div className="supplier-portal-animated">
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

      <ExtractedDataPanel data={extracted} />

      {alert && <div className={`alert alert-${alert.type} fade-in`}>{alert.message}</div>}

      <hr className="section-divider" />

      {/* ── Workflow Gate Indicator ── */}
      {status === 'active' && (
        <div className="workflow-gate">
          <h4 className="workflow-gate-title">Negotiation Workflow</h4>
          <div className="workflow-steps">
            {WORKFLOW_STEPS.map((step, idx) => {
              const stepIdx = WORKFLOW_STEPS.findIndex(s => s.key === currentStep);
              const thisIdx = idx;
              const isCompleted = thisIdx < stepIdx;
              const isCurrent = step.key === currentStep;
              const isPending = thisIdx > stepIdx;
              return (
                <div key={step.key} className={`workflow-step ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isPending ? 'pending' : ''}`}>
                  <div className="workflow-step-icon">
                    {isCompleted ? '✓' : step.icon}
                  </div>
                  <span className="workflow-step-label">{step.label}</span>
                  {idx < WORKFLOW_STEPS.length - 1 && (
                    <div className={`workflow-step-connector ${isCompleted ? 'completed' : ''}`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Excel Upload ── */}
      {(status === 'active' || status === 'rejected') && (
        <ExcelUpload onProcess={handleProcessExcel} loading={uploading} />
      )}

      {/* ── Cutting Allowance Question ── */}
      {showAllowancePrompt && (
        <div className="allowance-prompt fade-in">
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
        <div className="alert alert-info fade-in">
          <span className="spinner-overlay">
            <span className="spinner" />
            Validating sheet utilization across approved sizes…
          </span>
        </div>
      )}

      {/* ── Sheet Optimization Result ── */}
      {sheetOptResult && !checkingSheet && (
        <div className="sheet-opt-section fade-in">
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
                  <th>Gross Weight (kg)</th>
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

      {/* ── Blocking message with context ── */}
      {chatBlocked && blockingMsg && (
        <div className={`negotiation-gate-banner fade-in ${isRejected ? 'rejected' : ''}`}>
          <span className="gate-banner-icon">{blockingMsg.icon}</span>
          <div className="gate-banner-content">
            <strong>{isRejected ? 'Session Rejected' : 'Negotiation Locked'}</strong>
            <p>{blockingMsg.text}</p>
          </div>
        </div>
      )}

      {/* ── Rejection details + Reopen button ── */}
      {isRejected && (
        <div className="rejection-section fade-in">
          {session.rejection_remark && (
            <div className="rejection-remark-card">
              <div className="rejection-remark-header">
                <span className="rejection-remark-icon">📋</span>
                <strong>Rejection Reason</strong>
              </div>
              <p className="rejection-remark-text">{session.rejection_remark}</p>
            </div>
          )}
          <button
            className="btn-reopen"
            onClick={handleReopenSession}
            disabled={reopening}
          >
            {reopening ? (
              <span className="spinner-overlay">
                <span className="spinner" />
                Reopening…
              </span>
            ) : (
              <>🔄 Reopen for Re-negotiation</>
            )}
          </button>
        </div>
      )}

      <ChatHistory history={session.history || []} currentUserRole="supplier" />

      <form className={`chat-input-bar ${chatBlocked ? 'chat-disabled' : ''}`} onSubmit={handleSendMessage}>
        <input
          type="text"
          placeholder={chatBlocked ? 'Complete the workflow steps above to unlock chat...' : 'Enter supplier demand...'}
          value={chatMessage}
          onChange={(e) => setChatMessage(e.target.value)}
          disabled={negotiating || chatBlocked}
        />
        <button type="submit" disabled={negotiating || !chatMessage.trim() || chatBlocked}>
          {negotiating ? (
            <span className="spinner-overlay">
              <span className="spinner" />
            </span>
          ) : 'Send'}
        </button>
      </form>

      <hr className="section-divider" />

      {/* ── Submit for review ── */}
      {status === 'active' && (
        <div className="fade-in">
          <h3 className="section-heading">Submit for Review</h3>
          <div className="alert alert-info">
            Once submitted, your session will be visible to the Tata Motors review dashboard.
          </div>
          <button
            className="btn-primary"
            onClick={handleSubmitReview}
            disabled={submitting || chatBlocked}
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
        <div className="alert alert-info fade-in">
          This session has been submitted for Tata Motors review. Awaiting decision.
        </div>
      )}

      {status === 'approved' && (
        <div className="alert alert-success fade-in">
          This session has been <strong>approved</strong> by Tata Motors.
        </div>
      )}
    </div>
  );
}
