import { useEffect, useRef, useState } from 'react';

const STATUSES = ['planned', 'in_progress', 'blocked', 'done'];

export function Editor({ record, message, canEdit = true, conflict, bindClose, onClose, onUseLatest, onSave }) {
  const titleRef = useRef(null);
  const saving = useRef(false);
  const alertRef = useRef(null);
  const keepRef = useRef(null);
  const restoreRef = useRef(null);
  const [fields, setFields] = useState({
    title: record.title, status: record.status, next_step: record.next_step,
    blocker_reason: record.blocker_reason, due_at: record.due_at,
  });
  const [busy, setBusy] = useState(false);
  const [ask, setAsk] = useState(false);
  const task = record.kind === 'task';
  useEffect(() => { titleRef.current?.focus(); }, []);
  useEffect(() => { if (conflict) alertRef.current?.focus(); }, [conflict]);
  useEffect(() => { if (ask) keepRef.current?.focus(); }, [ask]);
  const dirty = ['title', 'status', 'next_step', 'blocker_reason', 'due_at'].some(key => (
    (fields[key] || '') !== (record[key] || '')
  ));
  function requestClose() {
    if (saving.current) return;
    if (ask) {
      setAsk(false);
      restoreRef.current?.focus();
      return;
    }
    if (!(conflict && dirty)) return onClose();
    restoreRef.current = document.activeElement;
    setAsk(true);
  }
  useEffect(() => { bindClose?.(requestClose); });
  function update(name, value) { setFields(current => ({ ...current, [name]: value })); }
  function whenIdle(action) {
    if (saving.current) return;
    action();
  }
  async function run(next) {
    if (saving.current || !canEdit) return;
    saving.current = true;
    setBusy(true);
    try {
      await onSave(next);
    } finally {
      saving.current = false;
      setBusy(false);
    }
  }
  function submit(event) {
    event.preventDefault();
    if (ask || conflict) return;
    const data = new FormData(event.currentTarget);
    const next = {
      title: String(data.get('title') ?? ''),
      status: String(data.get('status') ?? ''),
      next_step: String(data.get('next_step') ?? ''),
      blocker_reason: String(data.get('blocker_reason') ?? ''),
      due_at: String(data.get('due_at') ?? ''),
    };
    run(next);
  }
  const locked = canEdit ? undefined : true;
  const reconnect = canEdit ? undefined : 'Reconnect to edit';
  return (
    <>
      <div className="scrim on" onClick={requestClose} />
      <form className="drawer on editor-form" role="dialog" aria-label={`Edit ${record.title}`} onSubmit={submit}>
        <header><h2 title={record.title}>Edit {record.title}</h2><button type="button" className="x" aria-label="Close editor" onClick={requestClose}>×</button></header>
        <div className="body">
          {conflict ? <section className="conflict" role="alert">
            <h3 ref={alertRef} tabIndex={-1}>Your edit was not saved</h3>
            <p>This card changed while you were editing.</p>
            {conflict.latest ? conflict.rows.map(row => (
              <p key={row.key}>Latest: {row.latest} Yours: {row.yours}</p>
            )) : (
              <p>Couldn't load the latest version</p>
            )}
            {conflict.latest ? <button
              type="button"
              className="btn"
              aria-disabled={locked}
              title={reconnect}
              onClick={() => run(fields)}
            >Keep mine and save again</button> : null}
            <button type="button" className="btn ghost" onClick={() => whenIdle(onUseLatest)}>Use latest</button>
          </section> : null}
          {ask ? <div role="alertdialog" aria-label="Discard your changes?">
            <p>Discard your changes?</p>
            <button type="button" className="btn" onClick={() => whenIdle(onClose)}>Discard</button>
            <button type="button" className="btn ghost" ref={keepRef} onClick={requestClose}>Keep editing</button>
          </div> : null}
          <label>Title<input id="edit-title" name="title" ref={titleRef} value={fields.title} readOnly={busy} onChange={event => update('title', event.target.value)} required autoComplete="off" /></label>
          <label>Status<select name="status" value={fields.status} disabled={busy} onChange={event => update('status', event.target.value)}>
            {STATUSES.map(status => <option key={status} value={status}>{status.replaceAll('_', ' ')}</option>)}
          </select></label>
          <label>Next step<input name="next_step" value={fields.next_step} readOnly={busy} onChange={event => update('next_step', event.target.value)} required autoComplete="off" onKeyDown={event => { if (event.key === 'Enter') { event.preventDefault(); if (canEdit && !busy && !conflict) event.currentTarget.form?.requestSubmit(); } }} /></label>
          {task ? <label>Blocker reason<input name="blocker_reason" value={fields.blocker_reason} readOnly={busy} onChange={event => update('blocker_reason', event.target.value)} autoComplete="off" /></label> : null}
          {task ? <label>Due date<input name="due_at" value={fields.due_at} readOnly={busy} placeholder="YYYY-MM-DD" onChange={event => update('due_at', event.target.value)} autoComplete="off" /></label> : null}
          {message ? <p role="alert">{message}</p> : null}
          <button className="btn" type="submit" disabled={busy || undefined} aria-disabled={locked} title={reconnect}>{busy ? 'Saving...' : 'Save'}</button>
        </div>
      </form>
    </>
  );
}
