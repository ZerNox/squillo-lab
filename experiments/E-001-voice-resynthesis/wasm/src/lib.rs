//! E-001 round 2: the re-synthesis pipelines of round 1, in Rust, for timing
//! in native code and in WASM in a browser. Crude experiment code, never
//! built on.
//!
//! - `World`: WORLD (Morise, Yokomori and Ozawa 2016) through world-rs 0.1.0,
//!   a pure-Rust port of the C++ library. As round 1's `resynth.py`: f0 by
//!   Harvest, or DIO plus StoneMask, floor 60 Hz, ceiling 1100 Hz, 5 ms
//!   frames; CheapTrick and D4C with their defaults; the f0 multiplied by
//!   2^(shift/1200) and re-synthesized.
//! - `Psola`: a crude TD-PSOLA written here, standing in for Praat's
//!   Manipulation (round 1). Pitch every 10 ms by normalised autocorrelation
//!   (Boersma 1993: Hann window of three periods of the floor, divided by the
//!   window's own autocorrelation), no path search; pitch marks at waveform
//!   maxima one period apart; overlap-add of two-period Hann-windowed grains
//!   at the shifted period. Not Praat's algorithm; it shows the cost class.
//!
//! Each stage is a separate call so the caller can time it.

use realfft::RealFftPlanner;
use wasm_bindgen::prelude::*;
use world_rs::{cheaptrick, d4c, dio, harvest, stonemask, synthesis};

pub const FS: f64 = 48_000.0;
pub const F0_FLOOR: f64 = 60.0;
pub const F0_CEIL: f64 = 1100.0;
pub const FRAME_MS: f64 = 5.0;

fn shift_at(shift: &[f64], t: f64) -> f64 {
    // the request in cents, given at k * 5 ms; linear between, held at the ends
    let p = t / (FRAME_MS / 1000.0);
    if p <= 0.0 {
        return shift[0];
    }
    let i = p.floor() as usize;
    if i + 1 >= shift.len() {
        return shift[shift.len() - 1];
    }
    let a = p - i as f64;
    shift[i] * (1.0 - a) + shift[i + 1] * a
}

#[wasm_bindgen]
pub struct World {
    x: Vec<f64>,
    f0: Vec<f64>,
    t: Vec<f64>,
    sp: Vec<Vec<f64>>,
    ap: Vec<Vec<f64>>,
    fft_size: usize,
}

#[wasm_bindgen]
impl World {
    /// Stage 1: f0. `method` is "harvest" or "dio" (DIO plus StoneMask).
    #[wasm_bindgen(constructor)]
    pub fn new(x: Vec<f64>, method: &str) -> World {
        let (f0, t) = match method {
            "harvest" => {
                let mut o = harvest::initialize_harvest_option();
                o.f0_floor = F0_FLOOR;
                o.f0_ceil = F0_CEIL;
                o.frame_period = FRAME_MS;
                let r = harvest::harvest(&x, FS, &o).expect("harvest");
                (r.f0, r.temporal_positions)
            }
            "dio" => {
                let mut o = dio::initialize_dio_option();
                o.f0_floor = F0_FLOOR;
                o.f0_ceil = F0_CEIL;
                o.frame_period = FRAME_MS;
                let r = dio::dio(&x, FS, &o).expect("dio");
                let f0 = stonemask::stone_mask(&x, x.len(), FS, &r.temporal_positions, &r.f0, r.f0.len())
                    .expect("stonemask");
                (f0, r.temporal_positions)
            }
            _ => panic!("method"),
        };
        World { x, f0, t, sp: Vec::new(), ap: Vec::new(), fft_size: 0 }
    }

    /// Stage 2: CheapTrick envelope.
    pub fn envelope(&mut self) {
        let o = cheaptrick::initialize_cheaptrick_option(FS);
        self.fft_size = o.fft_size as usize;
        self.sp = cheaptrick::cheaptrick(&self.x, FS, &self.t, &self.f0, &o).expect("cheaptrick");
    }

    /// Stage 3: D4C aperiodicity.
    pub fn aperiodicity(&mut self) {
        let o = d4c::initialize_d4c_option();
        self.ap = d4c::d4c(&self.x, FS, &self.t, &self.f0, self.fft_size as i32, &o).expect("d4c");
    }

    /// Stage 4: re-synthesis with the f0 shifted by `shift` cents (per 5 ms frame).
    pub fn synth(&self, shift: Vec<f64>) -> Vec<f64> {
        let f0: Vec<f64> = self
            .f0
            .iter()
            .zip(&self.t)
            .map(|(&f, &t)| if f > 0.0 { f * 2f64.powf(shift_at(&shift, t) / 1200.0) } else { 0.0 })
            .collect();
        synthesis::synthesis(&f0, f0.len(), &self.sp, &self.ap, self.fft_size, FRAME_MS, FS, self.x.len())
            .expect("synthesis")
    }

    pub fn f0(&self) -> Vec<f64> {
        self.f0.clone()
    }

    /// Bytes held by the analysis (samples, f0, envelope, aperiodicity), as f64.
    pub fn bytes(&self) -> f64 {
        let rows: usize = self.sp.iter().map(|r| r.len()).sum::<usize>() + self.ap.iter().map(|r| r.len()).sum::<usize>();
        (8 * (self.x.len() + 2 * self.f0.len() + rows)) as f64
    }
}

#[wasm_bindgen]
pub struct Psola {
    x: Vec<f64>,
    /// pitch per 10 ms frame, 0 where unvoiced
    pitch: Vec<f64>,
    /// analysis marks (sample index) and whether each is voiced
    marks: Vec<usize>,
    voiced: Vec<bool>,
}

const P_STEP: f64 = 0.010;
const VOICING: f64 = 0.45; // Praat's default voicing threshold
const SILENCE: f64 = 0.03; // Praat's default silence threshold, of the global peak

#[wasm_bindgen]
impl Psola {
    /// Stage 1: pitch by normalised autocorrelation.
    #[wasm_bindgen(constructor)]
    pub fn new(x: Vec<f64>) -> Psola {
        let w = (3.0 * FS / F0_FLOOR).round() as usize; // 2400
        let nfft = (2 * w).next_power_of_two();
        let lag_min = (FS / F0_CEIL).floor() as usize;
        let lag_max = ((FS / F0_FLOOR).ceil() as usize).min(w / 2);
        let mut planner = RealFftPlanner::<f64>::new();
        let fwd = planner.plan_fft_forward(nfft);
        let inv = planner.plan_fft_inverse(nfft);
        let hann: Vec<f64> = (0..w).map(|i| 0.5 - 0.5 * (2.0 * std::f64::consts::PI * (i as f64 + 0.5) / w as f64).cos()).collect();
        let ac = |buf: &mut Vec<f64>| -> Vec<f64> {
            let mut spec = fwd.make_output_vec();
            fwd.process(buf, &mut spec).unwrap();
            for c in spec.iter_mut() {
                *c = realfft::num_complex::Complex::new(c.norm_sqr(), 0.0);
            }
            let mut out = inv.make_output_vec();
            inv.process(&mut spec, &mut out).unwrap();
            out
        };
        let mut hb = vec![0.0; nfft];
        hb[..w].copy_from_slice(&hann);
        let rw = ac(&mut hb);
        let peak = x.iter().fold(0.0f64, |m, v| m.max(v.abs()));
        let nfr = (x.len() as f64 / FS / P_STEP).floor() as usize;
        let mut pitch = vec![0.0; nfr];
        let mut buf = vec![0.0; nfft];
        for (k, p) in pitch.iter_mut().enumerate() {
            let c = ((k as f64 + 0.5) * P_STEP * FS) as isize;
            let s = c - (w / 2) as isize;
            let mut lpeak = 0.0f64;
            let mut mean = 0.0;
            for i in 0..w {
                let j = s + i as isize;
                let v = if j >= 0 && (j as usize) < x.len() { x[j as usize] } else { 0.0 };
                buf[i] = v;
                mean += v;
                lpeak = lpeak.max(v.abs());
            }
            if lpeak < SILENCE * peak {
                continue;
            }
            mean /= w as f64;
            for i in 0..w {
                buf[i] = (buf[i] - mean) * hann[i];
            }
            buf[w..].fill(0.0);
            let r = ac(&mut buf);
            let r0 = r[0];
            if r0 <= 0.0 {
                continue;
            }
            let nr = |l: usize| r[l] / r0 / (rw[l] / rw[0]);
            // highest local maximum in range; a shorter lag wins within 3 % (a crude octave cost)
            let mut best = (0usize, 0.0f64);
            for l in lag_min.max(1)..lag_max {
                let v = nr(l);
                if v > nr(l - 1) && v >= nr(l + 1) && v > best.1 * 1.03 {
                    best = (l, v);
                }
            }
            if best.0 == 0 || best.1 < VOICING {
                continue;
            }
            let (a, b, c2) = (nr(best.0 - 1), best.1, nr(best.0 + 1));
            let d = a - 2.0 * b + c2;
            let off = if d.abs() > 1e-12 { 0.5 * (a - c2) / d } else { 0.0 };
            *p = FS / (best.0 as f64 + off);
        }
        Psola { x, pitch, marks: Vec::new(), voiced: Vec::new() }
    }

    fn period_at(&self, n: usize) -> f64 {
        let k = ((n as f64 / FS) / P_STEP) as usize;
        let f = *self.pitch.get(k).unwrap_or(&0.0);
        if f > 0.0 { FS / f } else { 0.0 }
    }

    /// Stage 2: pitch marks. Voiced: waveform maxima one period apart;
    /// unvoiced: every 10 ms.
    pub fn marks(&mut self) {
        let n = self.x.len();
        let step_u = (P_STEP * FS) as usize;
        let mut m = 0usize;
        let (mut marks, mut voiced) = (Vec::new(), Vec::new());
        let mut last_voiced = false;
        while m < n {
            let t = self.period_at(m);
            if t > 0.0 {
                let (lo, hi) = if last_voiced {
                    (m + (0.8 * t) as usize, (m + (1.2 * t) as usize).min(n - 1))
                } else {
                    (m, (m + t as usize).min(n - 1))
                };
                if lo >= hi {
                    break;
                }
                let mut j = lo;
                for i in lo..=hi {
                    if self.x[i] > self.x[j] {
                        j = i;
                    }
                }
                marks.push(j);
                voiced.push(true);
                last_voiced = true;
                m = j;
            } else {
                m += step_u;
                if m < n && self.period_at(m) == 0.0 {
                    marks.push(m);
                    voiced.push(false);
                }
                last_voiced = false;
            }
        }
        self.marks = marks;
        self.voiced = voiced;
    }

    /// Stage 3: overlap-add at the period shifted by `shift` cents (per 5 ms frame).
    pub fn synth(&self, shift: Vec<f64>) -> Vec<f64> {
        let n = self.x.len();
        let mut y = vec![0.0; n];
        if self.marks.is_empty() {
            return y;
        }
        let local_p = |i: usize| -> f64 {
            let l = if i > 0 { self.marks[i] - self.marks[i - 1] } else { usize::MAX };
            let r = if i + 1 < self.marks.len() { self.marks[i + 1] - self.marks[i] } else { usize::MAX };
            let p = l.min(r);
            if p == usize::MAX { P_STEP * FS } else { p as f64 }
        };
        let mut t = self.marks[0] as f64;
        let mut i = 0usize;
        while t < n as f64 {
            // nearest analysis mark (no time-scaling: the map is the identity)
            while i + 1 < self.marks.len() && (self.marks[i + 1] as f64 - t).abs() <= (self.marks[i] as f64 - t).abs() {
                i += 1;
            }
            let p = local_p(i);
            let half = p.round() as isize;
            let c = self.marks[i] as isize;
            let to = t.round() as isize;
            for k in -half..=half {
                let (src, dst) = (c + k, to + k);
                if src < 0 || dst < 0 || src as usize >= n || dst as usize >= n {
                    continue;
                }
                let w = 0.5 + 0.5 * (std::f64::consts::PI * k as f64 / (half as f64 + 1.0)).cos();
                y[dst as usize] += w * self.x[src as usize];
            }
            let step = if self.voiced[i] { p / 2f64.powf(shift_at(&shift, t / FS) / 1200.0) } else { p };
            t += step.max(1.0);
        }
        y
    }

    pub fn pitch(&self) -> Vec<f64> {
        self.pitch.clone()
    }

    pub fn n_marks(&self) -> usize {
        self.marks.len()
    }
}
