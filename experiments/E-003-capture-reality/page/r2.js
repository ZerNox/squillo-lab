// E-003 round 2 (squillo iteration 47): round 1's capture path (probe.js
// capture(), mic path only, load 0) with the request as a parameter, so the
// same fake-device input is captured raw and with the browser's processing.
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function b64(buf) {
  const u = new Uint8Array(buf); let s = '';
  for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode.apply(null, u.subarray(i, i + 0x8000));
  return btoa(s);
}
const REQ = {
  raw: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 },
  default: true,  // what a page gets when it asks for nothing: all three on in Chrome (round 1)
  ec: { echoCancellation: true, noiseSuppression: false, autoGainControl: false, channelCount: 1 },
  ns: { echoCancellation: false, noiseSuppression: true, autoGainControl: false, channelCount: 1 },
  agc: { echoCancellation: false, noiseSuppression: false, autoGainControl: true, channelCount: 1 },
};
async function capture(cfg) {
  const out = { cfg, ua: navigator.userAgent };
  const stream = await navigator.mediaDevices.getUserMedia({ audio: REQ[cfg.request] });
  const track = stream.getAudioTracks()[0];
  out.settings = track.getSettings();
  const ctx = new AudioContext({ sampleRate: 48000 });
  out.ctxRate = ctx.sampleRate;
  await ctx.audioWorklet.addModule('/page/tap.js');
  const node = ctx.createMediaStreamSource(stream);
  const tap = new AudioWorkletNode(ctx, 'tap', { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1] });
  const worker = new Worker('/page/engine.js');
  const ch = new MessageChannel();
  const maxBlocks = Math.ceil((cfg.seconds + 2) * ctx.sampleRate / 128);
  const ready = new Promise((r) => { worker.onmessage = (e) => r(e.data); });
  worker.postMessage({ port: ch.port1, loadMs: 0, maxBlocks }, [ch.port1]);
  await ready;
  tap.port.postMessage({ port: ch.port2 }, [ch.port2]);
  const mute = ctx.createGain(); mute.gain.value = 0;
  node.connect(tap).connect(mute).connect(ctx.destination);
  await ctx.resume();
  await sleep(cfg.seconds * 1000);
  const tapDone = new Promise((r) => { tap.port.onmessage = (e) => r(e.data); });
  tap.port.postMessage({ stop: true });
  out.tap = await tapDone;
  const result = new Promise((r) => { worker.onmessage = (e) => r(e.data); });
  worker.postMessage({ stopAt: out.tap.lastSeq });
  const res = await Promise.race([result, sleep(60000).then(() => null)]);
  track.stop(); await ctx.close(); worker.terminate();
  if (!res) { out.workerTimeout = true; return out; }
  out.worker = { n: res.n, lost: res.lost, reordered: res.reordered, dup: res.dup, empty: res.empty };
  out.samples = b64(res.samples);
  return out;
}
window.e003r2 = { capture };
