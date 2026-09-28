// E-001 fold 2 (squillo iteration 43, F-043 k), the browser side. Crude experiment code.
// Fold 1's worker (f1_page/worker.js) compared browsers by a 32-bit FNV-1a hash.
// This one runs the same crate on the same inputs, two passes, and sends every
// rung's samples, as f64 and as the f32 that crosses squillo's boundary
// (ADR 0006), back to the server, so f2_compare.py compares them sample by sample.
self.onmessage = async (e) => {
  const { browser } = e.data;
  const mod = await import('/wasm/pkg/e001.js');
  await mod.default();
  const f64 = async (p) => new Float64Array(await (await fetch(p)).arrayBuffer());
  const put = async (p, a) => {
    const r = await fetch(p, { method: 'PUT', body: new Uint8Array(a.buffer, a.byteOffset, a.byteLength) });
    if (!r.ok) throw new Error(`PUT ${p}: ${r.status}`);
  };
  const lines = (await (await fetch('/data/f1/list.txt')).text()).trim().split('\n').map((l) => l.split(' '));
  const rows = [];
  for (const [name, ...reqs] of lines) {
    const x = await f64(`/data/f1/${name}.x.f64`);
    const shifts = {};
    for (const r of reqs) shifts[r] = await f64(`/data/f1/${name}.${r}.f64`);
    for (let pass = 0; pass < 2; pass++) {
      let t = performance.now();
      const w = new mod.World(x, 'dio');
      w.envelope();
      w.aperiodicity();
      const analysis_s = (performance.now() - t) / 1000;
      for (const r of reqs) {
        t = performance.now();
        const y = w.synth(shifts[r]);
        const synth_s = (performance.now() - t) / 1000;
        await put(`/out/${browser}/p${pass}/${name}.${r}.f64`, y);
        await put(`/out/${browser}/p${pass}/${name}.${r}.f32`, Float32Array.from(y));
        rows.push({ input: name, request: r, pass, seconds: x.length / 48000, analysis_s, synth_s, samples: y.length });
      }
      w.free();
    }
    self.postMessage({ log: `${name} done` });
  }
  self.postMessage({ rows, userAgent: navigator.userAgent });
};
