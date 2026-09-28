# E-001 round 2: WORLD and a crude PSOLA in WASM

Inputs: 8 (bass_plain_1 4.05 s, tenor_plain_1 4.05 s, soprano_high_plain_1 4.05 s, f1 11.43 s, f5 9.12 s, f9 7.79 s, m1 16.77 s, m8 8.47 s); one thread; best of 3.
Browsers: chrome 154.0.8037.57, cross-origin isolated True; chrome-simd 154.0.8037.57, cross-origin isolated True; firefox 156.0, cross-origin isolated True; firefox-simd 156.0, cross-origin isolated True

## Seconds of processing per second of audio (analysis + one c100 re-synthesis)

| Environment | harvest median (min-max) | dio median (min-max) | psola median (min-max) |
| :--- | ---: | ---: | ---: |
| round1-native | 0.290 (0.269-0.307) | 0.154 (0.141-0.171) | 0.034 (0.031-0.041) |
| native | 0.227 (0.200-0.237) | 0.089 (0.084-0.094) | 0.004 (0.004-0.004) |
| chrome | 0.382 (0.336-0.400) | 0.163 (0.152-0.183) | 0.007 (0.007-0.008) |
| chrome-simd | 0.365 (0.325-0.385) | 0.152 (0.145-0.176) | 0.007 (0.007-0.008) |
| firefox | 0.362 (0.323-0.385) | 0.140 (0.131-0.161) | 0.007 (0.007-0.008) |
| firefox-simd | 0.354 (0.311-0.368) | 0.136 (0.128-0.156) | 0.007 (0.007-0.009) |

`round1-native`: pyworld (C++ WORLD) and Praat through parselmouth, round 1's `timing.json`.
`native`: this crate (world-rs and the crude PSOLA) as x86-64 native code.

## Stage medians, s per s of audio

- native harvest: f0 (Harvest) 0.150, envelope (CheapTrick) 0.011, aperiodicity (D4C) 0.043, synthesis 0.020
- native dio: f0 (DIO + StoneMask) 0.013, envelope (CheapTrick) 0.011, aperiodicity (D4C) 0.044, synthesis 0.020
- native psola: pitch 0.003, marks 0.000, overlap-add 0.001
- chrome harvest: f0 (Harvest) 0.240, envelope (CheapTrick) 0.019, aperiodicity (D4C) 0.081, synthesis 0.039
- chrome dio: f0 (DIO + StoneMask) 0.019, envelope (CheapTrick) 0.019, aperiodicity (D4C) 0.081, synthesis 0.039
- chrome psola: pitch 0.007, marks 0.000, overlap-add 0.001
- chrome-simd harvest: f0 (Harvest) 0.230, envelope (CheapTrick) 0.018, aperiodicity (D4C) 0.076, synthesis 0.038
- chrome-simd dio: f0 (DIO + StoneMask) 0.019, envelope (CheapTrick) 0.018, aperiodicity (D4C) 0.077, synthesis 0.038
- chrome-simd psola: pitch 0.007, marks 0.000, overlap-add 0.001
- firefox harvest: f0 (Harvest) 0.237, envelope (CheapTrick) 0.016, aperiodicity (D4C) 0.067, synthesis 0.037
- firefox dio: f0 (DIO + StoneMask) 0.019, envelope (CheapTrick) 0.016, aperiodicity (D4C) 0.068, synthesis 0.037
- firefox psola: pitch 0.006, marks 0.000, overlap-add 0.001
- firefox-simd harvest: f0 (Harvest) 0.235, envelope (CheapTrick) 0.016, aperiodicity (D4C) 0.063, synthesis 0.036
- firefox-simd dio: f0 (DIO + StoneMask) 0.018, envelope (CheapTrick) 0.016, aperiodicity (D4C) 0.064, synthesis 0.036
- firefox-simd psola: pitch 0.006, marks 0.000, overlap-add 0.001

## WASM time / native time, per input

- chrome/harvest: median 1.69 (1.67-1.75)
- chrome/dio: median 1.81 (1.76-1.96)
- chrome/psola: median 1.90 (1.84-2.09)
- chrome-simd/harvest: median 1.63 (1.60-1.65)
- chrome-simd/dio: median 1.74 (1.67-1.87)
- chrome-simd/psola: median 1.90 (1.86-2.00)
- firefox/harvest: median 1.61 (1.58-1.64)
- firefox/dio: median 1.59 (1.51-1.71)
- firefox/psola: median 1.82 (1.76-1.99)
- firefox-simd/harvest: median 1.56 (1.55-1.60)
- firefox-simd/dio: median 1.53 (1.48-1.66)
- firefox-simd/psola: median 1.92 (1.85-2.07)

## Repeats: (slowest / fastest of 3) - 1, per input; and the first repeat over the best

- chrome/harvest: median 0.020, max 0.165; first over best, max 0.165
- chrome/dio: median 0.015, max 0.049; first over best, max 0.039
- chrome/psola: median 0.045, max 0.208; first over best, max 0.208
- chrome-simd/harvest: median 0.005, max 0.181; first over best, max 0.181
- chrome-simd/dio: median 0.014, max 0.058; first over best, max 0.058
- chrome-simd/psola: median 0.023, max 0.205; first over best, max 0.205
- firefox/harvest: median 0.010, max 0.224; first over best, max 0.224
- firefox/dio: median 0.015, max 0.062; first over best, max 0.062
- firefox/psola: median 0.012, max 0.192; first over best, max 0.192
- firefox-simd/harvest: median 0.008, max 0.266; first over best, max 0.266
- firefox-simd/dio: median 0.007, max 0.063; first over best, max 0.063
- firefox-simd/psola: median 0.021, max 0.104; first over best, max 0.104

## Bytes the WORLD analysis holds (samples, f0, envelope, aperiodicity; f64), per second of audio, median

- chrome/harvest: 3.67 MB/s
- chrome/dio: 3.67 MB/s
- chrome-simd/harvest: 3.67 MB/s
- chrome-simd/dio: 3.67 MB/s
- firefox/harvest: 3.67 MB/s
- firefox/dio: 3.67 MB/s
- firefox-simd/harvest: 3.67 MB/s
- firefox-simd/dio: 3.67 MB/s

## Numerics

- chrome/harvest: {'bit_identical_to_native': 0, 'max_abs_diff': 2.6567942290611768e-11, 'min_native_peak': 0.48218841731067635}
- chrome/dio: {'bit_identical_to_native': 0, 'max_abs_diff': 5.846680778409663e-12, 'min_native_peak': 0.47197539485114176}
- chrome/psola: {'bit_identical_to_native': 0, 'max_abs_diff': 1.1102230246251565e-16, 'min_native_peak': 0.4902625414398136}
- chrome-simd/harvest: {'bit_identical_to_native': 0, 'max_abs_diff': 2.6567942290611768e-11, 'min_native_peak': 0.48218841731067635}
- chrome-simd/dio: {'bit_identical_to_native': 0, 'max_abs_diff': 5.846680778409663e-12, 'min_native_peak': 0.47197539485114176}
- chrome-simd/psola: {'bit_identical_to_native': 0, 'max_abs_diff': 1.1102230246251565e-16, 'min_native_peak': 0.4902625414398136}
- firefox/harvest: {'bit_identical_to_native': 0, 'max_abs_diff': 2.6567942290611768e-11, 'min_native_peak': 0.48218841731067635}
- firefox/dio: {'bit_identical_to_native': 0, 'max_abs_diff': 5.846680778409663e-12, 'min_native_peak': 0.47197539485114176}
- firefox/psola: {'bit_identical_to_native': 0, 'max_abs_diff': 1.1102230246251565e-16, 'min_native_peak': 0.4902625414398136}
- firefox-simd/harvest: {'bit_identical_to_native': 0, 'max_abs_diff': 2.6567942290611768e-11, 'min_native_peak': 0.48218841731067635}
- firefox-simd/dio: {'bit_identical_to_native': 0, 'max_abs_diff': 5.846680778409663e-12, 'min_native_peak': 0.47197539485114176}
- firefox-simd/psola: {'bit_identical_to_native': 0, 'max_abs_diff': 1.1102230246251565e-16, 'min_native_peak': 0.4902625414398136}
- hash_sets_over_4_wasm_envs: [1]

## WASM linear memory, high-water mark over the run (MiB)

- chrome: 221
- chrome-simd: 221
- firefox: 221
- firefox-simd: 221

## Check (r2_check.py, native outputs, all 43 inputs)

```
{
 "equiv": {
  "synthetic/harvest": {
   "voicing_agree_min": 1.0,
   "voicing_agree_median": 1.0,
   "f0_p99_max": 0.21247867402008436,
   "f0_max": 0.33046989982821334,
   "f0_over1_max": 0.0,
   "snr_min": 38.63022805487137,
   "snr_median": 47.42219166910579
  },
  "synthetic/dio": {
   "voicing_agree_min": 1.0,
   "voicing_agree_median": 1.0,
   "f0_p99_max": 7.688223609155805e-13,
   "f0_max": 1.5376447218311597e-12,
   "f0_over1_max": 0.0,
   "snr_min": 36.479776603691015,
   "snr_median": 51.89094460575991
  },
  "vocalset/harvest": {
   "voicing_agree_min": 0.9826812059012188,
   "voicing_agree_median": 1.0,
   "f0_p99_max": 119.88192649784274,
   "f0_max": 2199.5579182395086,
   "f0_over1_max": 0.02321262766945218,
   "snr_min": -5.293600141716615,
   "snr_median": 43.275872818163265
  },
  "vocalset/dio": {
   "voicing_agree_min": 1.0,
   "voicing_agree_median": 1.0,
   "f0_p99_max": 7.688223609155805e-13,
   "f0_max": 3.8575661958943537e-10,
   "f0_over1_max": 0.0,
   "snr_min": 85.12171252303303,
   "snr_median": 96.59799564170216
  }
 },
 "pass_case": {
  "synthetic/harvest/c100": {
   "frames": 11497,
   "kept": 0.969758064516129,
   "achieved_fraction": 0.9974913657821872,
   "fine_p95": 3.4978470600075826,
   "gross": 0.0029572932069235453
  },
  "synthetic/harvest/s100": {
   "frames": 11516,
   "kept": 0.9710181451612904,
   "achieved_fraction": 0.9944611026108965,
   "fine_p95": 3.769105302643111,
   "gross": 0.027526919069121223
  },
  "synthetic/dio/c100": {
   "frames": 11481,
   "kept": 0.9671538978494624,
   "achieved_fraction": 0.9984256255744386,
   "fine_p95": 3.331483784828426,
   "gross": 0.0025259123769706474
  },
  "synthetic/dio/s100": {
   "frames": 11496,
   "kept": 0.9684979838709677,
   "achieved_fraction": 0.9941324146189479,
   "fine_p95": 3.36239126855817,
   "gross": 0.028270702853166317
  },
  "vocalset/harvest/c100": {
   "frames": 21964,
   "kept": 0.9968623935454953,
   "achieved_fraction": 0.9950991548948226,
   "fine_p95": 4.542199964011383,
   "gross": 0.025450737570570023
  },
  "vocalset/harvest/s100": {
   "frames": 22030,
   "kept": 1.002061855670103,
   "achieved_fraction": 0.9789373822850791,
   "fine_p95": 4.618093977766907,
   "gross": 0.02628234226055379
  },
  "vocalset/dio/c100": {
   "frames": 21939,
   "kept": 0.994621246077992,
   "achieved_fraction": 0.9949516203288478,
   "fine_p95": 4.547959983930226,
   "gross": 0.02529741556132914
  },
  "vocalset/dio/s100": {
   "frames": 22004,
   "kept": 0.9995517705064993,
   "achieved_fraction": 0.9779851937883484,
   "fine_p95": 4.516662810680985,
   "gross": 0.02613161243410289
  }
 },
 "fail_case": {
  "synthetic/harvest": {
   "frames": 11527,
   "kept": 0.9710181451612904,
   "achieved_fraction": -0.0001378861094893336,
   "fine_p95": 47.31466475892494,
   "gross": 0.02949596599288627
  },
  "synthetic/dio": {
   "frames": 11508,
   "kept": 0.9688340053763441,
   "achieved_fraction": 0.0010825541524070316,
   "fine_p95": 47.41549286820275,
   "gross": 0.030500521376433786
  },
  "synthetic/psola": {
   "frames": 11780,
   "kept": 0.9940356182795699,
   "achieved_fraction": -0.012697280711550012,
   "fine_p95": 46.693798753448085,
   "gross": 0.02937181663837012
  },
  "vocalset/harvest": {
   "frames": 22024,
   "kept": 1.0002241147467503,
   "achieved_fraction": 0.0033541142003789535,
   "fine_p95": 43.92446423602242,
   "gross": 0.02842353795859063
  },
  "vocalset/dio": {
   "frames": 22000,
   "kept": 0.996683101748095,
   "achieved_fraction": 0.0026508693987235057,
   "fine_p95": 43.96330184260964,
   "gross": 0.028454545454545455
  },
  "vocalset/psola": {
   "frames": 21254,
   "kept": 0.9554011653966831,
   "achieved_fraction": 0.019188017080796583,
   "fine_p95": 44.357100404895675,
   "gross": 0.02804178037075374
  }
 },
 "rows": {
  "synthetic/harvest/c100": {
   "frames": 11497,
   "kept": 0.969758064516129,
   "achieved_fraction": 0.9974895175473412,
   "fine_p95": 3.4978421459637388,
   "gross": 0.0029572932069235453,
   "lt_env_median": 0.6581047355807426,
   "lt_env_max": 1.646075489668687
  },
  "synthetic/harvest/s100": {
   "frames": 11516,
   "kept": 0.9710181451612904,
   "achieved_fraction": 0.9944564211353254,
   "fine_p95": 3.769036834749276,
   "gross": 0.02744008336227857,
   "lt_env_median": 0.7062541596640043,
   "lt_env_max": 1.3567087289160549
  },
  "synthetic/dio/c100": {
   "frames": 11481,
   "kept": 0.9671538978494624,
   "achieved_fraction": 0.9984255971396891,
   "fine_p95": 3.3314837848304526,
   "gross": 0.0025259123769706474,
   "lt_env_median": 0.6578141577836729,
   "lt_env_max": 1.6407679267978756
  },
  "synthetic/dio/s100": {
   "frames": 11496,
   "kept": 0.9684979838709677,
   "achieved_fraction": 0.9941324146064465,
   "fine_p95": 3.36239126855817,
   "gross": 0.028270702853166317,
   "lt_env_median": 0.7068996866710229,
   "lt_env_max": 1.3460635926715052
  },
  "synthetic/psola/c100": {
   "frames": 11760,
   "kept": 0.9918514784946236,
   "achieved_fraction": 0.9793250733698275,
   "fine_p95": 9.473501470580075,
   "gross": 0.00042517006802721087,
   "lt_env_median": 0.409653199231102,
   "lt_env_max": 1.1083097547417673
  },
  "synthetic/psola/s100": {
   "frames": 11754,
   "kept": 0.9923555107526881,
   "achieved_fraction": 1.0411358179665884,
   "fine_p95": 9.567592541496392,
   "gross": 0.00025523226135783564,
   "lt_env_median": 0.09155406697348023,
   "lt_env_max": 0.3166077146518092
  },
  "vocalset/harvest/c100": {
   "frames": 21955,
   "kept": 0.9971313312415957,
   "achieved_fraction": 0.9949296528581533,
   "fine_p95": 4.575589298291472,
   "gross": 0.025370075153723526,
   "lt_env_median": 0.7080658443890655,
   "lt_env_max": 1.4827468673532191
  },
  "vocalset/harvest/s100": {
   "frames": 22030,
   "kept": 1.0023756163155535,
   "achieved_fraction": 0.9790229133125475,
   "fine_p95": 4.532223304179129,
   "gross": 0.026236949614162505,
   "lt_env_median": 0.6474557034425742,
   "lt_env_max": 1.5873609490575897
  },
  "vocalset/dio/c100": {
   "frames": 21939,
   "kept": 0.994621246077992,
   "achieved_fraction": 0.994951620328856,
   "fine_p95": 4.5479599839297675,
   "gross": 0.02529741556132914,
   "lt_env_median": 0.6949686949685278,
   "lt_env_max": 1.3543258897257988
  },
  "vocalset/dio/s100": {
   "frames": 22004,
   "kept": 0.9995517705064993,
   "achieved_fraction": 0.9779851937883419,
   "fine_p95": 4.516662810680296,
   "gross": 0.02613161243410289,
   "lt_env_median": 0.6962741568196479,
   "lt_env_max": 1.30002552521623
  },
  "vocalset/psola/c100": {
   "frames": 21131,
   "kept": 0.9504258180188256,
   "achieved_fraction": 0.9839181768989319,
   "fine_p95": 16.964729690422523,
   "gross": 0.006010127301121575,
   "lt_env_median": 0.41609354620173455,
   "lt_env_max": 0.9283239489634985
  },
  "vocalset/psola/s100": {
   "frames": 21273,
   "kept": 0.9571940833706858,
   "achieved_fraction": 0.9574645538843038,
   "fine_p95": 16.37590199357036,
   "gross": 0.005923000987166831,
   "lt_env_median": 0.29123695395329513,
   "lt_env_max": 0.536175932941981
  }
 }
}
```
