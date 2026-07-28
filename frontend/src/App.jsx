import { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import LoginPage from './components/LoginPage';
import SessionForm from './components/SessionForm';
import SupplierPortal from './components/SupplierPortal';
import TataPortal from './components/TataPortal';
import * as api from './api';

export default function App() {
  const [portal, setPortal] = useState('Supplier');
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [role, setRole] = useState('');

  const [session, setSession] = useState(null);
  const [employeeId, setEmployeeId] = useState('');
  const [partNumber, setPartNumber] = useState('');
  const [sessionLoading, setSessionLoading] = useState(false);

  // ── Restore session on refresh (token persists in localStorage) ──
  useEffect(() => {
    if (api.isLoggedIn()) {
      setAuthenticated(true);
      setUsername(api.getUsername() || '');
      const savedRole = api.getRole();
      setRole(savedRole);
      setPortal(savedRole === 'tata' ? 'Tata Motors' : 'Supplier');
    }
  }, []);

  const handlePortalChange = (newPortal) => {
    setPortal(newPortal);
  };

  // ── Login now calls the BACKEND ──
  const handleLogin = async (user, pass, onError) => {
    try {
      const data = await api.login(user.trim(), pass);
      setAuthenticated(true);
      setUsername(data.username);
      setRole(data.role);
      // Route by the role the backend assigned, not the clicked tab
      setPortal(data.role === 'tata' ? 'Tata Motors' : 'Supplier');
    } catch (err) {
      onError(err.message || 'Invalid credentials. Please try again.');
    }
  };

  const handleLogout = () => {
    api.clearAuth();
    setAuthenticated(false);
    setUsername('');
    setRole('');
    setSession(null);
  };

  const handleStartSession = async (empId, partNum) => {
    setSessionLoading(true);
    setEmployeeId(empId);
    setPartNumber(partNum);
    try {
      const result = await api.getSessionContext(empId, partNum);
      setSession(result);
    } catch (err) {
      alert(`Unable to load session: ${err.message}`);
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

        {!authenticated && (
          <LoginPage portal={portal} onLogin={handleLogin} />
        )}

        {authenticated && (
          <>
            <SessionForm onStartSession={handleStartSession} loading={sessionLoading} />

            <hr className="section-divider" />

            {role === 'supplier' && session && (
              <SupplierPortal
                session={session}
                setSession={setSession}
                employeeId={employeeId}
                partNumber={partNumber}
              />
            )}

            {role === 'tata' && (
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