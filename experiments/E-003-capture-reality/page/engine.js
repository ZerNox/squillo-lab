// Stand-in for squillo's engine worker (ADR 0006): receives every block,
// burns a set CPU time per block to stand in for the engine's work, and
// records sequence, frame and arrival time.
let port, loadMs = 0, maxBlocks = 0, stopAt = -1;
let samples, seqs, frames, recv, done, n = 0, expect = 0;
let timerRes = null;
let lost = 0, reordered = 0, dup = 0, empty = 0, lagDone = [];
function finish() {
  postMessage({
    n, lost, reordered, dup, empty, timerRes,
    samples: samples.buffer.slice(0, n * 128 * 4),
    seqs: seqs.slice(0, n), frames: frames.slice(0, n),
    recv: recv.slice(0, n), done: done.slice(0, n),
  });
  port.close();
}
onmessage = (e) => {
  const d = e.data;
  if (d.port) {
    port = d.port; loadMs = d.loadMs; maxBlocks = d.maxBlocks;
    samples = new Float32Array(maxBlocks * 128);
    seqs = new Int32Array(maxBlocks); frames = new Float64Array(maxBlocks);
    recv = new Float64Array(maxBlocks); done = new Float64Array(maxBlocks);
    port.onmessage = (m) => {
      const t = performance.now();
      const b = m.data;
      if (n >= maxBlocks) return;
      if (b.seq > expect) lost += b.seq - expect;
      else if (b.seq < expect) reordered++;
      expect = Math.max(expect, b.seq + 1);
      if (b.empty) empty++;
      samples.set(new Float32Array(b.buf), n * 128);
      seqs[n] = b.seq; frames[n] = b.frame; recv[n] = t;
      const until = t + loadMs;
      if (loadMs > 0) { let x = 0; while (performance.now() < until) x++; }
      done[n] = performance.now();
      n++;
      if (stopAt >= 0 && b.seq >= stopAt) finish();
    };
    // the timer's resolution in this worker: smallest nonzero step seen
    let res = Infinity, a = performance.now();
    for (let i = 0; i < 200000; i++) { const b = performance.now(); if (b > a) { res = Math.min(res, b - a); a = b; } }
    timerRes = res;
    postMessage({ ready: true });
  }
  if (d.stopAt !== undefined) {
    stopAt = d.stopAt;
    if (expect > stopAt) finish();
  }
};
