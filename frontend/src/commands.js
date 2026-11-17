export const SUPPORTED = [
  'zoom into <venture>',
  'show only blocked',
  'show all',
  'clear all but active',
  'fit',
  'back',
];

function normalize(value) {
  return String(value || '').trim().toLowerCase().replace(/[.]/g, '').replace(/\s+/g, ' ');
}

function score(query, title) {
  const name = normalize(title);
  if (!query || !name) return 0;
  if (name === query) return 100;
  if (name.startsWith(query)) return 90;
  if (name.split(' ').some(word => word.startsWith(query))) return 80;
  if (query.length >= 4 && name.includes(query)) return 70;
  return 0;
}

export function matchVenture(query, ventures = []) {
  const ranked = ventures.map(venture => ({ ...venture, score: score(query, venture.title) }))
    .filter(venture => venture.score > 0)
    .sort((a, b) => b.score - a.score || a.title.localeCompare(b.title));
  if (!ranked.length || (ranked[1] && ranked[0].score === ranked[1].score)) return null;
  return { id: ranked[0].id, title: ranked[0].title };
}

export function interpret(command, ventures = []) {
  const text = normalize(command);
  if (text === 'fit') return { command: 'fit' };
  if (text === 'back') return { command: 'back' };
  if (text === 'show all') return { command: 'show-all' };
  if (text === 'show only blocked') return { command: 'only-blocked' };
  if (text === 'clear all but active') return { command: 'only-active' };
  const zoom = /^zoom into (.+)$/.exec(text);
  if (zoom) {
    const match = matchVenture(zoom[1], ventures);
    if (match) return { command: 'zoom', id: match.id, title: match.title };
  }
  return { command: 'unknown', supported: SUPPORTED };
}

export function isBlocked(node) {
  if ((node.data?.kind || node.type) === 'venture') return (node.data?.counts?.blocked || 0) > 0;
  return node.data?.status === 'blocked';
}

export function isActive(node) {
  if ((node.data?.kind || node.type) === 'venture') {
    const counts = node.data?.counts || {};
    return (counts.tasks || 0) - (counts.done || 0) > 0;
  }
  return node.data?.status === 'in_progress' || node.data?.status === 'blocked';
}

export function applyCommandView(nodes, edges = [], command = 'show-all') {
  const keep = command === 'only-blocked' ? isBlocked : command === 'only-active' ? isActive : null;
  if (!keep) return { nodes, edges };
  const next = nodes.filter(keep);
  const ids = new Set(next.map(node => node.id));
  return { nodes: next, edges: edges.filter(edge => ids.has(edge.source) && ids.has(edge.target)) };
}
