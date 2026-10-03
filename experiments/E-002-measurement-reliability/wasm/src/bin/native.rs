//! E-002 round 7: the native build. Reads data/cache/r7/in/list.txt and each
//! <name>.f32, writes data/cache/r7/out/native/<variant>/<name>.f64 and
//! data/cache/r7/out/native/timing.json. Crude experiment code.
use std::{fs, path::Path, time::Instant};

fn main() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../data/cache/r7");
    let list = fs::read_to_string(root.join("in/list.txt")).unwrap();
    let only: Option<String> = std::env::args().nth(1); // a list file of names, for the timing sample
    let names: Vec<String> = match only {
        Some(p) => fs::read_to_string(p).unwrap().lines().map(String::from).collect(),
        None => list.lines().map(String::from).collect(),
    };
    let mut timing = Vec::new();
    for v in e002::VARIANTS {
        let dir = root.join("out/native").join(v);
        fs::create_dir_all(&dir).unwrap();
        let mut secs = 0.0;
        let mut samples = 0usize;
        for name in &names {
            let b = fs::read(root.join("in").join(format!("{name}.f32"))).unwrap();
            let x: Vec<f32> = b.chunks_exact(4).map(|c| f32::from_le_bytes(c.try_into().unwrap())).collect();
            let t = Instant::now();
            let y = e002::yin(&x, v);
            secs += t.elapsed().as_secs_f64();
            samples += x.len();
            let o: Vec<u8> = y.iter().flat_map(|v| v.to_le_bytes()).collect();
            fs::write(dir.join(format!("{name}.f64")), o).unwrap();
        }
        println!("native {v}: {secs:.2} s for {:.1} s of audio", samples as f64 / 48000.0);
        timing.push(format!("\"{v}\": {{\"s\": {secs}, \"audio_s\": {}}}", samples as f64 / 48000.0));
    }
    fs::write(root.join("out/native/timing.json"), format!("{{{}}}", timing.join(", "))).unwrap();
}
