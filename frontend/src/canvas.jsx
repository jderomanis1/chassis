import { useEffect, useRef } from 'react';
import { Background, Controls, MiniMap, ReactFlow, ReactFlowProvider, useEdgesState, useNodesInitialized, useNodesState, useReactFlow } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { CardNode, VentureNode } from './nodes.jsx';
import { place, roundViewport } from './place.js';
import { flickedOff } from './records.js';

const nodeTypes = { venture: VentureNode, card: CardNode };
const FIT_PADDING = { top: '24px', left: '24px', right: '210px', bottom: '150px' };

function rememberZoom(zoom) {
  document.querySelector('[data-testid="command-canvas"]')?.style.setProperty('--canvas-zoom', String(zoom || 1));
}

function fit(flow) {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const phone = matchMedia('(max-width: 375px)').matches;
  const padding = phone ? { top: '12px', left: '12px', right: '12px', bottom: '12px' } : FIT_PADDING;
  flow.fitView({ duration: reduce ? 0 : 250, padding, minZoom: phone ? 0.5 : 0.1, maxZoom: phone ? 1 : 0.9 });
  rememberZoom(flow.getViewport().zoom);
}

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
  return { ...node, data: { ...node.data, writes: actions.current.writes, canEdit: actions.current.canEdit,
    onOpen: id => actions.current.onOpen(id),
    onHide: id => actions.current.onHide?.(id),
    onEdit: record => actions.current.canEdit && actions.current.onEdit(record),
    onHover: (record, rect) => actions.current.onHover(record, rect),
    onClear: () => actions.current.onClear() } };
}

function Surface({ model, layout, writes, canEdit, onLayout, onOpen, onEdit, onHover, onClear, onHide, onLink, fitSignal }) {
  const flow = useReactFlow();
  const actions = useRef({});
  actions.current = { onOpen, onEdit, onHover, onClear, onHide, writes, canEdit };
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const measured = useNodesInitialized();
  const framed = useRef(false);
  const fitted = useRef(0);
  useEffect(() => {
    const next = place(model.nodes, model.edges, layout.positions || {}).map(node => bind(node, actions));
    setNodes(current => {
      const at = Object.fromEntries(current.map(node => [node.id, node]));
      // keep the measured size so React Flow does not hide the node (visibility:hidden) until it re-measures
      return next.map(node => at[node.id] ? { ...node, position: at[node.id].position, measured: at[node.id].measured } : node);
    });
    setEdges(model.edges.map(styleEdge));
  }, [model, layout.positions, writes, canEdit, setNodes, setEdges]);
  useEffect(() => {
    if (!measured || !nodes.length || framed.current) return undefined;
    let cancel = false;
    document.fonts.ready.then(() => {
      if (cancel || framed.current) return;
      framed.current = true;
      fit(flow);
    });
    return () => { cancel = true; };
  }, [measured, nodes.length, flow]);
  useEffect(() => {
    if (!fitSignal || fitted.current === fitSignal || nodes.length !== model.nodes.length) return undefined;
    fitted.current = fitSignal;
    const frame = requestAnimationFrame(() => fit(flow));
    return () => cancelAnimationFrame(frame);
  }, [fitSignal, nodes.length, model.nodes.length, flow]);
  useEffect(() => {
    const onResize = () => { if (framed.current) fit(flow); };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [flow]);
  useEffect(() => {
    const pane = document.querySelector('[data-testid="command-canvas"]');
    if (!pane) return undefined;
    const quiet = () => pane.querySelectorAll('.react-flow__attribution, .react-flow__attribution a').forEach(node => { node.tabIndex = -1; });
    quiet();
    const observer = new MutationObserver(quiet);
    observer.observe(pane, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, []);
  function publish(nextNodes, viewport) {
    if (!nextNodes.length) return;
    onLayout(nextNodes.map(node => ({ id: node.id, position: node.position })), roundViewport(viewport || flow.getViewport()));
  }
  function dropped(event, node, next) {
    const pane = document.querySelector('.react-flow')?.getBoundingClientRect();
    const point = { x: event.clientX, y: event.clientY };
    if (pane && flickedOff(point, pane)) onHide?.(node.id);
    else publish(next);
  }
  return (
    <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} nodeTypes={nodeTypes}
      onNodeDragStop={(event, node, next) => dropped(event, node, next)}
      onMove={(_, viewport) => rememberZoom(viewport.zoom)}
      onMoveEnd={(_, viewport) => { rememberZoom(viewport.zoom); publish(nodes, viewport); }}
      minZoom={matchMedia('(max-width: 375px)').matches ? 0.5 : 0.1} maxZoom={4}
      nodesDraggable={!matchMedia('(max-width: 375px)').matches} nodesConnectable panOnScroll fitView={false}
      nodesFocusable={false} edgesFocusable={false} tabIndex={-1}
      onConnect={connection => onLink?.(connection)}
      colorMode={document.documentElement.dataset.theme === 'light' ? 'light' : 'dark'}
      proOptions={{ hideAttribution: false }}>
      <Background gap={48} color="var(--line)" />
      <Controls showInteractive={false} />
      <MiniMap pannable zoomable style={{ width: 180, height: 120 }} position="bottom-right" />
    </ReactFlow>
  );
}

export function Canvas(props) {
  return (
    <div className="flow-wrap" data-testid="command-canvas" data-task-count={props.model.nodes.filter(node => node.data?.kind === 'task').length}>
      <ReactFlowProvider>
        <Surface key={props.model.view} {...props} onHover={props.onHover} onClear={props.onClear} />
      </ReactFlowProvider>
    </div>
  );
}
