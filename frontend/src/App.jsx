import { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [limits, setLimits] = useState(null);
  const [options, setOptions] = useState([]);
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('signals');

  const API_BASE = 'http://localhost:8000';

  const handleLogin = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/login`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        setIsLoggedIn(true);
        fetchSignals(); // Load signals immediately on login
      } else {
        alert('Login failed. Check Python terminal.');
      }
    } catch (err) {
      alert('Could not connect to Python API. Is port 8000 running?');
    }
    setLoading(false);
  };

  const fetchLimits = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/limits`);
      const data = await res.json();
      setLimits(data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchOptions = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/sensex-options`);
      const data = await res.json();
      setOptions(data.data || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const fetchSignals = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/signals`);
      const data = await res.json();
      setSignals(data.data || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>📈 Kotak Pro Terminal</h1>
        {!isLoggedIn ? (
          <button onClick={handleLogin} disabled={loading} className="btn primary">
            {loading ? 'Authenticating...' : 'Login to Kotak Neo'}
          </button>
        ) : (
          <span className="status-badge success">🟢 API Connected</span>
        )}
      </header>

      {isLoggedIn && (
        <div className="main-content">
          <div className="tabs">
            <button className={activeTab === 'signals' ? 'tab active' : 'tab'} onClick={() => setActiveTab('signals')}>📡 Live Signals</button>
            <button className={activeTab === 'options' ? 'tab active' : 'tab'} onClick={() => setActiveTab('options')}>🎯 SENSEX Options</button>
            <button className={activeTab === 'limits' ? 'tab active' : 'tab'} onClick={() => setActiveTab('limits')}>📊 Account Limits</button>
          </div>

          <div className="tab-content">
            {/* SIGNALS TAB */}
            {activeTab === 'signals' && (
              <div>
                <button onClick={fetchSignals} className="btn secondary" style={{marginBottom: '1rem'}}>🔄 Refresh Feed</button>
                <div className="signal-feed">
                  {signals.length === 0 ? <p>No signals received yet...</p> : signals.map((sig, idx) => (
                    <div key={idx} className={`signal-card ${sig.status}`}>
                      <div className="signal-header">
                        <strong>{sig.status === 'valid' ? '✅ VALID SIGNAL' : '⏭️ IGNORED'}</strong>
                        <span>{sig.timestamp}</span>
                      </div>
                      {sig.status === 'valid' ? (
                        <div className="signal-body">
                          <h3>{sig.strike} {sig.type}</h3>
                          <p>Entry: <strong>{sig.low} - {sig.high}</strong></p>
                          <p>Token: <code>{sig.token}</code></p>
                        </div>
                      ) : (
                        <div className="signal-body error">
                          <p>Reason: {sig.reason}</p>
                        </div>
                      )}
                      <div className="raw-msg">Raw: {sig.raw_message}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* OPTIONS TAB */}
            {activeTab === 'options' && (
              <div>
                <button onClick={fetchOptions} disabled={loading} className="btn secondary" style={{marginBottom: '1rem'}}>
                  {loading ? 'Downloading Master...' : 'Fetch SENSEX Chain'}
                </button>
                {options.length > 0 && (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Symbol</th><th>Strike</th><th>Type</th><th>Expiry</th><th>Token</th>
                      </tr>
                    </thead>
                    <tbody>
                      {options.map((opt, idx) => (
                        <tr key={idx}>
                          <td>{opt.pSymbolName}</td>
                          <td>{opt.dStrikePrice}</td>
                          <td><span className={`badge ${opt.pOptionType}`}>{opt.pOptionType}</span></td>
                          <td>{opt.pExpiryDate || opt.lExpiryDate}</td>
                          <td><code>{opt.pSymbol}</code></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {/* LIMITS TAB */}
            {activeTab === 'limits' && (
              <div>
                <button onClick={fetchLimits} disabled={loading} className="btn secondary" style={{marginBottom: '1rem'}}>
                  {loading ? 'Fetching...' : 'Get Live Limits'}
                </button>
                {limits && (
                  <pre className="json-box">{JSON.stringify(limits, null, 2)}</pre>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;