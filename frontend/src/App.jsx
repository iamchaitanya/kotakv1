import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [settings, setSettings] = useState({
    lots: 1,
    product_type: "MIS",
    order_type: "L",
    price_mode: "LOW",
    is_trading_active: false
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/settings')
      .then(res => res.json())
      .then(data => {
        setSettings(data.data);
        setLoading(false);
      })
      .catch(err => console.error("Failed to fetch settings:", err));
  }, []);

  const updateBackend = async (newSettings) => {
    setSettings(newSettings); 
    try {
      await fetch('http://127.0.0.1:8000/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings)
      });
    } catch (err) {
      console.error("Failed to sync setting to backend:", err);
    }
  };

  const toggleTrading = () => updateBackend({ ...settings, is_trading_active: !settings.is_trading_active });
  const setSetting = (key, value) => updateBackend({ ...settings, [key]: value });
  const adjustLots = (delta) => updateBackend({ ...settings, lots: Math.max(1, settings.lots + delta) });

  const triggerEmergencyStop = async () => {
    if(!window.confirm("🚨 ARE YOU SURE? This will stop trading and clear all pending orders!")) return;
    try {
      const response = await fetch('http://127.0.0.1:8000/api/emergency-stop', { method: 'POST' });
      const data = await response.json();
      alert(data.message);
      setSettings({ ...settings, is_trading_active: false });
    } catch (err) {
      alert("Failed to hit Emergency Stop! Check Server connection.");
    }
  };

  const toggleBtnStyle = (isActive) => ({
    flex: 1, padding: '15px', fontSize: '16px', fontWeight: 'bold', cursor: 'pointer',
    backgroundColor: isActive ? '#007bff' : '#f0f0f0',
    color: isActive ? 'white' : '#333',
    border: '1px solid #ccc', borderRadius: '6px', margin: '0 5px', transition: '0.1s'
  });

  const chipBtnStyle = {
    padding: '10px 15px', cursor: 'pointer', fontWeight: 'bold', 
    backgroundColor: '#eee', color: '#333', border: '1px solid #ccc', borderRadius: '4px'
  };

  if (loading) return <h2 style={{textAlign: 'center', marginTop: '50px', color: '#333'}}>Connecting to Bot Engine...</h2>;

  return (
    // ADDED: color: '#333' to the main wrapper to force dark text globally
    <div style={{ padding: '20px', fontFamily: 'sans-serif', maxWidth: '700px', margin: '0 auto', color: '#333' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>⚡ Quick-Action Trading Terminal</h1>
      
      {/* STATUS & ARMING */}
      <div style={{ 
        padding: '20px', borderRadius: '8px', textAlign: 'center',
        backgroundColor: settings.is_trading_active ? '#e6ffe6' : '#ffe6e6',
        border: `3px solid ${settings.is_trading_active ? '#28a745' : '#dc3545'}`,
        marginBottom: '30px',
        color: '#000' // Forced dark text
      }}>
        <h2 style={{ margin: '0 0 15px 0' }}>{settings.is_trading_active ? '🟢 SYSTEM ARMED' : '🔴 SYSTEM PAUSED'}</h2>
        <p style={{ margin: '0 0 20px 0', fontWeight: '500' }}>The bot is currently {settings.is_trading_active ? 'executing signals.' : 'ignoring signals.'}</p>
        
        <button onClick={toggleTrading} style={{ 
          padding: '15px 40px', fontSize: '18px', fontWeight: 'bold', cursor: 'pointer',
          backgroundColor: settings.is_trading_active ? '#dc3545' : '#28a745', color: 'white', border: 'none', borderRadius: '6px'
        }}>
          {settings.is_trading_active ? 'Pause Trading' : 'Arm Bot (Enable Auto-Trade)'}
        </button>
      </div>

      {/* STRATEGY CONTROLS */}
      <div style={{ backgroundColor: '#fff', padding: '20px', borderRadius: '8px', border: '1px solid #ddd', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}>
        <h3 style={{ marginTop: 0, borderBottom: '2px solid #eee', paddingBottom: '10px', color: '#111' }}>Strategy Parameters</h3>
        
        {/* LOT SIZING */}
        <div style={{ marginBottom: '25px' }}>
          <p style={{ fontWeight: 'bold', margin: '0 0 10px 0', color: '#333' }}>Position Size (Lots)</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '10px' }}>
            <button onClick={() => adjustLots(-1)} style={{ padding: '15px 25px', fontSize: '20px', cursor: 'pointer', color: '#000' }}>-</button>
            {/* ADDED: color: '#000' to the lot number */}
            <div style={{ fontSize: '24px', fontWeight: 'bold', minWidth: '50px', textAlign: 'center', color: '#000' }}>{settings.lots}</div>
            <button onClick={() => adjustLots(1)} style={{ padding: '15px 25px', fontSize: '20px', cursor: 'pointer', color: '#000' }}>+</button>
            <div style={{ display: 'flex', gap: '5px', marginLeft: 'auto' }}>
              <button style={chipBtnStyle} onClick={() => setSetting('lots', 1)}>1</button>
              <button style={chipBtnStyle} onClick={() => setSetting('lots', 5)}>5</button>
              <button style={chipBtnStyle} onClick={() => setSetting('lots', 10)}>10</button>
            </div>
          </div>
        </div>

        {/* PRODUCT TYPE */}
        <div style={{ marginBottom: '20px' }}>
          <p style={{ fontWeight: 'bold', margin: '0 0 10px 0', color: '#333' }}>Product Type</p>
          <div style={{ display: 'flex' }}>
            <button style={toggleBtnStyle(settings.product_type === 'MIS')} onClick={() => setSetting('product_type', 'MIS')}>MIS (Intraday)</button>
            <button style={toggleBtnStyle(settings.product_type === 'NRML')} onClick={() => setSetting('product_type', 'NRML')}>NRML (Overnight)</button>
          </div>
        </div>

        {/* ORDER TYPE */}
        <div style={{ marginBottom: '20px' }}>
          <p style={{ fontWeight: 'bold', margin: '0 0 10px 0', color: '#333' }}>Execution Type</p>
          <div style={{ display: 'flex' }}>
            <button style={toggleBtnStyle(settings.order_type === 'L')} onClick={() => setSetting('order_type', 'L')}>Limit Order</button>
            <button style={toggleBtnStyle(settings.order_type === 'MKT')} onClick={() => setSetting('order_type', 'MKT')}>Market Order</button>
          </div>
        </div>

        {/* PRICE TARGET */}
        <div style={{ marginBottom: '10px' }}>
          <p style={{ fontWeight: 'bold', margin: '0 0 10px 0', color: '#333' }}>Signal Target Range</p>
          <div style={{ display: 'flex' }}>
            <button style={toggleBtnStyle(settings.price_mode === 'LOW')} onClick={() => setSetting('price_mode', 'LOW')}>Bid at LOW Price</button>
            <button style={toggleBtnStyle(settings.price_mode === 'HIGH')} onClick={() => setSetting('price_mode', 'HIGH')}>Bid at HIGH Price</button>
          </div>
        </div>
      </div>

      {/* KILL SWITCH */}
      <div style={{ marginTop: '30px' }}>
        <button onClick={triggerEmergencyStop} style={{ 
            backgroundColor: '#cc0000', color: 'white', padding: '20px', fontSize: '20px', 
            fontWeight: 'bold', borderRadius: '8px', border: 'none', cursor: 'pointer', width: '100%',
            boxShadow: '0 4px 6px rgba(204,0,0,0.3)'
          }}>
          🚨 EMERGENCY KILL SWITCH 🚨
        </button>
      </div>
    </div>
  )
}

export default App