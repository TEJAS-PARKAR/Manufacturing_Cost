const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

// ---------- Token helpers (localStorage-based) ----------
const TOKEN_KEY = 'auth_token';
const ROLE_KEY = 'auth_role';
const USER_KEY = 'auth_username';

export function saveAuth({ token, role, username }) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ROLE_KEY, role);
  localStorage.setItem(USER_KEY, username);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRole() {
  return localStorage.getItem(ROLE_KEY);
}

export function getUsername() {
  return localStorage.getItem(USER_KEY);
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(USER_KEY);
}

export function isLoggedIn() {
  return !!getToken();
}

// ---------- Central fetch wrapper: attaches token + handles 401 ----------
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearAuth();
    // Force back to login on expired/invalid token
    window.location.reload();
    return res;  // unreachable, but satisfies return type
  }
  if (res.status === 403) {
    throw new Error('You are not allowed to access this resource.');
  }
  return res;
}

// ---------- AUTH ----------

/**
 * POST /login
 * Authenticate and store the returned token + role.
 */
export async function login(username, password) {
  const res = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'Invalid username or password');
  }
  const data = await res.json(); // { token, role, username }
  saveAuth(data);
  return data;
}

// ---------- SESSION APIS (all now token-authenticated) ----------

export async function getSessionContext(employeeId, partNumber) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const res = await apiFetch(`/supplier/session/context?${params}`);
  if (!res.ok) throw new Error(`Session lookup failed: ${res.statusText}`);
  return res.json();
}

export async function startSession(employeeId, partNumber) {
  const res = await apiFetch(`/supplier/session/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: employeeId, part_number: partNumber }),
  });
  if (!res.ok) throw new Error(`Session start failed: ${res.statusText}`);
  return res.json();
}

export async function uploadExcel(employeeId, partNumber, file) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const formData = new FormData();
  formData.append('file', file);
  const res = await apiFetch(`/supplier/session/upload-excel?${params}`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) throw new Error(`Excel upload failed: ${res.statusText}`);
  return res.json();
}

export async function negotiate(employeeId, partNumber, message) {
  const res = await apiFetch(`/supplier/session/negotiate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ employee_id: employeeId, part_number: partNumber, message }),
  });
  if (!res.ok) throw new Error(`Negotiation failed: ${res.statusText}`);
  return res.json();
}

export async function submitForReview(employeeId, partNumber) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const res = await apiFetch(`/supplier/session/submit-review?${params}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Submit for review failed: ${res.statusText}`);
  return res.json();
}

export async function getReviewDashboard(employeeId, partNumber) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const res = await apiFetch(`/supplier/session/review?${params}`);
  if (!res.ok) throw new Error(`Review lookup failed: ${res.statusText}`);
  return res.json();
}

export async function approveSession(employeeId, partNumber) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const res = await apiFetch(`/supplier/session/approve?${params}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Approval failed: ${res.statusText}`);
  return res.json();
}

export async function rejectSession(employeeId, partNumber, reason) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber, reason });
  const res = await apiFetch(`/supplier/session/reject?${params}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Rejection failed: ${res.statusText}`);
  return res.json();
}

export async function checkSheetOptimization(employeeId, partNumber, includesCuttingAllowance = true) {
  const params = new URLSearchParams({
    employee_id: employeeId,
    part_number: partNumber,
    includes_cutting_allowance: includesCuttingAllowance,
  });
  const res = await apiFetch(`/supplier/session/check-sheet-optimization?${params}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Sheet optimization check failed: ${res.statusText}`);
  return res.json();
}

export async function reopenSession(employeeId, partNumber) {
  const params = new URLSearchParams({ employee_id: employeeId, part_number: partNumber });
  const res = await apiFetch(`/supplier/session/reopen?${params}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Reopen session failed: ${res.statusText}`);
  return res.json();
}