// E-003 round 4 (squillo iteration 53, F-042): round 1's stand-in engine
// worker (engine.js) that also sends the page one message per squillo
// frame (384 samples = 3 blocks, squillo SG-002), as JSON text (ADR 0006),
// once the block completing the frame has been received and its stand-in
// work done. The cell is a placeholder of the real one's shape: this round
// measures the transport, not the pitch.
const now = () => performance.timeOrigin + performance.now();
let port, loadMs = 0, maxBlocks = 0, stopAt = -1, stopAfter = -1, finished = false;
let seqs, recv, n = 0, expect = 0, lost = 0, reordered = 0, dup = 0;
let fBlockRecv, fPost, nf = 0;
function finish() {
  if (finished) return; finished = true;
  postMessage({ done: true, n, lost, reordered, dup, nf,
    seqs: seqs.slice(0, n), recv: recv.slice(0, n),
    fBlockRecv: fBlockRecv.slice(0, nf), fPost: fPost.slice(0, nf) });
  port.close();
}
onmessage = (e) => {
  const d = e.data;
  if (d.ping !== undefined) { postMessage({ pong: d.ping, t: now(), tRel: performance.now() }); return; }
  if (d.port) {
    port = d.port; loadMs = d.loadMs; maxBlocks = d.maxBlocks; stopAfter = d.stopAfter;
    seqs = new Int32Array(maxBlocks); recv = new Float64Array(maxBlocks);
    fBlockRecv = new Float64Array(Math.ceil(maxBlocks / 3)); fPost = new Float64Array(Math.ceil(maxBlocks / 3));
    port.onmessage = (m) => {
      const t = now();
      const b = m.data;
      if (finished || n >= maxBlocks) return;
      if (b.seq > expect) lost += b.seq - expect;
      else if (b.seq < expect) { reordered++; }
      if (b.seq === expect - 1) dup++;
      expect = Math.max(expect, b.seq + 1);
      seqs[n] = b.seq; recv[n] = t;
      const until = performance.now() + loadMs;
      if (loadMs > 0) { let x = 0; while (performance.now() < until) x++; }
      n++;
      if (n % 3 === 0) {
        const f = nf;
        const text = JSON.stringify({ frame: f, state: 'measured', cents: -1199.99, u: 1.7320508 });
        fBlockRecv[f] = t; fPost[f] = now(); nf++;
        postMessage(text);
      }
      // revised after the first Chrome step: the worker ends the frame stream
      // itself after stopAfter blocks, so a page that has fallen behind cannot
      // hold the run's end (README, round 4, R0)
      if (n === stopAfter || (stopAt >= 0 && b.seq >= stopAt)) finish();
    };
    postMessage({ ready: true });
  }
  if (d.stopAt !== undefined) { stopAt = d.stopAt; if (expect > stopAt) finish(); }
};
