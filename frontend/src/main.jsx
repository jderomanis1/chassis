import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { api } from './api.js';
import { Canvas } from './canvas.jsx';
import { CommandBar } from './command-bar.jsx';
import { applyCommandView } from './commands.js';
import { HoverCard } from './nodes.jsx';
import { Editor } from './editor.jsx';
import { editChanges, linkChange, overviewNodes, presentGraph, priorValues, readVenture, ventureModel } from './records.js';
import { roundPoint } from './place.js';
import './prototype.css';
import './tokens.css';
import './fonts.css';
import './canvas.css';

function applyPending(nodes, pending) {
  if (!pending) return nodes;
  return nodes.map(node => node.id === pending.id ? { ...node, data: { ...node.data, ...pending.changes,
    health: pending.changes.status === 'blocked' ? 'red' : pending.changes.status === 'done' ? 'green' : node.data.health } } : node);
}

function App() {
  const [data, setData] = useState(null), [detail, setDetail] = useState(null), [error, setError] = useState(null);
  const [theme, setTheme] = useState(document.documentElement.dataset.theme);
  const [ventureId, setVentureId] = useState(readVenture(location.hash));
  const [editor, setEditor] = useState(null), [fieldMessage, setFieldMessage] = useState('');
  const [notice, setNotice] = useState(''), [undo, setUndo] = useState([]), [pending, setPending] = useState(null);
  const [query, setQuery] = useState(''), [hits, setHits] = useState([]), [hover, setHover] = useState(null);
  const [commandOpen, setCommandOpen] = useState(false), [viewMode, setViewMode] = useState('show-all'), [fitSignal, setFitSignal] = useState(0);
  const ticket = useRef(0), layoutRef = useRef(null), timer = useRef(0);
  const writes = Boolean(data?.session.writes_enabled);

  async function loadVenture(id) {
    const venture = await api(`/api/ventures/${id}`);
    const tasks = {};
    const initiatives = await Promise.all(venture.initiatives.map(async initiative => {
      const item = await api(`/api/initiatives/${initiative.id}`);
      tasks[initiative.id] = item.tasks;
      return item.initiative;
    }));
    return { venture: venture.venture, initiatives, tasks, graph: await api(`/api/graph?venture=${encodeURIComponent(id)}`) };
  }
  async function load() {
    const current = ++ticket.current;
    const selected = readVenture(location.hash);
    try {
      const [session, snapshot, layout] = await Promise.all([api('/api/session'), api('/api/snapshot'), api('/api/layout')]);
      const nextDetail = selected ? await loadVenture(selected) : null;
      if (current !== ticket.current) return;
      layoutRef.current = layout;
      setData({ session, snapshot, layout }); setDetail(nextDetail); setVentureId(selected);
      setError(null); setPending(null);
    } catch (failure) {
      if (current !== ticket.current) return;
      setError(failure.message); setData(null);
    }
  }
  useEffect(() => {
    load();
    const onTheme = () => setTheme(document.documentElement.dataset.theme);
    const onHash = () => load();
    window.addEventListener('chassis-theme-change', onTheme);
    window.addEventListener('hashchange', onHash);
    return () => { window.removeEventListener('chassis-theme-change', onTheme); window.removeEventListener('hashchange', onHash); };
  }, []);
  useEffect(() => {
    if (!data) return undefined;
    const poll = setInterval(async () => {
      try { if ((await api('/api/version')).etag !== data.snapshot.etag) await load(); }
      catch (failure) { setError(failure.message); }
    }, 5000);
    return () => clearInterval(poll);
  }, [data]);
  useEffect(() => {
    function onKey(event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); setCommandOpen(true); return; }
      if (event.key === 'Escape') {
        if (commandOpen) { setCommandOpen(false); return; }
        if (editor) setEditor(null); else if (readVenture(location.hash)) location.hash = '#/';
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z' && !editor && !commandOpen && writes) { event.preventDefault(); undoLast(); }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });
  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next; setTheme(next);
    try { localStorage.setItem('chassis-theme', next); } catch { /* preference is optional */ }
  }
  function persistLayout(next) {
    if (!writes || !data) return;
    layoutRef.current = next;
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      try {
        const saved = await api('/api/layout', { method: 'PUT', csrf: data.session.csrf, data: layoutRef.current });
        layoutRef.current = saved; setData(current => current ? { ...current, layout: saved } : current);
      } catch (failure) { setNotice(failure.message); }
    }, 200);
  }
  function onLayout(moved, viewport) {
    const positions = { ...(layoutRef.current?.positions || {}) };
    for (const node of moved) positions[node.id] = roundPoint(node.position);
    persistLayout({ positions, collapsed: layoutRef.current?.collapsed || [], hidden: layoutRef.current?.hidden || [], viewport });
  }
  function hideCard(id) {
    const hidden = [...new Set([...(layoutRef.current?.hidden || []), id])].sort();
    persistLayout({ ...(layoutRef.current || { positions: {}, collapsed: [], viewport: { x: 0, y: 0, zoom: 1 } }), hidden });
  }
  async function openEdit(record) {
    if (!writes) return;
    const source = record.kind === 'venture' ? (await api(`/api/ventures/${record.id}`)).venture : record;
    const next = record.kind === 'venture'
      ? { ...record, title: source.title, status: source.status, next_step: source.next_step, version: source.version, kind: 'venture' }
      : record;
    setFieldMessage(''); setEditor(next);
  }
  async function save(fields) {
    if (editor.kind === 'task' && fields.status === 'blocked' && !fields.blocker_reason.trim()) {
      setFieldMessage('blocker_reason is required when a task is blocked'); return;
    }
    const changes = editChanges(editor.kind, editor, fields);
    if (!Object.keys(changes).length) { setEditor(null); return; }
    setPending({ id: editor.id, changes });
    try {
      const result = await api(`/api/records/${encodeURIComponent(editor.id)}`, { method: 'PATCH', csrf: data.session.csrf,
        data: { changes, expected_version: editor.version } });
      setUndo(stack => [...stack, { id: editor.id, changes: priorValues(changes, editor), version: result.record.version }].slice(-10));
      setEditor(null); setFieldMessage(''); setNotice(''); await load();
    } catch (failure) {
      setPending(null);
      if (failure.code === 'conflict') { setEditor(null); setNotice('Changed elsewhere. Reloaded the latest.'); await load(); }
      else setFieldMessage(failure.message);
    }
  }
  async function undoLast() {
    const entry = undo.at(-1);
    if (!entry || !writes) return;
    try {
      await api(`/api/records/${encodeURIComponent(entry.id)}`, { method: 'PATCH', csrf: data.session.csrf,
        data: { changes: entry.changes, expected_version: entry.version } });
      setUndo(stack => stack.slice(0, -1)); setNotice(''); await load();
    } catch (failure) {
      if (failure.code === 'conflict') setNotice('Changed elsewhere. Reloaded the latest.');
      else setNotice(failure.message);
      await load();
    }
  }
  async function search(event) {
    event.preventDefault();
    try { setHits((await api(`/api/search?q=${encodeURIComponent(query)}`)).hits || []); }
    catch (failure) { setNotice(failure.message); }
  }
  const source = useMemo(() => {
    if (!data) return null;
    if (!ventureId) return { view: 'overview', nodes: applyPending(overviewNodes(data.snapshot.ventures), pending), edges: [] };
    if (!detail) return null;
    const graph = ventureModel(detail);
    return { view: ventureId, title: detail.venture.title, nodes: applyPending(graph.nodes, pending), edges: graph.edges };
  }, [data, detail, ventureId, pending]);
  const hiddenIds = data?.layout?.hidden || [];
  const hiddenHere = (source?.nodes || []).filter(node => hiddenIds.includes(node.id));
  const model = useMemo(() => {
    if (!source) return null;
    const visible = presentGraph(source.nodes, source.edges, hiddenIds);
    return { ...source, ...visible, ...applyCommandView(visible.nodes, visible.edges, viewMode) };
  }, [source, hiddenIds, viewMode]);
  function runIntent(intent) {
    if (intent.command === 'fit') setFitSignal(value => value + 1);
    if (intent.command === 'back') location.hash = '#/';
    if (intent.command === 'zoom') location.hash = `#/v/${intent.id}`;
    if (intent.command === 'show-all' || intent.command === 'only-blocked' || intent.command === 'only-active') {
      setViewMode(intent.command);
      setFitSignal(value => value + 1);
    }
  }
  async function linkCards(connection) {
    const nodes = source?.nodes || [];
    const proposal = linkChange(nodes.find(node => node.id === connection.source)?.data,
      nodes.find(node => node.id === connection.target)?.data);
    if (!proposal.ok) { setNotice(proposal.message); return; }
    if (!writes) { setNotice('Read only · editing is off'); return; }
    try {
      const result = await api(`/api/records/${encodeURIComponent(proposal.id)}`, { method: 'PATCH', csrf: data.session.csrf,
        data: { changes: proposal.changes, expected_version: proposal.version } });
      const target = nodes.find(node => node.id === proposal.id);
      setUndo(stack => [...stack, { id: proposal.id, changes: { depends_on: [...(target?.data.depends_on || [])] },
        version: result.record.version }].slice(-10));
      setNotice(''); await load();
    } catch (failure) { setNotice(failure.message); }
  }
  function showHidden() {
    const back = new Set(hiddenHere.map(node => node.id));
    persistLayout({ ...(layoutRef.current || {}), hidden: (layoutRef.current?.hidden || []).filter(id => !back.has(id)) });
  }

  return <><header className="top"><a className="brand" href="#/"><span className="brand-mark">✦</span>
    <span><b>CHASSIS</b><small className="mono">Chief of staff console</small></span></a>
    <span className="live mono">{data ? <><i className="dot"/>Live store</> : 'Connecting'}</span>
    <button className="theme-btn" onClick={toggle} aria-label={`Theme: ${theme}. Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>{theme === 'dark' ? '☾' : '☀'} {theme}</button></header>
    <main id="canvas"><div className="intro"><div><p className="mono">Command canvas</p>
      <h1>Every venture. One clear view.</h1><p className="lede">Open a venture to see the work, the links, and what needs you next.</p></div>
      <span className="intro-actions">{writes ? <button className="btn ghost" type="button" onClick={undoLast} disabled={!undo.length}>Undo</button> : null}
        {data && <span className="mode mono">{writes ? 'Editing enabled' : 'Read only · editing is off'}</span>}</span></div>
      {ventureId && <p className="crumbs"><button type="button" className="back" onClick={() => { location.hash = '#/'; }}>Back to all</button>
        <span className="mono">{detail?.venture.title || ventureId}</span></p>}
      {notice ? <p className="attn" role="status">{notice}</p> : null}
      <form className="search" role="search" onSubmit={search}>
        <label className="sr" htmlFor="record-search">Search records</label>
        <input id="record-search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Search visible records" />
        <button className="btn" type="submit">Search</button>
      </form>
      {hits.length ? <ul className="hits">{hits.map(hit => <li key={hit.id}><button type="button" onClick={() => { if (hit.type === 'venture') location.hash = `#/v/${hit.id}`; }}>{hit.title}</button></li>)}</ul> : null}
      <HoverCard record={hover} />
      {hiddenHere.length ? <button type="button" className="btn ghost" onClick={showHidden}>Show hidden ({hiddenHere.length})</button> : null}
      {error ? <section className="panel empty" role="alert"><h2>Could not load canvas</h2><p>{error}</p><button className="btn" onClick={load}>Try again</button></section>
        : !data || (ventureId && !model) ? <section className="panel empty" role="status">Loading your canvas…</section>
        : !data.snapshot.ventures.length ? <section className="panel empty"><h2>No ventures yet</h2><p>Your visible ventures will appear here.</p></section>
        : <Canvas model={model} layout={data.layout} writes={writes} fitSignal={fitSignal} onLayout={onLayout} onOpen={id => { location.hash = `#/v/${id}`; }} onEdit={openEdit} onHover={setHover} onClear={() => setHover(null)} onHide={hideCard} onLink={linkCards} />}
    </main>
    {editor ? <Editor record={editor} message={fieldMessage} onClose={() => setEditor(null)} onSave={save} /> : null}
    <CommandBar open={commandOpen} ventures={data?.snapshot?.ventures || []} onClose={() => setCommandOpen(false)} onRun={runIntent} /></>;
}
createRoot(document.getElementById('root')).render(<App/>);
