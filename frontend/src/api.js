const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

/**
 * GET /supplier/session/context
 * Start or resume a supplier session.
 */
export async function getSessionContext(employeeId, partNumber) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const res = await fetch(`${API_BASE_URL}/supplier/session/context?${params}`);
  if (!res.ok) throw new Error(`Session lookup failed: ${res.statusText}`);
  return res.json();
}

/**
 * POST /supplier/session/upload-excel
 * Upload a costing Excel file for extraction.
 */
export async function uploadExcel(employeeId, partNumber, file) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE_URL}/supplier/session/upload-excel?${params}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Excel upload failed: ${res.statusText}`);
  return res.json();
}

/**
 * POST /supplier/session/negotiate
 * Send a supplier negotiation message.
 */
export async function negotiate(employeeId, partNumber, message) {
  const res = await fetch(`${API_BASE_URL}/supplier/session/negotiate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: employeeId, part_number: partNumber, message }),
  });
  if (!res.ok) throw new Error(`Negotiation failed: ${res.statusText}`);
  return res.json();
}

/**
 * POST /supplier/session/submit-review
 * Submit session for Tata Motors review.
 */
export async function submitForReview(employeeId, partNumber) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const res = await fetch(`${API_BASE_URL}/supplier/session/submit-review?${params}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Submit for review failed: ${res.statusText}`);
  return res.json();
}

/**
 * GET /supplier/session/review
 * Load the Tata Motors review dashboard.
 */
export async function getReviewDashboard(employeeId, partNumber) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const res = await fetch(`${API_BASE_URL}/supplier/session/review?${params}`);
  if (!res.ok) throw new Error(`Review lookup failed: ${res.statusText}`);
  return res.json();
}

/**
 * POST /supplier/session/approve
 * Approve a supplier quotation.
 */
export async function approveSession(employeeId, partNumber) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const res = await fetch(`${API_BASE_URL}/supplier/session/approve?${params}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Approval failed: ${res.statusText}`);
  return res.json();
}

/**
 * POST /supplier/session/reject
 * Reject a supplier quotation.
 */
export async function rejectSession(employeeId, partNumber, reason) {
  const params = new URLSearchParams({
    employee_id: employeeId,
    part_number: partNumber,
    reason,
  });
  const res = await fetch(`${API_BASE_URL}/supplier/session/reject?${params}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Rejection failed: ${res.statusText}`);
  return res.json();
}
