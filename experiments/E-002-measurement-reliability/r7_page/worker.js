// E-002 round 7, the browser side. Crude experiment code. For each input in
// the list and each variant, runs the WASM YIN and POSTs its float64 output
// to the harness, which writes it under data/cache/r7/out/<target>/.
self.onmessage = async (e) => {
  const cfg = e.data;
  const mod = await import(`/wasm/${cfg.pkg}/e002.js`);
  await mod.default();
  const names = (await (await fetch(cfg.list)).text()).trim().split('\n');
  const timing = {};
  for (const v of ['f64-direct', 'f32-direct', 'f64-fft', 'f32-fft']) {
    let ms = 0, samples = 0;
    for (const name of names) {
      const x = new Float32Array(await (await fetch(`/r7/in/${name}.f32`)).arrayBuffer());
      const t = performance.now();
      const y = mod.yin(x, v);
      ms += performance.now() - t;
      samples += x.length;
      const r = await fetch(`/put/${cfg.target}/${v}/${name}`, { method: 'POST', body: y.buffer });
      if (!r.ok) throw new Error(`put ${name} failed`);
    }
    timing[v] = { s: ms / 1000, audio_s: samples / 48000 };
    self.postMessage({ log: `${cfg.target} ${v}: ${(ms / 1000).toFixed(2)} s for ${(samples / 48000).toFixed(1)} s of audio` });
  }
  self.postMessage({ timing, ua: navigator.userAgent });
};
