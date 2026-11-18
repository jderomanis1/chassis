import test from 'node:test';
import assert from 'node:assert/strict';
import { startIntro } from '../src/intro.js';

function boot(...outcomes) {
  const events = new EventTarget();
  let attempts = 0;
  const audio = {
    volume: 1,
    play() {
      const error = outcomes[attempts++];
      return error ? Promise.reject(new DOMException('', error)) : Promise.resolve();
    },
  };
  startIntro(audio, events);
  return { audio, press: type => events.dispatchEvent(new Event(type)), count: () => attempts };
}

test('successful autoplay leaves both gestures available to the UI without replay', async () => {
  const player = boot();
  await Promise.resolve();
  assert.ok(player.audio.volume > 0 && player.audio.volume <= 0.5);
  player.press('click');
  player.press('keydown');
  assert.equal(player.count(), 1);
});

for (const gesture of ['click', 'keydown']) {
  test(`autoplay denial retries synchronously on first ${gesture}, exactly once`, async () => {
    const player = boot('NotAllowedError');
    await Promise.resolve();
    player.press(gesture);
    assert.equal(player.count(), 2);
    player.press('keydown');
    player.press('click');
    await Promise.resolve();
    player.press(gesture);
    assert.equal(player.count(), 2);
  });
}

test('a non-activating key can be followed by an eligible gesture', async () => {
  const player = boot('NotAllowedError', 'NotAllowedError');
  await Promise.resolve();
  player.press('keydown');
  await Promise.resolve();
  player.press('click');
  assert.equal(player.count(), 3);
});

test('a decode failure does not set up a retry loop', async () => {
  const player = boot('NotSupportedError');
  await Promise.resolve();
  player.press('click');
  assert.equal(player.count(), 1);
});
