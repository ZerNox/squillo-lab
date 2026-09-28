// E-001 fold 1 (squillo iteration 37), the browser side. Crude experiment code.
// For each input in data/f1/list.txt: WORLD with DIO plus StoneMask (round 2's
// crate, plain WASM), run twice in this worker; each request's output hashed
// as f64 and as f32 (the rung crosses the boundary as f32, squillo ADR 0006),
// compared with the native output, and the stages timed once per pass.
self.onmessage = async (e) => {
  const mod = await import('/wasm/pkg/e001.js');
  const inst = await mod.default();
  const mem = () => inst.memory.buffer.byteLength;
  const f64 = async (p) => new Float64Array(await (await fetch(p)).arrayBuffer());
  const hash = (a) => { // FNV-1a over the bytes
    const b = new Uint8Array(a.buffer, a.byteOffset, a.byteLength);
    let h = 0x811c9dc5;
    for (let i = 0; i < b.length; i++) { h ^= b[i]; h = Math.imul(h, 0x01000193) >>> 0; }
    return h.toString(16);
  };
  const lines = (await (await fetch('/data/f1/list.txt')).text()).trim().split('\n').map((l) => l.split(' '));
  const rows = [];
  for (const [name, ...reqs] of lines) {
    const x = await f64(`/data/f1/${name}.x.f64`);
    const shifts = {};
    for (const r of reqs) shifts[r] = await f64(`/data/f1/${name}.${r}.f64`);
    const per = Object.fromEntries(reqs.map((r) => [r, { f64_hashes: [], f32_hashes: [], synth_s: [] }]));
    const analysis = [];
    let held = 0, memMax = 0;
    for (let pass = 0; pass < 2; pass++) {
      let t = performance.now();
      const w = new mod.World(x, 'dio');
      w.envelope();
      w.aperiodicity();
      analysis.push((performance.now() - t) / 1000);
      held = w.bytes();
      for (const r of reqs) {
        t = performance.now();
        const y = w.synth(shifts[r]);
        per[r].synth_s.push((performance.now() - t) / 1000);
        per[r].f64_hashes.push(hash(y));
        per[r].f32_hashes.push(hash(Float32Array.from(y)));
        if (pass === 0) {
          const nat = await f64(`/data/f1/out/${name}.${r}.native.f64`);
          let maxDiff = 0, same = nat.length === y.length, f32same = true;
          for (let i = 0; i < y.length; i++) {
            const d = Math.abs(y[i] - nat[i]);
            if (!(d === 0)) same = false;
            if (Math.fround(y[i]) !== Math.fround(nat[i])) f32same = false;
            if (d > maxDiff || Number.isNaN(d)) maxDiff = Number.isNaN(d) ? NaN : d;
          }
          per[r].vs_native = { length_equal: nat.length === y.length, bit_identical: same, f32_identical: f32same, max_abs_diff: maxDiff };
        }
        memMax = Math.max(memMax, mem());
      }
      w.free();
    }
    for (const r of reqs) rows.push({ input: name, request: r, seconds: x.length / 48000, analysis_s: analysis,
      analysis_bytes: held, wasm_memory_bytes: memMax, ...per[r] });
    self.postMessage({ log: `${name} analysis ${analysis.map((v) => v.toFixed(3))} s, memory ${memMax}` });
  }
  self.postMessage({ rows, userAgent: navigator.userAgent });
};
