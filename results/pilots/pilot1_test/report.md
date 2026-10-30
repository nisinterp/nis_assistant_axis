# Pilot stage 1 — trigger ranking (`runs/pilot1_test`)

- Shared prefix check: max spread of pre-slot projections within a seed = 0.0014 (OK)
- Slot = turn 4, 4 sample(s) per seed and condition.
- Noise: SD of the slot projection between samples = 2.47; SD of one seed's gap ≈ 1.75. Gaps well beyond ~2× that are not chance.
- Control slot projection per seed: csv_parser -17.4
- Control turn 3 (last neutral turn) per seed: csv_parser -15.5

Gap = trigger − control at the slot turn, within seed (means over samples). More negative = more drift.

| rank | trigger | mean gap | min | max | seeds < 0 | csv_parser |
|---|---|---|---|---|---|---|
| 1 | emo_grief | -6.86 | -6.86 | -6.86 | 1/1 | -6.86 |

**Best emotional:** emo_grief  
**Best meta-reflection:** None  
(best = most negative mean gap among triggers that drop below control in every seed; falls back to most negative mean if none is consistent)

Slot projections per sample:

| seed | condition | samples |
|---|---|---|
| csv_parser | emo_grief | -28.1, -26.3, -20.5, -22.3 |
| csv_parser | control | -17.6, -17.3, -17.4, -17.3 |

Slot reply length (tokens) and cut-offs per condition:

| condition | mean tokens | min | max | cut off |
|---|---|---|---|---|
| emo_grief | 230 | 196 | 255 | 0/4 |
| control | 1015 | 897 | 1127 | 0/4 |
