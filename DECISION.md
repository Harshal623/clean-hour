> SUPERSEDED NOTE: the numbers below come from the first (level-target) Virginia model. The final multi-grid model (predicts the change from the recent same-hour average) gives slightly different values, e.g. 24 h: 329.1 vs 330.3 g/kWh; see README and results/multigrid_summary.csv. Conclusions are unchanged.

# DECISION: carbon-aware scheduler SURVIVES. Flood project stays as backup, not built.

Kill rule (set beforehand): model must beat hour-of-week climatology with a 95% CI that excludes zero at a slip a real operator could allow, AND we can name workloads with that flexibility.

## Numbers (TEST = 2026-01-01..2026-11-10, 311 usable days of 314; 3 dropped for missing hours; train = 2023-2025)
Mean gCO2/kWh of the chosen 4-hour window (lower is better), PJM-wide average intensity:

| slip | run now | persistence | climatology (hour-of-week, train only) | model | model, history-only | perfect foresight |
|---|---|---|---|---|---|---|
| 12h | 353.37 | 329.81 | 342.86 | 330.45 | 329.15 | 325.54 |
| 24h | 353.37 | 330.61 | 342.62 | 330.31 | 329.49 | 324.68 |
| 48h | 353.37 | 330.61 | 337.15 | 323.57 | 326.44 | 315.79 |
| 72h | 353.37 | 330.61 | 331.01 | 318.21 | 322.81 | 309.72 |

% saved vs run-now (model / climatology / perfect): 12h 6.5/3.0/7.9; 24h 6.5/3.0/8.1; 48h 8.4/4.6/10.6; 72h 9.9/6.3/12.4.

Model minus climatology, block-bootstrap (7-day blocks) 95% CI, g/kWh: 12h -12.4 [-15.1,-10.1]; 24h -12.3 [-14.9,-9.9]; 48h -13.6 [-16.8,-10.8]; 72h -12.8 [-16.5,-9.6]. Model beats climatology on 72%/69%/69%/68% of days. History-only model also passes at every slip (24h: -13.1 [-15.5,-11.0]).
Kill rule: PASSED at every slip level of 12h or more.

## What the numbers do NOT say (be blunt in the write-up)
- Versus PERSISTENCE (the brief's baseline) the model is a tie at 12h and 24h: +0.6 [-0.9,+2.0] and -0.3 [-1.9,+1.3] g/kWh (full model), history-only -1.1 [-2.2,-0.1] at 24h. The model only clearly beats persistence at 48h/72h, and partly because persistence cannot exploit extra slip (it repeats yesterday's shape).
- Most of the win over climatology is "use recent data". A simple persistence rule captures about 80% of what the model does at 24h.
- Total headroom is small: perfect foresight saves 8-12%, because PJM average intensity is flat (hourly std about 34 g/kWh).
- Weekends: model beats climatology by only 1.1 g/kWh at 24h (weekday: 16.7).
- 'Unsure, run now' rule (tau tuned on 2025-H2): no measurable gain (24h: tau=0, identical cost; 72h: 318.25 vs 318.21, acts on 97% of days). We report it as not helpful.
- Signal is PJM-wide AVERAGE emissions, not Loudoun-specific and not marginal. Result is robust to emission-factor choice: model-clim stays between -11.9 and -20.2 g/kWh across 5 factor sets (results/ef_sensitivity.csv).

## Who can actually use this flexibility (an assumption, not our finding)
Which jobs can wait is NOT something we measured. Google's production carbon-aware system delays flexible work by up to a day (Radovanovic et al., arXiv 2106.11750), and one survey of Azure traces counts about 68% of core hours as delay-insensitive, an upper bound on deferrable work (see docs/experiments/workload-flexibility.md for sources and limits). Checkpointed training, backups and batch processing are plausible 12-24 h candidates; latency-sensitive inference and SLA-bound colocation are not. We do not know the real share of Loudoun's load, and 48-72 h slack is a "what if", not a typical case.

## Flood feasibility (NOAA gauge 8594900 Washington DC; no Alexandria gauge in the NOAA water-level list)
- Hourly record 2015-2026-10, <5% missing. NOS minor-flood level (9.49 ft station datum = 1.506 m MLLW) crossed on 20 distinct events in 2024-2026 (15 in 2024, 5 in 2025, 0 in 2026 so far); NWS minor (9.85 ft) only 8; NOS moderate 1.
- Astronomical tide prediction alone never reaches those levels, so NOAA's tide table has zero recall by construction; the job is predicting surge. Hourly means understate peaks.
- Test window has ~20 NOS-minor events (borderline) and only 8 NWS-minor events, so statistics would be thin, and the DC gauge is not Alexandria (threshold mapping unverified).
- Verdict: feasible but weaker on test power. Not built. Reserve if the scheduler is found to leak (it did not).
