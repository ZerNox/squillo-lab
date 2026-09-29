// E-006 worklet stand-in: reports which network APIs its global scope has.
const APIS = ['fetch', 'XMLHttpRequest', 'WebSocket', 'EventSource', 'importScripts'];
class Probe extends AudioWorkletProcessor {
  constructor() { super(); const has = {}; for (const a of APIS) has[a] = typeof globalThis[a];
    this.port.postMessage({ context: 'worklet', has }); }
  process() { return false; }
}
registerProcessor('e006-probe', Probe);
