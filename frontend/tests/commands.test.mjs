import test from 'node:test';
import assert from 'node:assert/strict';
import { SUPPORTED, applyCommandView, interpret } from '../src/commands.js';

const ventures = [
  { id: 'venture-ridgeview', title: 'Ridgeview HOA' },
  { id: 'venture-acme', title: 'Acme D2C' },
  { id: 'venture-atlas', title: 'Atlas Trades' },
];

test('fit, back, show all, show only blocked, and clear all but active are exact', () => {
  assert.deepEqual(interpret('fit'), { command: 'fit' });
  assert.deepEqual(interpret('  Back '), { command: 'back' });
  assert.deepEqual(interpret('show all'), { command: 'show-all' });
  assert.deepEqual(interpret('show only blocked'), { command: 'only-blocked' });
  assert.deepEqual(interpret('clear all but active'), { command: 'only-active' });
});

test('zoom into fuzzy-matches one venture and rejects an ambiguous name', () => {
  assert.deepEqual(interpret('zoom into ridgeview', ventures),
    { command: 'zoom', id: 'venture-ridgeview', title: 'Ridgeview HOA' });
  assert.equal(interpret('zoom into a', ventures).command, 'unknown');
  assert.equal(interpret('zoom into missing', ventures).command, 'unknown');
});

test('an unknown command returns the supported list', () => {
  const result = interpret('make it pop');
  assert.equal(result.command, 'unknown');
  assert.deepEqual(result.supported, SUPPORTED);
});

test('blocked and active views keep only the matching cards and their edges', () => {
  const nodes = [
    { id: 'done', data: { kind: 'task', status: 'done' } },
    { id: 'work', data: { kind: 'task', status: 'in_progress' } },
    { id: 'stuck', data: { kind: 'task', status: 'blocked' } },
    { id: 'venture', type: 'venture', data: { kind: 'venture', counts: { tasks: 3, done: 1, blocked: 1 } } },
  ];
  const edges = [{ source: 'work', target: 'stuck' }, { source: 'done', target: 'stuck' }];
  const blocked = applyCommandView(nodes, edges, 'only-blocked');
  assert.deepEqual(blocked.nodes.map(node => node.id), ['stuck', 'venture']);
  assert.deepEqual(blocked.edges, []);
  const active = applyCommandView(nodes, edges, 'only-active');
  assert.deepEqual(active.nodes.map(node => node.id), ['work', 'stuck', 'venture']);
  assert.deepEqual(active.edges, [{ source: 'work', target: 'stuck' }]);
  assert.equal(applyCommandView(nodes, edges, 'show-all').nodes.length, 4);
});
