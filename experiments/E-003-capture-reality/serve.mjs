// Serves the E-003 pages on http://localhost:8003/ for the needs-human step.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
const HERE = path.dirname(new URL(import.meta.url).pathname);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.wav': 'audio/wav' };
http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  let f = u === '/' ? '/page/human.html' : u;
  if (f.startsWith('/data/')) f = '/data/cache/' + f.slice(6);
  const p = path.join(HERE, f);
  if (!p.startsWith(HERE) || !fs.existsSync(p)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
}).listen(8003, 'localhost', () => console.log('open http://localhost:8003/ in Chrome, then in Firefox'));
