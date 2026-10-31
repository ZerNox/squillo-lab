// Draws the home-screen icons (a pitch coil on the page's dark ground) into page/icon/ with headless Chrome. Usage: node check/make-icons.mjs
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const dir = join(dirname(fileURLToPath(import.meta.url)), '../page/icon'); mkdirSync(dir, { recursive: true });
const b = await chromium.launch({ channel: 'chrome' }).catch(() => chromium.launch()), p = await b.newPage();
for (const s of [180, 192, 512]) { const url = await p.evaluate(s => { const c = document.createElement('canvas'); c.width = c.height = s; const x = c.getContext('2d'); x.fillStyle = '#0a0d12'; x.fillRect(0, 0, s, s); x.lineCap = 'round';
    const P = t => [s * (0.5 + 0.27 * Math.sin(t)), s * (0.76 - 0.52 * t / (6 * Math.PI) + 0.045 * Math.cos(t))], N = 240;
    for (const back of [true, false]) for (let i = 0; i < N; i++) { const t = 6 * Math.PI * i / N, u = t + 6 * Math.PI / N; if ((Math.cos(t) < 0) !== back) continue; const a = P(t), e = P(u); x.strokeStyle = back ? '#d9925c' : '#4fd8c4'; x.globalAlpha = back ? 0.55 : 1; x.lineWidth = s * (back ? 0.03 : 0.05); x.beginPath(); x.moveTo(...a); x.lineTo(...e); x.stroke(); }
    return c.toDataURL('image/png'); }, s); writeFileSync(join(dir, `icon-${s}.png`), Buffer.from(url.split(',')[1], 'base64')); }
await b.close();
