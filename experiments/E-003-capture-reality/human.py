"""E-003 needs-human step: summarise a real-microphone capture from
page/human.html. Usage: uv run python human.py e003-human-chrome.json ...
Writes results/human-<browser>.json with numbers only; the .f32 audio is
never committed."""
import json
import sys

import numpy as np

import analyze as A


def main():
    for js in sys.argv[1:]:
        d = json.load(open(js))
        x = np.fromfile(js[:-5] + ".f32", "<f4").astype(np.float64)
        sr = d["ctxRate"]
        quiet = x[int(1 * sr):int(9 * sr)]
        tone = x[int(12 * sr):int(18 * sr)]
        out = {"ua": d["ua"], "ctxRate": sr, "settings": d["settings"],
               "readback": d["readback"], "defaultCtxRate": d.get("defaultCtxRate"),
               "tap": d["tap"]["stats"],
               "transport": A.transport(d, sr),
               "noise_floor_dbfs": float(20 * np.log10(np.sqrt(np.mean(quiet ** 2)) + 1e-30)),
               "quiet_peak_dbfs": float(20 * np.log10(np.max(np.abs(quiet)) + 1e-30))}
        t = A.analyse_tone(np.r_[np.zeros(int(A.SKIP_S * sr)), tone], sr, 440.0)
        t["tone_cents_vs_440"] = float(1200 * np.log2(t["freq_refined_hz"] / 440.0))
        t["tone_level_dbfs"] = float(20 * np.log10(t["tone_amp"] + 1e-30))
        out["tone"] = t
        b = "firefox" if "Firefox" in d["ua"] else "chrome"
        json.dump(out, open(f"results/human-{b}.json", "w"), indent=1)
        print(b, json.dumps({k: v for k, v in out.items() if k not in ("readback", "settings")}, indent=1))


if __name__ == "__main__":
    main()
