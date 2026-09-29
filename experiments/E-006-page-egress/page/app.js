// E-006 page: fires the document probes at the logger, starts the engine
// worker (from its URL or a blob), the worklet, and gathers outcomes.
// ENGINE_SRC is prepended by run.mjs as the worker's source text.
const WASM = new Uint8Array([0, 97, 115, 109, 1, 0, 0, 0]);
const q = new URLSearchParams(location.search);
const LOGGER = q.get('logger'), RUN = q.get('run'), MODE = q.get('mode');
const STUN = q.get('stun').split(',');
const violations = [];
document.addEventListener('securitypolicyviolation', (e) => violations.push([e.violatedDirective, e.blockedURI]));
function settle(p, ms) { return Promise.race([p, new Promise((r) => setTimeout(() => r('pending'), ms))]); }
function el(tag, attrs) { return new Promise((r) => { const e = document.createElement(tag);
  e.onload = () => r('load'); e.onerror = () => r('error'); Object.assign(e, attrs); document.body.appendChild(e);
  setTimeout(() => r('pending'), 1500); }); }
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
      case 'beacon': return String(navigator.sendBeacon(url, 'x'));
      case 'img': return await el('img', { src: url });
      case 'script': return await el('script', { src: url });
      case 'style': return await el('link', { rel: 'stylesheet', href: url });
      case 'prefetch': return await el('link', { rel: 'prefetch', href: url });
      case 'audio': return await settle(new Promise((r) => { const a = new Audio(); a.onerror = () => r('error');
        a.oncanplay = () => r('canplay'); a.src = url; a.load(); }), 1500);
      case 'iframe': return await el('iframe', { src: url });
      case 'webrtc': {
        const pc = new RTCPeerConnection({ iceServers: STUN.map((h) => ({ urls: `stun:${h}` })) });
        pc.createDataChannel('x');
        const done = new Promise((r) => { pc.onicegatheringstatechange = () => { if (pc.iceGatheringState === 'complete') r('complete'); }; });
        await pc.setLocalDescription(await pc.createOffer());
        const s = await settle(done, Number(q.get('ice')));
        pc.close(); return 'gathering:' + s;
      }
    }
  } catch (e) { return 'throw:' + e.name; }
}
async function worker(probes) {
  let w;
  try {
    w = MODE === 'blob' ? new Worker(URL.createObjectURL(new Blob([ENGINE_SRC], { type: 'text/javascript' })))
      : new Worker('/engine.js');
  } catch (e) { return { error: 'throw:' + e.name }; }
  return settle(new Promise((r) => { w.onmessage = (e) => r(e.data); w.onerror = (e) => r({ error: 'error:' + e.message });
    w.postMessage({ logger: LOGGER, run: RUN, probes }); }), 8000);
}
async function worklet() {
  try {
    const ctx = new AudioContext();
    await ctx.audioWorklet.addModule('/worklet.js');
    const n = new AudioWorkletNode(ctx, 'e006-probe');
    const r = await settle(new Promise((res) => { n.port.onmessage = (e) => res(e.data); }), 3000);
    ctx.close(); return r;
  } catch (e) { return { error: 'throw:' + e.name + ':' + e.message }; }
}
window.e006 = async (docProbes, workerProbes) => {
  const out = { mode: MODE, doc: {}, violations };
  try { await WebAssembly.instantiate(WASM); out.wasm = 'ok'; } catch (e) { out.wasm = 'throw:' + e.name; }
  await Promise.all(docProbes.map(async (p) => { out.doc[p] = await probe(p, `${LOGGER}/${RUN}/doc/${p}`); }));
  out.worker = await worker(workerProbes);
  out.worklet = await worklet();
  return out;
};
window.e006nav = () => { location.href = `${LOGGER}/${RUN}/doc/navigate`; };
