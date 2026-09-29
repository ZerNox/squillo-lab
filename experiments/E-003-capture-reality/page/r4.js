// E-003 round 4 (squillo iteration 53, F-042): round 1's mic path (probe.js
// capture(), raw request, 48 kHz context) with engine4.js, which sends the
// page one JSON-text message per 8 ms frame. The page records each frame
// message's arrival and then burns cfg.pageLoadMs, standing in for drawing.
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const now = () => performance.timeOrigin + performance.now();
const RAW = { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 };
async function clockPings(worker, k) {
  // K0: the page's and the worker's clocks, compared by round trips
  const out = [];
  for (let i = 0; i < k; i++) {
    const tA = now(), tArel = performance.now();
    const r = await new Promise((res) => { worker.onmessage = (e) => { if (e.data.pong === i) res(e.data); }; worker.postMessage({ ping: i }); });
    out.push({ tA, tB: now(), tW: r.t, tArel, tBrel: performance.now(), tWrel: r.tRel });
    await sleep(5);
  }
  return out;
}
function timerRes() {
  let res = Infinity, a = performance.now();
  for (let i = 0; i < 200000; i++) { const b = performance.now(); if (b > a) { res = Math.min(res, b - a); a = b; } }
  return res;
}
async function capture(cfg) {
  const out = { cfg, ua: navigator.userAgent, pageTimerRes: timerRes() };
  const stream = await navigator.mediaDevices.getUserMedia({ audio: RAW });
  const track = stream.getAudioTracks()[0];
  out.settings = track.getSettings();
  const ctx = new AudioContext({ sampleRate: 48000 });
  out.ctxRate = ctx.sampleRate;
  await ctx.audioWorklet.addModule('/page/tap.js');
  const node = ctx.createMediaStreamSource(stream);
  const tap = new AudioWorkletNode(ctx, 'tap', { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1] });
  const worker = new Worker('/page/engine4.js');
  out.pings = await clockPings(worker, 20);
  const ch = new MessageChannel();
  const maxBlocks = Math.ceil((cfg.seconds + 2) * ctx.sampleRate / 128);
  const fRecv = [], fSeq = [];
  let bad = 0, other = null;
  const ready = new Promise((r) => { worker.onmessage = (e) => r(e.data); });
  worker.postMessage({ port: ch.port1, loadMs: cfg.workerLoadMs, maxBlocks }, [ch.port1]);
  await ready;
  let resolveDone;
  const doneP = new Promise((r) => { resolveDone = r; });
  worker.onmessage = (e) => {
    if (typeof e.data === 'string') {
      const t = now();
      let m; try { m = JSON.parse(e.data); } catch (_) { bad++; return; }
      fRecv.push(t); fSeq.push(m.frame);
      if (cfg.pageLoadMs > 0) { const until = performance.now() + cfg.pageLoadMs; let x = 0; while (performance.now() < until) x++; }
    } else if (e.data.done) resolveDone(e.data);
    else other = e.data;
  };
  tap.port.postMessage({ port: ch.port2 }, [ch.port2]);
  const mute = ctx.createGain(); mute.gain.value = 0;
  node.connect(tap).connect(mute).connect(ctx.destination);
  await ctx.resume();
  await sleep(cfg.seconds * 1000);
  const tapDone = new Promise((r) => { tap.port.onmessage = (e) => r(e.data); });
  tap.port.postMessage({ stop: true });
  out.tap = await tapDone;
  const t0 = now();
  worker.postMessage({ stopAt: out.tap.lastSeq });
  const res = await Promise.race([doneP, sleep(120000).then(() => null)]);
  out.drainMs = now() - t0;
  track.stop(); await ctx.close(); worker.terminate();
  if (!res) { out.workerTimeout = true; return out; }
  out.worker = { n: res.n, lost: res.lost, reordered: res.reordered, dup: res.dup, nf: res.nf };
  out.blockSeqs = Array.from(res.seqs);
  out.fBlockRecv = Array.from(res.fBlockRecv); out.fPost = Array.from(res.fPost);
  out.fRecv = fRecv; out.fSeq = fSeq; out.badJson = bad; out.other = other;
  return out;
}
window.e003r4 = { capture };
