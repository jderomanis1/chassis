export const POLL_MS = 1000;

export function freshnessWorstCaseMs(pollMs = POLL_MS, roundTripMs = 1000) {
  return pollMs + roundTripMs;
}
