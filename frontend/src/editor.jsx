import { useEffect, useRef, useState } from 'react';

const STATUSES = ['planned', 'in_progress', 'blocked', 'done'];

export function Editor({ record, message, onClose, onSave }) {
  const titleRef = useRef(null);
  const saving = useRef(false);
  const [fields, setFields] = useState({
    title: record.title, status: record.status, next_step: record.next_step,
    blocker_reason: record.blocker_reason, due_at: record.due_at,
  });
  const task = record.kind === 'task';
  useEffect(() => { titleRef.current?.focus(); }, []);
  function update(name, value) { setFields(current => ({ ...current, [name]: value })); }
  function submit(event) {
    event.preventDefault();
    if (saving.current) return;
    saving.current = true;
    const data = new FormData(event.currentTarget);
    const next = {
      title: String(data.get('title') ?? ''),
      status: String(data.get('status') ?? ''),
      next_step: String(data.get('next_step') ?? ''),
      blocker_reason: String(data.get('blocker_reason') ?? ''),
      due_at: String(data.get('due_at') ?? ''),
    };
    Promise.resolve(onSave(next)).finally(() => { saving.current = false; });
  }
  return (
    <>
      <div className="scrim on" onClick={onClose} />
      <form className="drawer on editor-form" role="dialog" aria-label={`Edit ${record.title}`} onSubmit={submit}>
        <header><h2>Edit</h2><button type="button" className="x" aria-label="Close editor" onClick={onClose}>×</button></header>
        <div className="body">
          <label>Title<input id="edit-title" name="title" ref={titleRef} value={fields.title} onChange={event => update('title', event.target.value)} required autoComplete="off" /></label>
          <label>Status<select name="status" value={fields.status} onChange={event => update('status', event.target.value)}>
            {STATUSES.map(status => <option key={status} value={status}>{status.replaceAll('_', ' ')}</option>)}
          </select></label>
          <label>Next step<input name="next_step" value={fields.next_step} onChange={event => update('next_step', event.target.value)} required autoComplete="off" /></label>
          {task ? <label>Blocker reason<input name="blocker_reason" value={fields.blocker_reason} onChange={event => update('blocker_reason', event.target.value)} autoComplete="off" /></label> : null}
          {task ? <label>Due date<input name="due_at" value={fields.due_at} placeholder="YYYY-MM-DD" onChange={event => update('due_at', event.target.value)} autoComplete="off" /></label> : null}
          {message ? <p role="alert">{message}</p> : null}
          <button className="btn" type="submit">Save</button>
        </div>
      </form>
    </>
  );
}
