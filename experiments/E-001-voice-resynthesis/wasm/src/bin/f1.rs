//! E-001 fold 1 (squillo iteration 37), native side. Crude experiment code.
//!
//! `f1 <dir>` reads <dir>/list.txt, one line per input: its name and the
//! names of its requests. For each it reads <name>.x.f64 (48 kHz samples,
//! f64 little-endian) and <name>.<req>.f64 (the request in cents at WORLD's
//! frame times k * 5 ms), runs round 2's WORLD pipeline with DIO plus
//! StoneMask, and writes <dir>/out/<name>.<req>.native.f64. One JSON line per
//! input to stdout: seconds, the analysis's bytes, stage times (one pass).
use e001::World;
use std::time::Instant;

fn read(p: &str) -> Vec<f64> {
    let b = std::fs::read(p).unwrap_or_else(|e| panic!("{p}: {e}"));
    b.chunks_exact(8).map(|c| f64::from_le_bytes(c.try_into().unwrap())).collect()
}

fn write(p: &str, v: &[f64]) {
    let b: Vec<u8> = v.iter().flat_map(|x| x.to_le_bytes()).collect();
    std::fs::write(p, b).unwrap();
}

fn main() {
    let dir = std::env::args().nth(1).expect("dir");
    std::fs::create_dir_all(format!("{dir}/out")).unwrap();
    for line in std::fs::read_to_string(format!("{dir}/list.txt")).unwrap().lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        let name = f[0];
        let x = read(&format!("{dir}/{name}.x.f64"));
        let t0 = Instant::now();
        let mut w = World::new(x.clone(), "dio");
        w.envelope();
        w.aperiodicity();
        let analysis = t0.elapsed().as_secs_f64();
        let mut synth = Vec::new();
        for req in &f[1..] {
            let s = read(&format!("{dir}/{name}.{req}.f64"));
            let t1 = Instant::now();
            let y = w.synth(s);
            synth.push(t1.elapsed().as_secs_f64());
            assert_eq!(y.len(), x.len(), "{name} {req}: output length");
            write(&format!("{dir}/out/{name}.{req}.native.f64"), &y);
        }
        println!(
            "{{\"input\":\"{name}\",\"seconds\":{},\"analysis_bytes\":{},\"analysis_s\":{analysis},\"synth_s\":{:?}}}",
            x.len() as f64 / e001::FS,
            w.bytes(),
            synth
        );
    }
}
