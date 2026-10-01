// Generator of squillo fixtures/build/engine-modules.json (squillo iteration
// 56, `build` BU-004): WebAssembly modules written byte by byte, each with the
// properties squillo's build checks of the engine module (ADR 0006: imports
// nothing; ADR 0016: no relaxed SIMD, no threads). Not the engine: test inputs.
//
// Conditions, written and committed before generating (squillo S15, L-047):
//  - every module is valid WebAssembly (WebAssembly.validate in this Node's V8);
//  - 'no-import', 'simd', 'relaxed-simd', 'shared-memory' import nothing, and
//    'one-import' imports exactly one function (WebAssembly.Module.imports);
//  - 'relaxed-simd' holds a relaxed SIMD instruction (opcode 0xFD then
//    0x100..0x113 as LEB128, WebAssembly 3.0 relaxed SIMD) in its code
//    section, and no other module does; 'simd' differs from it only in that
//    one instruction (plain i8x16.swizzle, 0xFD 0x0E), the must-fail input of
//    the relaxed check;
//  - 'shared-memory' declares a shared memory (limits flag 0x03), and no
//    other module declares any memory.
// Expected build outcome, by the conditions above: accept 'no-import' and
// 'simd'; refuse the other three, each for its one property.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { execSync } from 'node:child_process';

const HERE = path.dirname(new URL(import.meta.url).pathname);
try { execSync('git ls-files --error-unmatch -- build_fixtures.mjs', { cwd: HERE, stdio: 'ignore' }); execSync('git diff --quiet HEAD -- build_fixtures.mjs', { cwd: HERE }); }
catch { throw new Error('build_fixtures.mjs has uncommitted edits: commit it first (S15, L-047)'); }

const HDR = '0061736d01000000';
const V128_ZERO = 'fd0c' + '00'.repeat(16);
const hex2 = (n) => n.toString(16).padStart(2, '0');
// one function () -> v128: two v128.const 0, one two-operand SIMD op, end
function simdModule(op) {
  const body = '00' + V128_ZERO + V128_ZERO + op + '0b';
  const code = '01' + hex2(body.length / 2) + body;
  return HDR + '0105016000017b' + '03020100' + '0a' + hex2(code.length / 2) + code;
}
const MODULES = {
  'no-import': { hex: HDR, build: 'accept' },
  'one-import': { hex: HDR + '010401600000' + '020701016d01660000', build: 'refuse', why: 'imports' },
  simd: { hex: simdModule('fd0e'), build: 'accept' },
  'relaxed-simd': { hex: simdModule('fd8002'), build: 'refuse', why: 'relaxed SIMD' },
  'shared-memory': { hex: HDR + '050401030101', build: 'refuse', why: 'threads' },
};

// An independent reader: sections by id; memory limits flags; a scan of the
// code section for 0xFD followed by a LEB128 in 0x100..0x113.
function leb(b, i) { let r = 0, s = 0, x; do { x = b[i++]; r |= (x & 0x7f) << s; s += 7; } while (x & 0x80); return [r, i]; }
function read(b) {
  const out = { memories: [], relaxed: false };
  let i = 8;
  while (i < b.length) {
    const id = b[i++]; let n; [n, i] = leb(b, i); const end = i + n;
    if (id === 5) { let c, j; [c, j] = leb(b, i); for (let k = 0; k < c; k++) { const flags = b[j++]; out.memories.push(flags); let x; [x, j] = leb(b, j); if (flags & 1) [x, j] = leb(b, j); } }
    if (id === 10) for (let j = i; j < end - 2; j++) if (b[j] === 0xfd) { const [op] = leb(b, j + 1); if (op >= 0x100 && op <= 0x113) out.relaxed = true; }
    i = end;
  }
  return out;
}
// Check of the reader (S15): must-pass and must-fail on inputs that differ.
assert.equal(read(Buffer.from(MODULES['relaxed-simd'].hex, 'hex')).relaxed, true, 'reader must-pass: relaxed');
assert.equal(read(Buffer.from(MODULES.simd.hex, 'hex')).relaxed, false, 'reader must-fail: plain simd');
assert.deepEqual(read(Buffer.from(MODULES['shared-memory'].hex, 'hex')).memories, [3], 'reader must-pass: shared');
assert.deepEqual(read(Buffer.from(MODULES['no-import'].hex, 'hex')).memories, [], 'reader must-fail: no memory');

const out = { generator: 'squillo-lab experiments/E-006-page-egress/build_fixtures.mjs', modules: {} };
for (const [name, m] of Object.entries(MODULES)) {
  const b = Buffer.from(m.hex, 'hex');
  assert.ok(WebAssembly.validate(b), `${name} valid`);
  const imports = WebAssembly.Module.imports(new WebAssembly.Module(b)).length;
  const r = read(b);
  const shared = r.memories.some((f) => f & 2);
  assert.equal(imports, name === 'one-import' ? 1 : 0, `${name} imports`);
  assert.equal(r.relaxed, name === 'relaxed-simd', `${name} relaxed`);
  assert.equal(shared, name === 'shared-memory', `${name} shared`);
  assert.equal(r.memories.length, name === 'shared-memory' ? 1 : 0, `${name} memories`);
  const expect = imports === 0 && !r.relaxed && !shared ? 'accept' : 'refuse';
  assert.equal(m.build, expect, `${name} expected outcome follows from its properties`);
  out.modules[name] = { bytes_hex: m.hex, imports, relaxed_simd: r.relaxed, shared_memory: shared, build: m.build };
}
const dest = process.argv[2] ?? path.join(HERE, 'results/engine-modules.json');
fs.writeFileSync(dest, JSON.stringify(out, null, 2) + '\n');
console.log('wrote', dest);
