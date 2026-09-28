//! E-001 round 2, native side. Crude experiment code.
//!
//! `cargo run --release --bin bench -- <dir>` reads <dir>/list.txt and the
//! inputs r2_export.py wrote, and for every input and method writes the
//! output of each request to <dir>/out/<name>.<method>.<mod>.native.f64 and
//! the f0 (WORLD, per 5 ms) or pitch (PSOLA, per 10 ms) to
//! <dir>/out/<name>.<method>.f0.native.f64. For the timing inputs it times
//! each stage, best of three, one thread, and prints one JSON line per input
//! and method to stdout.
use e001::{Psola, World};
use std::time::Instant;

fn read(p: &str) -> Vec<f64> {
    let b = std::fs::read(p).unwrap_or_else(|e| panic!("{p}: {e}"));
    b.chunks_exact(8).map(|c| f64::from_le_bytes(c.try_into().unwrap())).collect()
}

fn write(p: &str, v: &[f64]) {
    let b: Vec<u8> = v.iter().flat_map(|x| x.to_le_bytes()).collect();
    std::fs::write(p, b).unwrap();
}

const MODS: [&str; 3] = ["id", "c100", "s100"];

fn main() {
    let dir = std::env::args().nth(1).expect("dir");
    let only_timing = std::env::args().any(|a| a == "--timing-only");
    std::fs::create_dir_all(format!("{dir}/out")).unwrap();
    for line in std::fs::read_to_string(format!("{dir}/list.txt")).unwrap().lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        let (name, timing) = (f[0], f[2] == "1");
        if only_timing && !timing {
            continue;
        }
        let x = read(&format!("{dir}/{name}.x.f64"));
        let secs = x.len() as f64 / e001::FS;
        let shifts: Vec<Vec<f64>> = MODS.iter().map(|m| read(&format!("{dir}/{name}.{m}.f64"))).collect();
        for method in ["harvest", "dio", "psola"] {
            let reps = if timing { 3 } else { 1 };
            let mut best = vec![f64::INFINITY; 4];
            for _ in 0..reps {
                let mut st = Vec::new();
                let t0 = Instant::now();
                if method == "psola" {
                    let mut p = Psola::new(x.clone());
                    st.push(t0.elapsed().as_secs_f64());
                    let t1 = Instant::now();
                    p.marks();
                    st.push(t1.elapsed().as_secs_f64());
                    st.push(0.0);
                    let t2 = Instant::now();
                    let _ = p.synth(shifts[1].clone());
                    st.push(t2.elapsed().as_secs_f64());
                    for (k, m) in MODS.iter().enumerate() {
                        write(&format!("{dir}/out/{name}.{method}.{m}.native.f64"), &p.synth(shifts[k].clone()));
                    }
                    write(&format!("{dir}/out/{name}.{method}.f0.native.f64"), &p.pitch());
                } else {
                    let mut w = World::new(x.clone(), method);
                    st.push(t0.elapsed().as_secs_f64());
                    let t1 = Instant::now();
                    w.envelope();
                    st.push(t1.elapsed().as_secs_f64());
                    let t2 = Instant::now();
                    w.aperiodicity();
                    st.push(t2.elapsed().as_secs_f64());
                    let t3 = Instant::now();
                    let _ = w.synth(shifts[1].clone());
                    st.push(t3.elapsed().as_secs_f64());
                    for (k, m) in MODS.iter().enumerate() {
                        write(&format!("{dir}/out/{name}.{method}.{m}.native.f64"), &w.synth(shifts[k].clone()));
                    }
                    write(&format!("{dir}/out/{name}.{method}.f0.native.f64"), &w.f0());
                }
                for k in 0..4 {
                    best[k] = best[k].min(st[k]);
                }
            }
            if timing {
                println!(
                    "{{\"input\":\"{name}\",\"method\":\"{method}\",\"env\":\"native\",\"seconds\":{secs},\"stages_s\":[{},{},{},{}]}}",
                    best[0], best[1], best[2], best[3]
                );
            }
            eprintln!("{name} {method}");
        }
    }
}
