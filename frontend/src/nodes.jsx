import { Handle, Position } from '@xyflow/react';
import { activityLabel } from './records.js';

function watchers(data) {
  return {
    onMouseEnter: event => data.onHover(data, event.currentTarget.getBoundingClientRect()),
    onMouseLeave: () => data.onClear(),
    onFocus: event => data.onHover(data, event.currentTarget.getBoundingClientRect()),
    onBlur: () => data.onClear(),
  };
}

export function VentureNode({ data }) {
  const blocked = data.counts?.blocked || 0;
  const open = Math.max(0, (data.counts?.tasks || 0) - (data.counts?.done || 0) - blocked);
  return (
    <div role="button" tabIndex={0} aria-label={data.title} data-record-id={data.id} data-kind="venture" data-health={data.health}
      data-task-count={data.counts?.tasks || 0}
      className={`tile panel health-${data.health}${blocked ? ' has-block' : ''}`}
      onClick={() => data.onOpen(data.id)}
      onKeyDown={event => {
        if (event.key === 'Enter') { event.preventDefault(); data.onOpen(data.id); }
        if (event.key.toLowerCase() === 'h' && !event.metaKey && !event.ctrlKey && !event.altKey) {
          event.preventDefault(); data.onHide?.(data.id);
        }
      }}
      {...watchers(data)}>
      <p className="mono">{data.counts?.initiatives || 0} initiatives · {data.counts?.tasks || 0} tasks</p>
      <div className="row"><h3>{data.title}</h3>
        <span className={`blk ${blocked ? 'on' : 'off'}`}><span className="num">{blocked}</span><span className="mono">blocked</span></span></div>
      <div className="seg" aria-hidden="true">
        <i className="c-done" style={{ flex: data.counts?.done || 0 }} />
        <i className="c-blocked" style={{ flex: blocked }} />
        <i className="c-planned" style={{ flex: open || 1 }} />
      </div>
      <p className="legend"><span><i className="sw c-done" />{data.counts?.done || 0} done</span>
        <span><i className="sw c-blocked" />{blocked} blocked</span>
        <span><i className="sw c-planned" />{open} open</span></p>
      {data.writes ? <button type="button" className="btn ghost nodrag nopan" onClick={event => { event.stopPropagation(); data.onEdit(data); }}>Edit</button> : null}
    </div>
  );
}

export function CardNode({ data }) {
  return (
    <div role="button" tabIndex={0} aria-label={data.title} data-record-id={data.id} data-kind={data.kind} data-health={data.health} data-status={data.status}
      className={`node-card panel health-${data.health}${data.status === 'blocked' ? ' is-blocked' : ''}`}
      onPointerDown={event => {
        if (!matchMedia('(max-width: 375px)').matches || event.target.closest('button')) return;
        event.stopPropagation();
        data.onEdit?.(data);
      }}
      onDoubleClick={() => data.onEdit(data)}
      onKeyDown={event => {
        if (event.key === 'Enter') { event.preventDefault(); data.onEdit(data); }
        if (event.key.toLowerCase() === 'h' && !event.metaKey && !event.ctrlKey && !event.altKey) {
          event.preventDefault(); data.onHide?.(data.id);
        }
      }}
      {...watchers(data)}>
      <Handle className="nodrag" type="target" position={Position.Left} isConnectable={data.kind === 'task'} tabIndex={-1} />
      <span className={`pill s-${data.status}`}>{String(data.status || '').replaceAll('_', ' ')}</span>
      <span className="t">{data.title}</span>
      {data.writes ? <button type="button" className="btn ghost nodrag nopan" onClick={event => { event.stopPropagation(); data.onEdit(data); }}>Edit</button> : null}
      <Handle className="nodrag" type="source" position={Position.Right} isConnectable={data.kind === 'task'} tabIndex={-1} />
    </div>
  );
}

export function hoverSummary(record) {
  if (!record) return '';
  if (record.counts) return `${record.counts.initiatives} initiatives, ${record.counts.tasks} tasks, ${record.counts.blocked} blocked`;
  if (record.progress) return `${record.progress.done} of ${record.progress.total} tasks done`;
  return record.kind || '';
}

export function HoverCard({ record }) {
  return (
    <aside className="hover-slot panel" role="tooltip" aria-label={record ? record.title : 'Card details'}>
      {record ? <>
        <p className="mono">{record.kind}</p>
        <h4 title={record.title}>{record.title}</h4>
        <dl>
          <div><dt>Next</dt><dd>{record.next_milestone || record.next_step || 'None'}</dd></div>
          <div><dt>Counts</dt><dd>{hoverSummary(record)}</dd></div>
          <div><dt>Activity</dt><dd>{activityLabel(record.last_activity_at)}</dd></div>
        </dl>
      </> : <p className="mono">Hover or focus a card. Its details stay in this strip.</p>}
    </aside>
  );
}
