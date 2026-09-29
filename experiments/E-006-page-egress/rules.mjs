// E-006 rules, written and committed before the full run (squillo S15, L-047).
// run.mjs and analyze.mjs refuse to run on an uncommitted edit of this file or of themselves.

// The policy under test: squillo ADR 0010 requirement 2 (no connect-src, no
// third-party script or style) with ADR 0006's 'wasm-unsafe-eval', and the
// worker and worklet the page needs (ADR 0006: one engine worker, the capture
// AudioWorklet). default-src 'none' makes every directive not named 'none'.
export const POLICY = [
  "default-src 'none'",
  "script-src 'self' 'wasm-unsafe-eval'",
  "style-src 'self'",
  "img-src 'self'",
  "worker-src 'self' blob:",
  "connect-src 'none'",
  "object-src 'none'",
  "base-uri 'none'",
  "form-action 'none'",
].join('; ');
// The must-fail policy for WebAssembly: the same without 'wasm-unsafe-eval'.
export const POLICY_NOWASM = POLICY.replace(" 'wasm-unsafe-eval'", '');

// How the policy reaches the page. 'none' is the reference every probe must
// reach the logger under (K1's must-pass side for the probes themselves).
export const CONDITIONS = {
  none: { meta: null, header: null },
  meta: { meta: POLICY, header: null },            // a static host that sets no headers
  header: { meta: null, header: POLICY },          // a host that sends the policy on every response
  'meta-nowasm': { meta: POLICY_NOWASM, header: null },
  'header-nowasm': { meta: null, header: POLICY_NOWASM },
};
// How the page starts its engine worker: from its own URL, or from a blob:
// URL made from source text built into the page's script.
export const WORKER_MODES = ['url', 'blob'];
export const BROWSERS = ['chrome', 'firefox'];
export const REPS = 3;

// Every probe aims at the logger, a second origin (another port on
// 127.0.0.1), with a path naming the run, context and probe.
export const DOC_PROBES = ['fetch', 'xhr', 'websocket', 'eventsource', 'beacon', 'img', 'script',
  'style', 'prefetch', 'audio', 'iframe', 'webrtc'];
export const WORKER_PROBES = ['fetch', 'xhr', 'websocket', 'eventsource', 'importscripts'];
// Fired last, after the page's outcomes are read: the page navigating itself.
export const NAV_PROBE = 'navigate';
export const WORKLET_APIS = ['fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'importScripts'];

// Settle times, ms: after the probes fire, before the logger is read.
export const SETTLE_MS = 2000;
export const ICE_WAIT_MS = 3000;   // webrtc: until ICE gathering completes, or this long
export const NAV_SETTLE_MS = 1500;

// Checks.
// K0 (the logger check, checked): a request the runner itself sends to the
//   logger before the page loads must be seen (must pass); a path no one
//   requests must not be (must fail, differing in the input the check reads).
//   The UDP port, WebRTC's measure, must have received nothing before the
//   page loads (its must-fail input: no probe fired); 'none' is its must-pass.
// K1 (probe judged): a probe is judged in a browser only if it reached the
//   logger in every rep of 'none' for that browser and worker mode; one that
//   did not is reported "not judged", never counted as blocked.
// K2 (run complete): every run returns an outcome for every probe and the
//   worklet's API list, with no harness error.
// Recorded, not asserted: whether the reps agree (reported per cell);
// the page's own-origin requests (listed); securitypolicyviolation events.

// Hypotheses, written before the run (not checks; the result says which held).
export const HYPOTHESES = {
  H1: "Under 'meta' and 'header', no judged document probe but webrtc reaches the logger, in both browsers",
  H2: "Under 'meta', a URL-loaded worker's judged probes reach the logger (it runs under no policy) and a blob worker's do not; under 'header', neither's do",
  H3: 'Where judged, webrtc reaches the logger under every condition: the policy does not govern it',
  H4: "WebAssembly instantiates under 'meta' and 'header' in the document and in a policy-bound worker, and is refused under '*-nowasm' there",
  H5: "Navigation of the page itself to the logger reaches it under every condition",
};
