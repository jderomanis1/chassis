import { useEffect, useState } from 'react';
import { SUPPORTED, interpret } from './commands.js';

export function CommandBar({ open, ventures, onClose, onRun }) {
  const [value, setValue] = useState('');
  const [help, setHelp] = useState('');
  useEffect(() => { if (open) { setValue(''); setHelp(''); } }, [open]);
  if (!open) return null;
  function submit(event) {
    event.preventDefault();
    const intent = interpret(value, ventures);
    if (intent.command === 'unknown') setHelp(intent.supported.join(', '));
    else { onRun(intent); onClose(); }
  }
  return (
    <>
      <div className="scrim on" onClick={onClose} />
      <form className="command panel" role="dialog" aria-label="Command" onSubmit={submit}>
        <label className="sr" htmlFor="command-input">Command</label>
        <input id="command-input" autoFocus value={value} onChange={event => setValue(event.target.value)}
          placeholder="zoom into Ridgeview HOA" />
        <p role="status">{help ? `Supported: ${help}` : SUPPORTED.join(', ')}</p>
        <button className="btn" type="submit">Run</button>
      </form>
    </>
  );
}
