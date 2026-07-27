import { useState } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import LoginPage from './components/LoginPage';
import SessionForm from './components/SessionForm';
import SupplierPortal from './components/SupplierPortal';
import TataPortal from './components/TataPortal';
import * as api from './api';

// ── Credentials from env or defaults (build-time embedded) ──
const CREDENTIALS = {
  Supplier: {
    username: import.meta.env.VITE_SUPPLIER_USERNAME || 'supplier',
    password: import.meta.env.VITE_SUPPLIER_PASSWORD || 'supplier123',
  },
  'Tata Motors': {
    username: import.meta.env.VITE_TATA_USERNAME || 'tata',
    password: import.meta.env.VITE_TATA_PASSWORD || 'tata123',
  },
};

export default function App() {
  // ── Auth state (mirrors st.session_state) ──
  const [portal, setPortal] = useState('Supplier');
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState('');

  // ── Session state ──
  const [session, setSession] = useState(null);
  const [employeeId, setEmployeeId] = useState('');
  const [partNumber, setPartNumber] = useState('');
  const [sessionLoading, setSessionLoading] = useState(false);

  // ── Portal switch (resets auth, like Streamlit) ──
  const handlePortalChange = (newPortal) => {
    if (newPortal !== portal) {
      setAuthenticated(false);
      setUsername('');
      setSession(null);
    }
    setPortal(newPortal);
  };

  // ── Login ──
  const handleLogin = (user, pass, onError) => {
    const expected = CREDENTIALS[portal];
    if (user === expected.username && pass === expected.password) {
      setAuthenticated(true);
      setUsername(user);
    } else {
      onError('Invalid credentials. Please try again.');
    }
  };

  // ── Logout ──
  const handleLogout = () => {
    setAuthenticated(false);
    setUsername('');
    setSession(null);
  };

  // ── Start / Resume Session ──
  const handleStartSession = async (empId, partNum) => {
    setSessionLoading(true);
    setEmployeeId(empId);
    setPartNumber(partNum);
    try {
      const result = await api.getSessionContext(empId, partNum);
      setSession(result);
    } catch (err) {
      alert(`Unable to reach the backend: ${err.message}`);
    } finally {
      setSessionLoading(false);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        portal={portal}
        onPortalChange={handlePortalChange}
        authenticated={authenticated}
        username={username}
        onLogout={handleLogout}
      />

      <main className="main-content">
        <Header />

        {/* ── Login gate ── */}
        {!authenticated && (
          <LoginPage portal={portal} onLogin={handleLogin} />
        )}

        {/* ── Authenticated content ── */}
        {authenticated && (
          <>
            <SessionForm onStartSession={handleStartSession} loading={sessionLoading} />

            <hr className="section-divider" />

            {/* ── Supplier Portal ── */}
            {portal === 'Supplier' && session && (
              <SupplierPortal
                session={session}
                setSession={setSession}
                employeeId={employeeId}
                partNumber={partNumber}
              />
            )}

            {/* ── Tata Motors Portal ── */}
            {portal === 'Tata Motors' && (
              <TataPortal
                employeeId={employeeId}
                partNumber={partNumber}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}
