import { useState } from 'react';

const STATUSES = ['planned', 'in_progress', 'blocked', 'done'];

export function Editor({ record, message, onClose, onSave }) {
  const [fields, setFields] = useState({
    title: record.title, status: record.status, next_step: record.next_step,
    blocker_reason: record.blocker_reason, due_at: record.due_at,
  });
  const task = record.kind === 'task';
  function update(name, value) { setFields(current => ({ ...current, [name]: value })); }
  return (
    <>
      <div className="scrim on" onClick={onClose} />
      <form className="drawer on editor-form" role="dialog" aria-label={`Edit ${record.title}`}
        onSubmit={event => { event.preventDefault(); onSave(fields); }}>
        <header><h2>Edit</h2><button type="button" className="x" aria-label="Close editor" onClick={onClose}>×</button></header>
        <div className="body">
          <label>Title<input value={fields.title} onChange={event => update('title', event.target.value)} required /></label>
          <label>Status<select value={fields.status} onChange={event => update('status', event.target.value)}>
            {STATUSES.map(status => <option key={status} value={status}>{status.replaceAll('_', ' ')}</option>)}
          </select></label>
          <label>Next step<input value={fields.next_step} onChange={event => update('next_step', event.target.value)} required /></label>
          {task ? <label>Blocker reason<input value={fields.blocker_reason} onChange={event => update('blocker_reason', event.target.value)} /></label> : null}
          {task ? <label>Due date<input value={fields.due_at} placeholder="YYYY-MM-DD" onChange={event => update('due_at', event.target.value)} /></label> : null}
          {message ? <p role="alert">{message}</p> : null}
          <button className="btn" type="submit">Save</button>
        </div>
      </form>
    </>
  );
}
