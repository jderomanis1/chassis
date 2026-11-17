import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { api } from './api.js';
import './prototype.css';
import './tokens.css';
import './fonts.css';
import './canvas.css';

function App() {
  const [data, setData] = useState(null), [error, setError] = useState(null);
  const [theme, setTheme] = useState(document.documentElement.dataset.theme);
  async function refresh() {
    try {
      const [session, snapshot, layout] = await Promise.all([api('/api/session'), api('/api/snapshot'), api('/api/layout')]);
      setData({ session, snapshot, layout }); setError(null);
    } catch (error) { setError(error.message); setData(null); }
  }
  useEffect(() => {
    refresh();
    const update = () => setTheme(document.documentElement.dataset.theme);
    window.addEventListener('chassis-theme-change', update);
    return () => window.removeEventListener('chassis-theme-change', update);
  }, []);
  useEffect(() => {
    if (!data) return;
    const timer = setInterval(async () => {
      try { if ((await api('/api/version')).etag !== data.snapshot.etag) await refresh(); }
      catch (error) { setError(error.message); }
    }, 5000);
    return () => clearInterval(timer);
  }, [data]);
  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next; setTheme(next);
    try { localStorage.setItem('chassis-theme', next); } catch {}
  }
  return <><header className="top"><a className="brand" href="#/"><span className="brand-mark">✦</span>
    <span><b>CHASSIS</b><small className="mono">Chief of staff console</small></span></a>
    <span className="live mono">{data ? <><i className="dot"/>Live store</> : 'Connecting'}</span>
    <button className="theme-btn" onClick={toggle} aria-label={`Theme: ${theme}. Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>{theme === 'dark' ? '☾' : '☀'} {theme}</button></header>
    <main id="canvas"><div className="intro"><div><p className="mono">Command canvas</p>
      <h1>Every venture. One clear view.</h1><p className="lede">Open a venture to see the work, the links, and what needs you next.</p></div>
      {data && <span className="mode mono">{data.session.writes_enabled ? 'Editing enabled' : 'Read only · editing is off'}</span>}</div>
      {error ? <section className="panel empty" role="alert"><h2>Could not load canvas</h2><p>{error}</p><button className="btn" onClick={refresh}>Try again</button></section>
        : !data ? <section className="panel empty" role="status">Loading your canvas…</section>
        : !data.snapshot.ventures.length ? <section className="panel empty"><h2>No ventures yet</h2><p>Your visible ventures will appear here.</p></section>
        : <section className="panel empty">{data.snapshot.ventures.length} ventures ready</section>}
    </main></>;
}
createRoot(document.getElementById('root')).render(<App/>);
