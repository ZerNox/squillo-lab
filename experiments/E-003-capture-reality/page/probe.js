// E-003 probe: squillo's capture path (ADR 0002 request and readback,
// ADR 0006 worklet-to-worker transport), driven by run.mjs.
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function b64(buf) {
  const u = new Uint8Array(buf); let s = '';
  for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode.apply(null, u.subarray(i, i + 0x8000));
  return btoa(s);
}
const RAW = { echoCancellation: false, noiseSuppression: false,
              autoGainControl: false, channelCount: 1 };

async function readback(which) {
  const out = { supported: navigator.mediaDevices.getSupportedConstraints() };
  const req = which === 'raw' ? RAW : true;
  const s = await navigator.mediaDevices.getUserMedia({ audio: req });
  const t = s.getAudioTracks()[0];
  out.label = t.label;
  out.settings = t.getSettings();
  out.constraints = t.getConstraints();
  out.capabilities = t.getCapabilities ? t.getCapabilities() : null;
  // mono as an exact constraint, after the ideal one above
  if (which === 'raw') {
    try { await t.applyConstraints({ ...RAW, channelCount: { exact: 1 } }); out.afterExactMono = t.getSettings(); }
    catch (e) { out.exactMonoError = `${e.name}: ${e.message}`; }
    t.stop();
    try {
      const s2 = await navigator.mediaDevices.getUserMedia({ audio: { ...RAW, channelCount: { exact: 1 } } });
      out.exactMonoRequest = s2.getAudioTracks()[0].getSettings();
      s2.getAudioTracks()[0].stop();
    } catch (e) { out.exactMonoRequestError = `${e.name}: ${e.message}`; }
  }
  // apply the raw request after the fact, as a second path
  if (which === 'default') {
    try { await t.applyConstraints(RAW); out.afterApply = t.getSettings(); }
    catch (e) { out.applyError = String(e); }
  }
  t.stop();
  return out;
}

async function capture(cfg) {
  const out = { cfg, ua: navigator.userAgent };
  let stream, srcCtx;
  if (cfg.path === 'mic') {
    stream = await navigator.mediaDevices.getUserMedia({ audio: RAW });
  } else {
    srcCtx = new AudioContext({ sampleRate: cfg.srcRate });
    out.srcCtxRate = srcCtx.sampleRate;
    const data = new Float32Array(await (await fetch(`/data/probe${cfg.srcRate}.f32`)).arrayBuffer());
    const ab = srcCtx.createBuffer(1, data.length, cfg.srcRate);
    ab.copyToChannel(data, 0);
    const src = srcCtx.createBufferSource(); src.buffer = ab; src.loop = true;
    const dest = srcCtx.createMediaStreamDestination();
    dest.channelCount = 1;
    src.connect(dest); src.start();
    await srcCtx.resume();
    stream = dest.stream;
  }
  const track = stream.getAudioTracks()[0];
  out.settings = track.getSettings();
  let ctx;
  try { ctx = new AudioContext({ sampleRate: cfg.ctxRate }); }
  catch (e) { out.ctxError = String(e); return out; }
  out.ctxRate = ctx.sampleRate;
  out.baseLatency = ctx.baseLatency;
  await ctx.audioWorklet.addModule('/page/tap.js');
  let node;
  try { node = ctx.createMediaStreamSource(stream); }
  catch (e) { out.sourceError = String(e); return out; }
  const tap = new AudioWorkletNode(ctx, 'tap', { numberOfInputs: 1,
    numberOfOutputs: 1, outputChannelCount: [1] });
  const worker = new Worker('/page/engine.js');
  const ch = new MessageChannel();
  const maxBlocks = Math.ceil((cfg.seconds + 2) * ctx.sampleRate / 128);
  const ready = new Promise((r) => { worker.onmessage = (e) => r(e.data); });
  worker.postMessage({ port: ch.port1, loadMs: cfg.loadMs, maxBlocks }, [ch.port1]);
  await ready;
  tap.port.postMessage({ port: ch.port2 }, [ch.port2]);
  const mute = ctx.createGain(); mute.gain.value = 0;
  node.connect(tap).connect(mute).connect(ctx.destination);
  await ctx.resume();
  const t0 = performance.now(), c0 = ctx.currentTime;
  await sleep(cfg.seconds * 1000);
  const t1 = performance.now(), c1 = ctx.currentTime;
  out.clock = { wallMs: t1 - t0, ctxS: c1 - c0 };
  const tapDone = new Promise((r) => { tap.port.onmessage = (e) => r(e.data); });
  tap.port.postMessage({ stop: true });
  out.tap = await tapDone;
  const result = new Promise((r) => { worker.onmessage = (e) => r(e.data); });
  const drainStart = performance.now();
  worker.postMessage({ stopAt: out.tap.lastSeq });
  const res = await Promise.race([result, sleep(120000).then(() => null)]);
  out.drainMs = performance.now() - drainStart;
  track.stop(); await ctx.close(); if (srcCtx) await srcCtx.close();
  worker.terminate();
  if (!res) { out.workerTimeout = true; return out; }
  out.worker = { n: res.n, lost: res.lost, reordered: res.reordered,
                 dup: res.dup, empty: res.empty, timerRes: res.timerRes };
  out.samples = b64(res.samples);
  out.seqs = Array.from(res.seqs); out.frames = Array.from(res.frames);
  out.recv = Array.from(res.recv); out.done = Array.from(res.done);
  return out;
}
window.e003 = { readback, capture };
