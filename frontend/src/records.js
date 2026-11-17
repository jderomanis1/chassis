const HEALTH = new Set(['green', 'yellow', 'red', 'unknown']);

export function text(value) {
  return value == null ? '' : String(value);
}

export function healthOf(record) {
  return HEALTH.has(record?.health?.color) ? record.health.color : 'unknown';
}

export function activityLabel(value) {
  if (!value) return 'No committed activity';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'No committed activity';
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Phoenix', dateStyle: 'medium', timeStyle: 'short',
  }).format(date);
}

export function cardFrom(record, kind) {
  return {
    id: record.id, kind, title: text(record.title), health: healthOf(record),
    status: record.status || 'planned', version: record.version, owner: text(record.owner),
    next_step: text(record.next_step), blocker_reason: text(record.blocker_reason),
    due_at: text(record.due_at), next_milestone: text(record.next_milestone),
    milestone_due_at: text(record.milestone_due_at), last_activity_at: text(record.last_activity_at),
    counts: record.counts || null, progress: record.progress || null,
    depends_on: Array.isArray(record.depends_on) ? record.depends_on.map(String) : [],
  };
}

export function overviewNodes(ventures) {
  return (ventures || []).map(venture => ({ id: venture.id, type: 'venture', data: cardFrom(venture, 'venture') }));
}

export function ventureModel(bundle) {
  const nodes = [], edges = [];
  for (const initiative of bundle.initiatives || []) {
    nodes.push({ id: initiative.id, type: 'card', data: cardFrom(initiative, 'initiative') });
    for (const task of bundle.tasks?.[initiative.id] || []) {
      nodes.push({ id: task.id, type: 'card', data: cardFrom(task, 'task') });
      edges.push({ id: `parent-${initiative.id}-${task.id}`, source: initiative.id, target: task.id,
        data: { kind: 'parent', blocking: false } });
    }
  }
  const visible = new Set(nodes.map(node => node.id));
  for (const edge of bundle.graph?.edges || []) {
    if (!visible.has(edge.from) || !visible.has(edge.to)) continue;
    const blocking = Boolean(edge.blocking);
    edges.push({ id: `depends-${edge.from}-${edge.to}`, source: edge.from, target: edge.to,
      label: blocking ? 'BLOCKING' : undefined, data: { kind: 'depends', blocking } });
  }
  return { nodes, edges };
}

export function editChanges(kind, before, after) {
  const changes = {};
  for (const field of ['title', 'status', 'next_step']) {
    if (after[field] !== before[field]) changes[field] = after[field];
  }
  if (kind === 'task') {
    const due = after.due_at || null;
    if (due !== (before.due_at || null)) changes.due_at = due;
    const reason = after.status === 'blocked' ? after.blocker_reason : null;
    const previous = before.status === 'blocked' ? (before.blocker_reason || null) : null;
    if (reason !== previous) changes.blocker_reason = reason;
  }
  return changes;
}

export function priorValues(changes, before) {
  const prior = {};
  for (const field of Object.keys(changes)) {
    const value = before[field];
    if (Array.isArray(value)) prior[field] = [...value];
    else prior[field] = value == null || value === '' ? null : value;
  }
  return prior;
}

export function linkChange(source, target, visibleIds) {
  if (!source || !target || source.id === target.id) return { ok: false, message: 'Choose two different tasks.' };
  if (source.kind !== 'task' || target.kind !== 'task') return { ok: false, message: 'Only tasks can be linked.' };
  const allowed = visibleIds ? new Set(visibleIds) : null;
  if (allowed && (!allowed.has(source.id) || !allowed.has(target.id))) {
    return { ok: false, message: 'invalid dependency' };
  }
  const current = (target.depends_on || []).filter(id => !allowed || allowed.has(id));
  if (current.includes(source.id)) return { ok: false, message: 'Those tasks are already linked.' };
  return { ok: true, id: target.id, version: target.version, changes: { depends_on: [...current, source.id] } };
}

export function presentGraph(nodes, edges = [], hidden = []) {
  const skip = new Set(hidden);
  const kept = nodes.filter(node => !skip.has(node.id));
  const ids = new Set(kept.map(node => node.id));
  return { nodes: kept, edges: edges.filter(edge => ids.has(edge.source) && ids.has(edge.target)) };
}

export function flickedOff(point, pane, margin = 2) {
  if (!point || !pane) return false;
  return point.x <= pane.x + margin || point.y <= pane.y + margin
    || point.x >= pane.x + pane.width - margin || point.y >= pane.y + pane.height - margin;
}

export function nextUndoStack(stack, undoneId, version) {
  const next = stack.slice(0, -1);
  for (let index = next.length - 1; index >= 0; index -= 1) {
    if (next[index].id === undoneId) {
      return next.map((item, itemIndex) => itemIndex === index ? { ...item, version } : item);
    }
  }
  return next;
}

export function readVenture(hash = '') {
  const match = /^#\/v\/([a-z][a-z0-9]*(?:-[a-z0-9]+)*)$/.exec(hash);
  return match ? match[1] : null;
}
