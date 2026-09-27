// The capture AudioWorklet as squillo ADR 0006 has it: one message per
// 128-sample render quantum, the block's buffer transferred to the engine
// worker over a MessagePort.
class Tap extends AudioWorkletProcessor {
  constructor() {
    super();
    this.out = null;
    this.seq = 0;
    this.stopped = false;
    this.stats = { calls: 0, emptyInputs: 0, maxChannels: 0, channelsDiffer: 0,
                   firstFrame: null, sizes: {} };
    this.port.onmessage = (e) => {
      if (e.data.port) this.out = e.data.port;
      if (e.data.stop) {
        this.stopped = true;
        this.port.postMessage({ lastSeq: this.seq - 1, stats: this.stats,
                                frame: currentFrame });
      }
    };
  }
  process(inputs) {
    if (this.stopped || !this.out) return true;
    const s = this.stats;
    s.calls++;
    if (s.firstFrame === null) s.firstFrame = currentFrame;
    const input = inputs[0];
    s.maxChannels = Math.max(s.maxChannels, input.length);
    let buf;
    if (input.length === 0) {
      s.emptyInputs++;
      buf = new Float32Array(128);
    } else {
      const ch0 = input[0];
      s.sizes[ch0.length] = (s.sizes[ch0.length] || 0) + 1;
      buf = new Float32Array(ch0);
      for (let c = 1; c < input.length; c++) {
        const ch = input[c];
        for (let i = 0; i < ch.length; i++) {
          if (ch[i] !== ch0[i]) { s.channelsDiffer++; break; }
        }
      }
    }
    this.out.postMessage({ seq: this.seq++, frame: currentFrame,
                           empty: input.length === 0, buf: buf.buffer },
                         [buf.buffer]);
    return true;
  }
}
registerProcessor('tap', Tap);
