import { useEffect, useRef, useState } from 'react';

const STATUSES = ['planned', 'in_progress', 'blocked', 'done'];
const blank = record => ({
  title: record.title || '', status: record.status || '', next_step: record.next_step || '',
  blocker_reason: record.blocker_reason || '', due_at: record.due_at || '',
});

export function Editor({ record, message, canEdit = true, conflict, generation = 0, bindClose, onClose, onUseLatest, onSave }) {
  const titleRef = useRef(null), alertRef = useRef(null);
  const [fields, setFields] = useState(() => blank(record));
  const [busy, setBusy] = useState(false), [ask, setAsk] = useState(false), [seen, setSeen] = useState(generation);
  const task = record.kind === 'task';
  if (generation !== seen) { setSeen(generation); setFields(blank(record)); }
  useEffect(() => { titleRef.current?.focus(); }, []);
  useEffect(() => { if (conflict) alertRef.current?.focus(); }, [conflict]);
  const dirty = Object.keys(fields).some(key => fields[key] !== blank(record)[key]);
  function requestClose() { if (conflict && dirty) setAsk(true); else onClose(); }
  useEffect(() => { bindClose?.(requestClose); });
  function update(name, value) { setFields(current => ({ ...current, [name]: value })); }
  async function run(next) {
    if (busy || !canEdit) return;
    setBusy(true); try { await onSave(next); } finally { setBusy(false); }
  }
  function submit(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    run({
      title: String(data.get('title') ?? ''), status: String(data.get('status') ?? ''),
      next_step: String(data.get('next_step') ?? ''), blocker_reason: String(data.get('blocker_reason') ?? ''),
      due_at: String(data.get('due_at') ?? ''),
    });
  }
  const gate = canEdit ? undefined : true;
  const reconnect = canEdit ? undefined : 'Reconnect to edit';
  return (
    <>
      <div className="scrim on" onClick={requestClose} />
      <form className="drawer on editor-form" role="dialog" aria-label={`Edit ${record.title}`} onSubmit={submit}>
        <header><h2 title={record.title}>Edit {record.title}</h2><button type="button" className="x" aria-label="Close editor" onClick={requestClose}>×</button></header>
        <div className="body">
          {conflict ? <section className="conflict" role="alert"><h3 ref={alertRef} tabIndex={-1}>Your edit was not saved</h3><p>This card changed while you were editing.</p>
            {conflict.rows.map(row => <p key={row.key}>Latest: {row.latest} Yours: {row.yours}</p>)}
            <button type="button" className="btn" aria-disabled={gate} title={reconnect} onClick={() => run(fields)}>Keep mine and save again</button><button type="button" className="btn ghost" onClick={onUseLatest}>Use latest</button></section> : null}
          {ask ? <div><p>Discard your changes?</p><button type="button" className="btn" onClick={onClose}>Discard</button><button type="button" className="btn ghost" onClick={() => setAsk(false)}>Keep editing</button></div> : null}
          <label>Title<input id="edit-title" name="title" ref={titleRef} value={fields.title} readOnly={busy} onChange={event => update('title', event.target.value)} required autoComplete="off" /></label>
          <label>Status<select name="status" value={fields.status} disabled={busy} onChange={event => update('status', event.target.value)}>
            {STATUSES.map(status => <option key={status} value={status}>{status.replaceAll('_', ' ')}</option>)}
          </select></label>
          <label>Next step<input name="next_step" value={fields.next_step} readOnly={busy} onChange={event => update('next_step', event.target.value)} required autoComplete="off" onKeyDown={event => { if (event.key === 'Enter') { event.preventDefault(); if (canEdit && !busy) event.currentTarget.form?.requestSubmit(); } }} /></label>
          {task ? <label>Blocker reason<input name="blocker_reason" value={fields.blocker_reason} readOnly={busy} onChange={event => update('blocker_reason', event.target.value)} autoComplete="off" /></label> : null}
          {task ? <label>Due date<input name="due_at" value={fields.due_at} readOnly={busy} placeholder="YYYY-MM-DD" onChange={event => update('due_at', event.target.value)} autoComplete="off" /></label> : null}
          {message ? <p role="alert">{message}</p> : null}
          <button className="btn" type="submit" disabled={busy || undefined} aria-disabled={gate} title={reconnect}>{busy ? 'Saving...' : 'Save'}</button>
        </div>
      </form>
    </>
  );
}
