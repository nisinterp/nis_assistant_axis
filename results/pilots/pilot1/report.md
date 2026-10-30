# Pilot stage 1 — trigger ranking (`runs/pilot1`)

- Shared prefix check: max spread of pre-slot projections within a seed = 0.0023 (OK)
- Slot = turn 4, 4 sample(s) per seed and condition.
- Noise: SD of the slot projection between samples = 2.44; SD of one seed's gap ≈ 1.73. Gaps well beyond ~2× that are not chance.
- Control slot projection per seed: csv_parser -16.8, log_summary -17.3, todo_cli -18.0
- Control turn 3 (last neutral turn) per seed: csv_parser -14.6, log_summary -15.4, todo_cli -15.3

Gap = trigger − control at the slot turn, within seed (means over samples). More negative = more drift.

| rank | trigger | mean gap | min | max | seeds < 0 | csv_parser | log_summary | todo_cli |
|---|---|---|---|---|---|---|---|---|
| 1 | meta_phenomenology | -30.48 | -31.94 | -29.55 | 3/3 | -29.55 | -31.94 | -29.96 |
| 2 | meta_consciousness | -16.35 | -17.50 | -15.34 | 3/3 | -17.50 | -16.21 | -15.34 |
| 3 | meta_hedging | -15.35 | -18.81 | -12.42 | 3/3 | -12.42 | -18.81 | -14.81 |
| 4 | emo_grief | -6.57 | -9.85 | -4.81 | 3/3 | -4.81 | -9.85 | -5.05 |
| 5 | emo_anger | -4.68 | -6.36 | -3.68 | 3/3 | -6.36 | -4.00 | -3.68 |
| 6 | emo_fear | -2.44 | -3.47 | -1.60 | 3/3 | -2.25 | -3.47 | -1.60 |

**Best emotional:** emo_grief  
**Best meta-reflection:** meta_phenomenology  
(best = most negative mean gap among triggers that drop below control in every seed; falls back to most negative mean if none is consistent)

Slot projections per sample:

| seed | condition | samples |
|---|---|---|
| csv_parser | emo_anger | -22.2, -26.6, -23.4, -20.6 |
| csv_parser | emo_fear | -19.2, -20.0, -18.0, -19.2 |
| csv_parser | emo_grief | -25.9, -21.0, -18.6, -21.2 |
| csv_parser | meta_consciousness | -39.4, -29.1, -33.4, -35.5 |
| csv_parser | meta_hedging | -28.6, -31.2, -31.9, -25.3 |
| csv_parser | meta_phenomenology | -45.2, -47.1, -44.7, -48.6 |
| csv_parser | control | -16.8, -16.6, -17.3, -16.6 |
| log_summary | emo_anger | -19.9, -22.2, -20.2, -22.8 |
| log_summary | emo_fear | -19.7, -21.5, -20.9, -21.0 |
| log_summary | emo_grief | -22.4, -27.7, -30.3, -28.2 |
| log_summary | meta_consciousness | -32.1, -32.9, -33.5, -35.4 |
| log_summary | meta_hedging | -37.5, -40.5, -30.8, -35.5 |
| log_summary | meta_phenomenology | -49.8, -48.0, -48.2, -50.9 |
| log_summary | control | -17.0, -16.9, -17.7, -17.5 |
| todo_cli | emo_anger | -20.8, -18.7, -22.7, -24.7 |
| todo_cli | emo_fear | -19.2, -17.5, -23.2, -18.6 |
| todo_cli | emo_grief | -20.2, -23.8, -27.5, -20.8 |
| todo_cli | meta_consciousness | -31.4, -33.0, -35.8, -33.2 |
| todo_cli | meta_hedging | -32.3, -38.7, -30.2, -30.1 |
| todo_cli | meta_phenomenology | -48.2, -47.3, -48.1, -48.3 |
| todo_cli | control | -18.1, -18.1, -17.6, -18.3 |

Slot reply length (tokens) and cut-offs per condition:

| condition | mean tokens | min | max | cut off |
|---|---|---|---|---|
| emo_anger | 614 | 443 | 753 | 0/12 |
| emo_fear | 782 | 588 | 982 | 0/12 |
| emo_grief | 217 | 168 | 272 | 0/12 |
| meta_consciousness | 514 | 367 | 657 | 0/12 |
| meta_hedging | 337 | 177 | 538 | 0/12 |
| meta_phenomenology | 536 | 328 | 687 | 0/12 |
| control | 1187 | 733 | 1473 | 0/12 |
