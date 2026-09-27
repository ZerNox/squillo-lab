# Data sources

| Data | Source | Licence | Committed |
| :--- | :--- | :--- | :--- |
| 159 VocalSet files, listed in `vocalset-files.txt`: `long_tones/{straight,forte,pp,messa}/*_a.wav` (20 singers each), `arpeggios/vibrato/*_a.wav` (19), `excerpts/vibrato/*row*.wav` (20), `scales/breathy/*_a.wav` (20), `scales/straight/*_a.wav` (20) | VocalSet 1.1: Wilkins, Seetharaman, Wahl and Pardo (2018), *VocalSet: A Singing Voice Dataset*, ISMIR 2018; Zenodo record 1442513, `VocalSet11.zip`, doi:10.5281/zenodo.1442513 | CC BY 4.0 (Zenodo record metadata) | No. `fetch.py` reads the members by HTTP range requests into `data/cache/`, which is ignored |
| Their WORLD re-syntheses and the noise, rooms and results derived from them | `r2_truth.py`, `r2_run.py`, seeds in the code | Derived from the above | No; regenerated into `data/cache/` |
| Round 1's synthetic tones | `run.py`, seed 20260925 | Ours | No; regenerated |

The VocalSet items are long tones, scales and arpeggios on the vowel /a/, and
the traditional round "Row, row, row your boat" (a 19th-century nursery song
in the public domain). Two files carry no singer prefix in their name
(`female4/.../scales_straight_a.wav`, `male10/.../row_vibrato.wav`); the
singer is taken from the zip path. No copyrighted lyrics or melodies are used
or committed.
