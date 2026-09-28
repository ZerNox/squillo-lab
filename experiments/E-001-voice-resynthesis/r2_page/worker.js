// E-001 round 2, the browser side. Crude experiment code.
// For each timing input and method: every stage timed with performance.now(),
// best of three (every repeat's total kept too), the bytes the WORLD analysis
// holds, in this worker (one thread). The c100 output is compared with
// the native build's (data/cache/r2/out) and hashed, so Chrome and Firefox can
// be compared with each other.
self.onmessage = async (e) => {
  const cfg = e.data;
  const mod = await import(`/wasm/${cfg.pkg}/e001.js`);
  const inst = await mod.default();
  const mem = () => inst.memory.buffer.byteLength;
  const f64 = async (p) => new Float64Array(await (await fetch(p)).arrayBuffer());
  const list = (await (await fetch('/data/r2/list.txt')).text()).trim().split('\n')
    .map((l) => l.split(' ')).filter((f) => f[2] === '1').map((f) => f[0]);
  const rows = [];
  const hash = (a) => { // FNV-1a over the bytes
    const b = new Uint8Array(a.buffer, a.byteOffset, a.byteLength);
    let h = 0x811c9dc5;
    for (let i = 0; i < b.length; i++) { h ^= b[i]; h = Math.imul(h, 0x01000193) >>> 0; }
    return h.toString(16);
  };
  for (const name of list) {
    const x = await f64(`/data/r2/${name}.x.f64`);
    const c100 = await f64(`/data/r2/${name}.c100.f64`);
    for (const method of ['harvest', 'dio', 'psola']) {
      const best = [Infinity, Infinity, Infinity, Infinity];
      let y = null;
      let memMax = 0, held = 0;
      const totals = [];
      for (let rep = 0; rep < cfg.reps; rep++) {
        const st = [];
        let t = performance.now();
        if (method === 'psola') {
          const p = new mod.Psola(x);
          st.push(performance.now() - t); t = performance.now();
          p.marks();
          st.push(performance.now() - t); st.push(0); t = performance.now();
          y = p.synth(c100);
          st.push(performance.now() - t);
          p.free();
        } else {
          const w = new mod.World(x, method);
          st.push(performance.now() - t); t = performance.now();
          w.envelope();
          st.push(performance.now() - t); t = performance.now();
          w.aperiodicity();
          st.push(performance.now() - t); t = performance.now();
          y = w.synth(c100);
          st.push(performance.now() - t);
          held = w.bytes();
          w.free();
        }
        memMax = Math.max(memMax, mem());
        totals.push(st.reduce((a, b) => a + b, 0) / 1000);
        for (let k = 0; k < 4; k++) best[k] = Math.min(best[k], st[k]);
      }
      const nat = await f64(`/data/r2/out/${name}.${method}.c100.native.f64`);
      let maxDiff = 0, peak = 0, same = nat.length === y.length;
      for (let i = 0; i < y.length; i++) {
        const d = Math.abs(y[i] - nat[i]);
        if (!(d === 0)) same = false;
        if (d > maxDiff || Number.isNaN(d)) maxDiff = Number.isNaN(d) ? NaN : d;
        peak = Math.max(peak, Math.abs(nat[i]));
      }
      const row = { input: name, method, seconds: x.length / 48000, stages_s: best.map((v) => v / 1000),
        reps_total_s: totals, analysis_bytes: held,
        wasm_memory_bytes: memMax, vs_native: { bit_identical: same, max_abs_diff: maxDiff, native_peak: peak },
        c100_hash: hash(y) };
      rows.push(row);
      self.postMessage({ log: `${name} ${method} ${JSON.stringify(row.stages_s.map((v) => +v.toFixed(4)))}` });
    }
  }
  self.postMessage({ rows, userAgent: navigator.userAgent, crossOriginIsolated: self.crossOriginIsolated,
    hardwareConcurrency: navigator.hardwareConcurrency });
};
