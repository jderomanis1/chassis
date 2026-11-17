import { useEffect, useRef } from 'react';
import { Background, Controls, MiniMap, ReactFlow, ReactFlowProvider, useEdgesState, useNodesInitialized, useNodesState, useReactFlow } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CardNode, VentureNode } from './nodes.jsx';
import { place, roundViewport } from './place.js';

const nodeTypes = { venture: VentureNode, card: CardNode };

function styleEdge(edge) {
  const blocking = Boolean(edge.data?.blocking);
  const parent = edge.data?.kind === 'parent';
  return { ...edge, type: 'smoothstep',
    style: { stroke: blocking ? 'var(--red)' : parent ? 'var(--slate)' : 'var(--cyan)', strokeWidth: blocking ? 2.5 : 2,
      strokeDasharray: parent ? undefined : '6 6' },
    labelStyle: { fill: 'var(--red)', fontWeight: 600 },
    labelBgStyle: { fill: 'var(--panel)', fillOpacity: 0.92 }, labelBgPadding: [4, 2], labelBgBorderRadius: 4 };
}

function bind(node, actions) {
  return { ...node, data: { ...node.data, writes: actions.current.writes,
    onOpen: id => actions.current.onOpen(id),
    onEdit: record => actions.current.writes && actions.current.onEdit(record),
    onHover: (record, rect) => actions.current.onHover(record, rect),
    onClear: () => actions.current.onClear() } };
}

function Surface({ model, layout, writes, onLayout, onOpen, onEdit, onHover, onClear }) {
  const flow = useReactFlow();
  const actions = useRef({});
  actions.current = { onOpen, onEdit, onHover, onClear, writes };
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const measured = useNodesInitialized();
  const framed = useRef(false);
  useEffect(() => {
    const next = place(model.nodes, model.edges, layout.positions || {}).map(node => bind(node, actions));
    setNodes(current => {
      const at = Object.fromEntries(current.map(node => [node.id, node.position]));
      return next.map(node => at[node.id] ? { ...node, position: at[node.id] } : node);
    });
    setEdges(model.edges.map(styleEdge));
  }, [model, layout.positions, writes, setNodes, setEdges]);
  useEffect(() => {
    if (!measured || !nodes.length || framed.current) return undefined;
    let cancel = false;
    document.fonts.ready.then(() => {
      if (cancel || framed.current) return;
      framed.current = true;
      const saved = model.nodes.some(node => layout.positions?.[node.id]);
      const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (saved && layout.viewport) flow.setViewport(roundViewport(layout.viewport), { duration: 0 });
      else flow.fitView({ duration: reduce ? 0 : 350, padding: 0.18, maxZoom: 0.9 });
    });
    return () => { cancel = true; };
  }, [measured, nodes.length, flow, model.nodes, layout.positions, layout.viewport]);
  function publish(nextNodes, viewport) {
    if (!nextNodes.length) return;
    onLayout(nextNodes.map(node => ({ id: node.id, position: node.position })), roundViewport(viewport || flow.getViewport()));
  }
  return (
    <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} nodeTypes={nodeTypes}
      onNodeDragStop={(_, __, next) => publish(next)} onMoveEnd={(_, viewport) => publish(nodes, viewport)}
      minZoom={0.1} maxZoom={4} nodesConnectable={false} panOnScroll fitView={false} colorMode={document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'}
      proOptions={{ hideAttribution: false }}>
      <Background gap={48} color="var(--line)" />
      <Controls showInteractive={false} />
      <MiniMap pannable zoomable />
    </ReactFlow>
  );
}

export function Canvas(props) {
  return (
    <div className="flow-wrap" data-testid="command-canvas">
      <ReactFlowProvider>
        <Surface key={props.model.view} {...props} onHover={props.onHover} onClear={props.onClear} />
      </ReactFlowProvider>
    </div>
  );
}
