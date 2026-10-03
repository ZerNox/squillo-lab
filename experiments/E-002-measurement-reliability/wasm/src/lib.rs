//! E-002 round 7: squillo ADR 0007's YIN, as `yin.py` (E-002 round 1) runs
//! it, in four arithmetic variants, for the numeric epsilon across targets
//! (squillo ADR 0007, *Numeric epsilon*; question S-004). Crude experiment
//! code, never built on.
//!
//! Frame axis: frame i holds samples 384i..384i+383; its window is the 1536
//! samples ending with it; frames 0..2 have none, so frame k of the output
//! is frame k + 3. Lags 16..763 (yin.py: floor(48000/3000), ceil(48000/63)+1),
//! so W = 1536 - 763 = 773 samples are compared. CMND threshold 0.1, the
//! first lag under it, then down the dip while the next lag is lower; a lag
//! at either end of the search is not found; parabolic interpolation on the
//! difference function d, f0 = 48000 / lag.
//!
//! Variants: the difference function by its definition, a sum of squared
//! differences (`direct`, de Cheveigne and Kawahara 2002, eq. 6), or as
//! yin.py computes it, e0 + e_tau - 2 r with r by FFT (`fft`); each in
//! `f64` or `f32` throughout (input samples are f32 in every case).
//!
//! Output, per frame k, three f64 arrays concatenated: f0 in Hz (NaN when no
//! period is found), the CMND at the chosen whole lag (yin.py's `dmin`: the
//! smallest CMND over the search when no dip is under the threshold), and
//! the chosen whole lag (-1 when no dip is under the threshold).

use realfft::num_complex::Complex;
use realfft::num_traits::Float;
use realfft::{FftNum, RealFftPlanner};
use wasm_bindgen::prelude::*;

pub const SR: f64 = 48_000.0;
pub const HOP: usize = 384;
pub const WIN: usize = 1536;
pub const TAU_MIN: usize = 16; // floor(48000 / 3000), yin.py yin()
pub const TAU_MAX: usize = 763; // ceil(48000 / 63) + 1, yin.py yin()
pub const W: usize = WIN - TAU_MAX; // 773
pub const THRESHOLD: f64 = 0.1; // squillo ADR 0007, iteration 38
pub const N_FFT: usize = 4096; // yin.py: 1 << ceil(log2(WIN + W))

fn diff_direct<T: Float>(w: &[T], d: &mut [T]) {
    d[0] = T::zero();
    for t in 1..=TAU_MAX {
        let mut s = T::zero();
        for j in 0..W {
            let e = w[j] - w[j + t];
            s = s + e * e;
        }
        d[t] = s;
    }
}

struct Fft<T: FftNum> {
    fwd: std::sync::Arc<dyn realfft::RealToComplex<T>>,
    inv: std::sync::Arc<dyn realfft::ComplexToReal<T>>,
    ina: Vec<T>,
    inb: Vec<T>,
    sa: Vec<Complex<T>>,
    sb: Vec<Complex<T>>,
    r: Vec<T>,
    sq: Vec<T>,
}

impl<T: FftNum + Float> Fft<T> {
    fn new() -> Self {
        let mut p = RealFftPlanner::<T>::new();
        let fwd = p.plan_fft_forward(N_FFT);
        let inv = p.plan_fft_inverse(N_FFT);
        let (ina, inb) = (fwd.make_input_vec(), fwd.make_input_vec());
        let (sa, sb) = (fwd.make_output_vec(), fwd.make_output_vec());
        let r = inv.make_output_vec();
        Fft { fwd, inv, ina, inb, sa, sb, r, sq: vec![T::zero(); WIN + 1] }
    }

    /// yin.py cmnd(): r[t] = sum_{j<W} x[j] x[j+t] by FFT, d = e0 + e_t - 2r,
    /// d[0] = 0, d clamped at 0.
    fn diff(&mut self, w: &[T], d: &mut [T]) {
        for v in self.ina.iter_mut() { *v = T::zero(); }
        for v in self.inb.iter_mut() { *v = T::zero(); }
        self.ina[..W].copy_from_slice(&w[..W]);
        self.inb[..WIN].copy_from_slice(w);
        self.fwd.process(&mut self.ina, &mut self.sa).unwrap();
        self.fwd.process(&mut self.inb, &mut self.sb).unwrap();
        for (a, b) in self.sa.iter_mut().zip(self.sb.iter()) {
            *a = a.conj() * b;
        }
        let last = self.sa.len() - 1;
        self.sa[0].im = T::zero();
        self.sa[last].im = T::zero();
        self.inv.process(&mut self.sa, &mut self.r).unwrap();
        let n = T::from(N_FFT).unwrap();
        self.sq[0] = T::zero();
        for i in 0..WIN {
            self.sq[i + 1] = self.sq[i] + w[i] * w[i];
        }
        let e0 = self.sq[W];
        let two = T::from(2.0).unwrap();
        for t in 0..=TAU_MAX {
            let et = self.sq[t + W] - self.sq[t];
            let v = e0 + et - two * (self.r[t] / n);
            d[t] = if v > T::zero() { v } else { T::zero() };
        }
        d[0] = T::zero();
    }
}

fn parabola<T: Float>(y: &[T], t: usize) -> T {
    let (a, b, c) = (y[t - 1], y[t], y[t + 1]);
    let den = a - T::from(2.0).unwrap() * b + c;
    let tt = T::from(t).unwrap();
    if den <= T::zero() {
        return tt;
    }
    tt + T::from(0.5).unwrap() * (a - c) / den
}

fn run<T: FftNum + Float>(x: &[f32], fft: bool) -> Vec<f64> {
    let n_frames = x.len() / HOP;
    let nf = n_frames.saturating_sub(3);
    let mut out = vec![0.0f64; 3 * nf];
    let mut w = vec![T::zero(); WIN];
    let mut d = vec![T::zero(); TAU_MAX + 1];
    let mut dn = vec![T::zero(); TAU_MAX + 1];
    let mut f = if fft { Some(Fft::<T>::new()) } else { None };
    let thr = T::from(THRESHOLD).unwrap();
    for k in 0..nf {
        let s = HOP * k; // frame k + 3's window starts at 384 k
        for i in 0..WIN {
            w[i] = T::from(x[s + i]).unwrap();
        }
        match f.as_mut() {
            Some(f) => f.diff(&w, &mut d),
            None => diff_direct(&w, &mut d),
        }
        // CMND, yin.py: dn[0] = 1; dn[t] = d[t] t / sum_{1..t} d, 1 where the sum is 0
        dn[0] = T::one();
        let mut cs = T::zero();
        for t in 1..=TAU_MAX {
            cs = cs + d[t];
            dn[t] = if cs > T::zero() { d[t] * T::from(t).unwrap() / cs } else { T::one() };
        }
        let mut first = None;
        for t in TAU_MIN..TAU_MAX {
            if dn[t] < thr {
                first = Some(t);
                break;
            }
        }
        let (f0, dmin, lag) = match first {
            None => {
                let mut m = dn[TAU_MIN];
                for t in TAU_MIN..TAU_MAX {
                    if dn[t] < m { m = dn[t]; }
                }
                (f64::NAN, m.to_f64().unwrap(), -1.0)
            }
            Some(mut t) => {
                while t + 1 < TAU_MAX && dn[t + 1] < dn[t] {
                    t += 1;
                }
                let f0 = if t <= TAU_MIN || t >= TAU_MAX - 1 {
                    f64::NAN
                } else {
                    (T::from(SR).unwrap() / parabola(&d, t)).to_f64().unwrap()
                };
                (f0, dn[t].to_f64().unwrap(), t as f64)
            }
        };
        out[k] = f0;
        out[nf + k] = dmin;
        out[2 * nf + k] = lag;
    }
    out
}

/// `variant`: "f64-direct", "f32-direct", "f64-fft" or "f32-fft".
#[wasm_bindgen]
pub fn yin(x: &[f32], variant: &str) -> Vec<f64> {
    match variant {
        "f64-direct" => run::<f64>(x, false),
        "f32-direct" => run::<f32>(x, false),
        "f64-fft" => run::<f64>(x, true),
        "f32-fft" => run::<f32>(x, true),
        _ => panic!("unknown variant {variant}"),
    }
}

pub const VARIANTS: [&str; 4] = ["f64-direct", "f32-direct", "f64-fft", "f32-fft"];
