import dagre from '@dagrejs/dagre';

const SIZE = { venture: { width: 420, height: 220 }, card: { width: 260, height: 120 } };

export function roundPoint(point) {
  const x = Math.round((point?.x || 0) * 100) / 100;
  const y = Math.round((point?.y || 0) * 100) / 100;
  return {
    x: Number.isFinite(x) ? Math.max(-1000000, Math.min(1000000, x)) : 0,
    y: Number.isFinite(y) ? Math.max(-1000000, Math.min(1000000, y)) : 0,
  };
}

export function roundViewport(viewport = {}) {
  const point = roundPoint(viewport);
  const zoom = Math.round((viewport.zoom ?? 1) * 100) / 100;
  return { ...point, zoom: Number.isFinite(zoom) ? Math.min(4, Math.max(0.1, zoom)) : 1 };
}

function grid(nodes) {
  const columns = nodes.some(node => node.type === 'venture') ? 3 : 4;
  return nodes.map((node, index) => {
    const size = SIZE[node.type] || SIZE.card;
    return roundPoint({
      x: (index % columns) * (size.width + 48),
      y: Math.floor(index / columns) * (size.height + 40),
    });
  });
}

export function place(nodes, edges = [], saved = {}) {
  const pending = nodes.filter(node => !saved[node.id]);
  const positions = {};
  if (pending.length) {
    const graph = new dagre.graphlib.Graph();
    graph.setDefaultEdgeLabel(() => ({}));
    graph.setGraph({ rankdir: 'LR', nodesep: 48, ranksep: 140, marginx: 24, marginy: 24 });
    const pendingIds = new Set(pending.map(node => node.id));
    const linked = edges.some(edge => pendingIds.has(edge.source) && pendingIds.has(edge.target));
    if (!linked) grid(pending).forEach((point, index) => { positions[pending[index].id] = point; });
    else {
      for (const node of pending) graph.setNode(node.id, { ...(SIZE[node.type] || SIZE.card) });
      for (const edge of edges) {
        if (pendingIds.has(edge.source) && pendingIds.has(edge.target)) graph.setEdge(edge.source, edge.target);
      }
      dagre.layout(graph);
      pending.forEach(node => {
        const size = SIZE[node.type] || SIZE.card;
        const laid = graph.node(node.id);
        positions[node.id] = roundPoint({ x: laid.x - size.width / 2, y: laid.y - size.height / 2 });
      });
      const signatures = new Set(Object.values(positions).map(point => `${point.x},${point.y}`));
      if (signatures.size !== pending.length) grid(pending).forEach((point, index) => { positions[pending[index].id] = point; });
    }
  }
  return nodes.map(node => ({ ...node, position: saved[node.id] ? roundPoint(saved[node.id]) : positions[node.id] }));
}
