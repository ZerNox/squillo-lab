# E-006 — Does the page's policy keep everything on the device?

**Status:** answered · **Serves:** `squillo/VISION.md` §8 (audio stays on the
device; the user decides), §6 (honesty: a claim a singer can check) ·
**For:** squillo's first `security` spec (iteration 54), ADR 0010, ADR 0014,
ADR 0006

## Question

squillo ADR 0010 promises that a singer can open a network tab and see
nothing leave: a Content-Security-Policy with no `connect-src` and no
third-party script or style, plus ADR 0006's `'wasm-unsafe-eval'`. The
first slice is a static page whose host `build` has not chosen, and the
engine runs in a dedicated worker (ADR 0006). In Chrome and Firefox:

1. Does the policy stop every way the page could send something to another
   origin, when it arrives in a `<meta>` element (a host that sets no
   headers) and when it arrives as a response header?
2. Is the engine worker bound by it, when started from its own URL and when
   started from a `blob:` URL made from source text built into the page?
3. Does it stop WebRTC, and the page navigating itself away?
4. Does WebAssembly run under it, and is it refused without
   `'wasm-unsafe-eval'` (the claim ADR 0006 cites from MDN)?
5. Does the capture `AudioWorklet`'s scope have any network API at all?

## Hypotheses (written before the run, `rules.mjs`)

- **H1** Under `meta` and `header`, no judged document probe but WebRTC
  reaches the logger, in both browsers.
- **H2** Under `meta`, a URL-loaded worker's probes reach the logger (a
  worker loaded from a URL takes its policy container from its own
  response, and a `blob:` one inherits its creator's: HTML Living
  Standard, *creating a policy container from a fetch response*; a
  `<meta>` policy is on no response) and a `blob:` worker's do not; under `header`, neither's do.
- **H3** Where judged, WebRTC reaches the logger under every condition:
  the policy does not govern it.
- **H4** WebAssembly instantiates under `meta` and `header` in the document
  and in a policy-bound worker, and is refused under `*-nowasm` there.
- **H5** The page navigating itself to the logger reaches it under every
  condition.

## Protocol

`node run.mjs`, then `node analyze.mjs`; both refuse to run on uncommitted
edits of the rules (squillo S15, L-047). Per run, fresh: a page server on
`127.0.0.1` (one port), a logger on another port (so another origin), HTTP
and WebSocket on TCP and a UDP socket for STUN, and a fresh headless
browser (Chrome 154 via Playwright's `chrome` channel; the snap Firefox).

- **Conditions** (`rules.mjs`, `CONDITIONS`): `none` (the reference every
  probe must reach under), `meta`, `header`, `meta-nowasm`, `header-nowasm`;
  × worker `url` or `blob`; × Chrome, Firefox; × 3 reps = 60 runs.
- **Policy**: `default-src 'none'; script-src 'self' 'wasm-unsafe-eval';
  style-src 'self'; img-src 'self'; worker-src 'self' blob:; connect-src
  'none'; object-src 'none'; base-uri 'none'; form-action 'none'`. Under
  `header` it is sent on every response, the worker's and worklet's
  scripts included.
- **Probes**, each at the logger with a path naming run, context and probe.
  Document: `fetch`, XHR, WebSocket, EventSource, `sendBeacon`, `img`,
  `script`, stylesheet, `prefetch`, `audio`, `iframe`, WebRTC (a data
  channel's offer with STUN servers at the logger's UDP port, on 127.0.0.1
  and the laptop's LAN address). Worker: `fetch`, XHR, WebSocket,
  EventSource, `importScripts`. Then, after the page's outcomes are read,
  the page sets `location.href` to the logger. Worklet: `typeof` of
  `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `importScripts`.
  WebAssembly: the empty module instantiated in the document and in the
  worker.
- **Measure**: whether the logger logged the probe's exact path (WebRTC:
  whether the UDP port received any datagram) before navigation, read
  2000 ms after the probes return (ICE gathering waited up to 3000 ms).
  The page's own outcomes and `securitypolicyviolation` events are
  recorded too, but the logger is the truth: Chrome fires `load` on a
  blocked `iframe` and `sendBeacon` returns `true` when blocked.

### Checks

| Check | What | Must pass | Must fail |
| :--- | :--- | :--- | :--- |
| K0 | The logger check | a request the runner sends to the logger before the page loads is seen | a path no one requests is not; the UDP port has received nothing before the page loads |
| K1 | A probe is judged | it reached the logger in every rep of `none` (browser, worker mode) | a probe that did not is "not judged", never counted as blocked |
| K2 | A run is complete | every probe and the worklet's list returned, no harness error | — (asserted per run; a run that fails it stops the analysis) |

Recorded, not asserted: whether the reps agree (a count; nothing here is
timing-dependent by design, so disagreement would be reported, not
hidden); the page's own-origin requests; violation events.

### Timing (S19)

A sample of rep 0 of every cell, 20 runs covering every condition,
must-fail condition and worker mode in both browsers, each run to its end,
before the rules were committed (`node run.mjs --sample`, uncommitted,
to `data/cache/sample`, for timing and harness faults only): 2 min 42 s,
6.8 s a Chrome run and 9.3–9.6 s a Firefox run. The full run: 60 runs,
estimated 8 min 10 s; the analysis under 1 s on the sample. The sample
found no harness fault.

## Result

Round 1, squillo iteration 54. Chrome 154.0.8037.57 and Firefox 156.0,
headless, one Linux laptop, both origins on `127.0.0.1`; 60 runs, 3 reps
of each cell, `results/summary.json`. Checks: K0 held in 60 of 60 runs
(`checks.K0`: the runner's request seen 60, the unrequested path unseen
60, the UDP port silent before the page 60); K2 60 of 60; K1 judged 18
probes in Chrome and 17 in Firefox, whose `prefetch` never reached the
logger even with no policy, so it is not judged there
(`checks.K1_judged`). The reps agreed in every cell
(`reps_disagree_recorded` 0). Every hypothesis held (`hypotheses`).

1. **The document is bound either way.** Under `meta` and under `header`,
   in both worker modes and all reps, none of the judged document probes
   reached the logger: 11 in Chrome (`fetch`, XHR, WebSocket, EventSource,
   `sendBeacon`, `img`, `script`, stylesheet, `prefetch`, `audio`,
   `iframe`), 10 in Firefox; 252 probe firings, 0 reached (`cells.*.blocked`).
   The page's own reports mislead: Chrome's `sendBeacon` returned `true`
   and its blocked `iframe` fired `load`.
2. **A worker loaded from its own URL is not bound by a `<meta>` policy.**
   Under `meta` (and `meta-nowasm`), the URL-loaded worker's five probes
   reached the logger in 3 of 3 reps in both browsers, and it instantiated
   WebAssembly under `meta-nowasm`: it ran under no policy. A `blob:`
   worker made from source text in the page's script inherited the
   document's policy: none of its probes reached the logger, and
   WebAssembly was refused under `meta-nowasm`. Under `header`, sent with
   the worker's own script too, neither worker's probes reached it.
3. **WebRTC and navigation are not governed.** Under every condition, in
   60 of 60 runs, the data channel's ICE gathering sent STUN requests to
   the logger's UDP port (Chrome from 127.0.0.1 and the LAN address,
   Firefox from the LAN address; `cells.*.udp_from`), and the page setting
   its own `location.href` reached the logger in 60 of 60. No policy
   here stops a page that opens a peer connection or navigates itself;
   only the page's own code can, and `build` can check for it.
4. **WebAssembly:** instantiated in the document and in a policy-bound
   worker under `meta` and `header`; refused with a `CompileError` under
   `meta-nowasm` and `header-nowasm` there, in both browsers, 3 of 3.
   `'wasm-unsafe-eval'` is needed and sufficient for the empty module.
5. **The worklet has no network API:** `fetch`, `XMLHttpRequest`,
   `WebSocket`, `EventSource` and `importScripts` were `undefined` in the
   `AudioWorklet` scope in 60 of 60 runs (`worklet_apis`).
6. Own-origin requests: the page, its script, the engine script when
   URL-loaded, the worklet script, and `/favicon.ico`, which both browsers
   requested under `default-src 'none'` too (`own_origin_requests`); the
   favicon is the page's own origin, not egress.

**Limits.** Headless browsers on one laptop, both origins on loopback; a
real host, HTTPS and a real remote server are untested (the policy
directives do not depend on the scheme here, all probes cross origins by
port). Safari and Edge untested. The probe list is the channels named in
the protocol, not every browser feature; `prefetch` is not judged in
Firefox. One empty WebAssembly module, not the engine. No human step:
nothing here needs a microphone, room or listener.
