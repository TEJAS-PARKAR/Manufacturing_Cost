import { useState } from 'react';

export default function LoginPage({ portal, onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const portalDesc =
    portal === 'Supplier'
      ? 'Upload costing sheets and negotiate with Tata Motors AI buyer.'
      : 'Review supplier quotes, compare benchmarks, and make decisions.';

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    onLogin(username, password, (errMsg) => setError(errMsg));
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h2>{portal} Portal</h2>
          <p>{portalDesc}</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="login-username">Username</label>
            <input
              id="login-username"
              type="text"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>

          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          {error && <div className="alert alert-error">{error}</div>}

          <button type="submit" className="btn-primary">Login</button>
        </form>
      </div>
    </div>
  );
}
