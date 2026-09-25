# Compute: what the lab machine's GPUs mean for squillo

Written 2026-09-25, after the discrete GPU was verified at 12.61 TFLOPS FP32
(torch XPU, 4096² matmul, 705 ms engine time on the Arc, 0 ms on the Iris Xe,
206 MiB device memory). That check lives in
`~/investor/src/investor/core/gpu_probe.py`. It verifies the toolchain, and says
nothing about squillo yet.

## The lab host

| Device | Where | Role for squillo |
| :--- | :--- | :--- |
| Intel Core i7-12700H, 20 threads | CPU | Every timing measured so far (E-001 row 7, native code) |
| Intel Iris Xe (Alder Lake-P GT2) | PCI `0000:00:02.0`, `renderD128` | Integrated. A plausible proxy for a typical singer's laptop GPU |
| Intel Arc A770M, 16 GiB | PCI `0000:03:00.0`, `renderD129` | Discrete. About 13.5 TFLOPS FP32 peak. A proxy for the remote tier, not for a singer's device |

Other machines or cards may run lab code later. Do not write code or results
that assume this table.

## What the numbers mean here

squillo's first slice runs **in the browser, on the singer's device, as WASM**
(VISION §8, ADR 0001, ADR 0014). Remote processing is an opt-in tier that
needs a new decision, and that decision needs evidence from this lab. So:

- **The Arc measures the remote tier.** It answers "what would extra compute
  buy?": neural vocoders against WORLD/PSOLA in E-001, heavier pitch models
  against YIN in E-002 and E-005. That is the evidence VISION §8 asks for
  before remote processing is offered.
- **The Arc does not measure the device tier.** A GPU time is never evidence
  that something runs on-device. The device tier is WASM on a CPU, perhaps
  WebGPU later. Even E-001's native-CPU times on a 20-thread i7 are an upper
  bound for a browser.
- **TFLOPS do not predict audio work.** Squillo's per-frame work is small and
  latency-bound: a 10 ms frame, not a large matmul. Launch and transfer
  overhead can make the GPU slower than the CPU for streaming. Measure the
  real workload, per second of audio and per frame, never a peak figure.
- **The Iris Xe is a useful test target.** If WebGPU becomes a question, an
  integrated GPU is closer to what singers own than the Arc is.

## Do

- Use the Arc to speed lab work: batch runs over VocalSet, and reference
  trackers that give an upper bound or pseudo-ground-truth for E-002 and E-005.
- Report each timing with its tier (`device-cpu-native`, `device-wasm`,
  `remote-gpu`), the device's full name and PCI address, and the tool
  versions.
- Keep remote-tier results in their own rows, so a spec cannot cite one as an
  on-device result.

## Don't

- Don't select a GPU by index. OpenVINO's `GPU.0`, `renderD128` and `xpu:0`
  can all be the Iris Xe on this host, and Vulkan's order differs from DRM's.
  Select by name or device memory.
- Don't trust that selection alone. Verify which GPU did the work (below).
- Don't count a run where the device is unverified or a fallback happened. A
  silent CPU fallback looks like a slow GPU.
- Don't put GPU code or GPU-only assumptions into squillo's specs.

## Which GPU did the work: a recipe for any card

1. **Enumerate.** Use `/sys/class/drm/card*/device`: PCI address, vendor,
   device id and driver. A card is discrete when it has device-local memory
   (`lmem_total_bytes` on Intel) or is off the root bus `0000:00:*`.
2. **Select.** Pick the device by name or memory in the framework (torch,
   OpenVINO, Vulkan), never by index.
3. **Attribute.** Run the workload in a child process and sample
   `/proc/<pid>/fdinfo/*` about 10 times a second. Each DRM fd reports
   `drm-pdev` (the PCI address) and cumulative `drm-engine-*` nanoseconds. The
   run counts only when the engine time is on the intended PCI address, with
   no more than 10 % elsewhere. This works on Intel i915/xe and AMD amdgpu.
   NVIDIA's proprietary driver may not report it; use `nvidia-smi
   --query-compute-apps` or NVML there, matched by PID.
4. **Floor.** Set a throughput floor that the wrong device cannot reach.
   Iris Xe's peak is about 2.2 TFLOPS, so 4 TFLOPS separates it from the Arc.
   Set a new floor for each new card from its published peak.

`gpu_probe.py` implements steps 1 to 4 for Intel. Copy it into an experiment
when one first needs the GPU, rather than importing across repos.
