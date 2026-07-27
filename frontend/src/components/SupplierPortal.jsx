import { useState } from 'react';
import StatusBadge from './StatusBadge';
import Stepper from './Stepper';
import MetricCard from './MetricCard';
import CostChart from './CostChart';
import CostSummary from './CostSummary';
import ChatHistory from './ChatHistory';
import ExcelUpload from './ExcelUpload';
import * as api from '../api';

export default function SupplierPortal({ session, setSession, employeeId, partNumber }) {
  const [uploading, setUploading] = useState(false);
  const [negotiating, setNegotiating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [chatMessage, setChatMessage] = useState('');
  const [alert, setAlert] = useState(null);

  const extracted = session.extracted_data || {};
  const status = session.status || 'active';

  // ── Excel upload handler ──
  const handleProcessExcel = async (file) => {
    setUploading(true);
    setAlert(null);
    try {
      const result = await api.uploadExcel(employeeId, partNumber, file);
      setSession(result);
      setAlert({ type: 'success', message: 'Excel data extracted and merged into the session.' });
    } catch (err) {
      setAlert({ type: 'error', message: `Excel upload failed: ${err.message}` });
    } finally {
      setUploading(false);
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

      {alert && <div className={`alert alert-${alert.type}`}>{alert.message}</div>}

      <hr className="section-divider" />

      {/* ── Excel Upload ── */}
      <ExcelUpload onProcess={handleProcessExcel} loading={uploading} />

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
      <ChatHistory history={session.history || []} />

      <form className="chat-input-bar" onSubmit={handleSendMessage}>
        <input
          type="text"
          placeholder="Enter supplier demand..."
          value={chatMessage}
          onChange={(e) => setChatMessage(e.target.value)}
          disabled={negotiating}
        />
        <button type="submit" disabled={negotiating || !chatMessage.trim()}>
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
          <button className="btn-primary" onClick={handleSubmitReview} disabled={submitting}>
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
