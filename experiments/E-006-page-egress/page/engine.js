// E-006 engine worker stand-in: fires the worker probes at the logger and
// tries WebAssembly, then reports each outcome. Not product code.
const WASM = new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0]); // the empty module
function settle(p, ms) { return Promise.race([p, new Promise((r) => setTimeout(() => r('pending'), ms))]); }
async function probe(name, url) {
  try {
    switch (name) {
      case 'fetch': await fetch(url, { mode: 'no-cors' }); return 'ok';
      case 'xhr': return await new Promise((r) => { const x = new XMLHttpRequest(); x.open('GET', url);
        x.onload = () => r('ok'); x.onerror = () => r('error'); try { x.send(); } catch (e) { r('throw:' + e.name); } });
      case 'websocket': return await settle(new Promise((r) => { const w = new WebSocket(url.replace('http', 'ws'));
        w.onopen = () => r('open'); w.onerror = () => r('error'); }), 1500);
      case 'eventsource': return await settle(new Promise((r) => { const s = new EventSource(url);
        s.onopen = () => { s.close(); r('open'); }; s.onerror = () => { s.close(); r('error'); }; }), 1500);
      case 'importscripts': importScripts(url); return 'ok';
    }
  } catch (e) { return 'throw:' + e.name; }
}
self.onmessage = async (ev) => {
  const { logger, run, probes } = ev.data;
  const out = { context: 'worker', probes: {}, violations: [] };
  self.addEventListener('securitypolicyviolation', (e) => out.violations.push([e.violatedDirective, e.blockedURI]));
  try { await WebAssembly.instantiate(WASM); out.wasm = 'ok'; } catch (e) { out.wasm = 'throw:' + e.name; }
  await Promise.all(probes.map(async (p) => { out.probes[p] = await probe(p, `${logger}/${run}/worker/${p}`); }));
  self.postMessage(out);
};
