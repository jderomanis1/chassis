import test from 'node:test';
import assert from 'node:assert/strict';
import { editChanges, overviewNodes, priorValues, readVenture, ventureModel } from '../src/records.js';
import { place } from '../src/place.js';

test('new cards receive distinct positions and saved positions win', () => {
  const nodes = [{ id: 'a', type: 'card' }, { id: 'b', type: 'card' }, { id: 'c', type: 'venture' }];
  const edges = [{ source: 'a', target: 'b' }];
  const placed = place(nodes, edges, { b: { x: 12.3456, y: -4 } });
  const points = placed.map(node => `${node.position.x},${node.position.y}`);
  assert.equal(new Set(points).size, 3);
  assert.deepEqual(placed.find(node => node.id === 'b').position, { x: 12.35, y: -4 });
});

test('venture graph keeps only visible parent and dependency edges', () => {
  const model = ventureModel({
    initiatives: [{ id: 'initiative-one', title: 'One', status: 'planned', version: 1 }],
    tasks: { 'initiative-one': [{ id: 'task-one', title: '<img>', status: 'blocked', version: 2, blocker_reason: 'Wait' }] },
    graph: { edges: [{ from: 'task-hidden', to: 'task-one', blocking: true }, { from: 'task-one', to: 'task-outside', blocking: true }] },
  });
  assert.deepEqual(model.edges.map(edge => edge.id), ['parent-initiative-one-task-one']);
  assert.equal(model.nodes[1].data.title, '<img>');
  assert.equal(overviewNodes([{ id: 'venture-one', title: 'One', health: { color: 'red' }, counts: { tasks: 1, blocked: 1, done: 0, initiatives: 1 } }])[0].data.health, 'red');
});

test('task edits clear a blocker when leaving blocked and undo restores prior values', () => {
  const before = { title: 'Old', status: 'blocked', next_step: 'Wait', blocker_reason: 'Supplier', due_at: '2026-12-01' };
  const changes = editChanges('task', before, { ...before, status: 'in_progress', blocker_reason: 'Supplier' });
  assert.deepEqual(changes, { status: 'in_progress', blocker_reason: null });
  assert.deepEqual(priorValues(changes, before), { status: 'blocked', blocker_reason: 'Supplier' });
  assert.deepEqual(editChanges('venture', { title: 'A', status: 'planned', next_step: 'Go' },
    { title: 'B', status: 'planned', next_step: 'Go' }), { title: 'B' });
});

test('deep links accept only record ids', () => {
  assert.equal(readVenture('#/v/venture-ridgeview'), 'venture-ridgeview');
  assert.equal(readVenture('#/v/Venture'), null);
  assert.equal(readVenture('#/ask'), null);
});
