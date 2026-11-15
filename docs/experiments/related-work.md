# E5: related work (verified against the sources' own abstracts where marked)

Owner: A (HM-Claude) wrote this Saturday night because it was unclaimed; C may extend it. Status of each source is stated honestly.

| Work | What it claims | Checked how | How ours differs |
|---|---|---|---|
| Wiesner et al., "Let's Wait Awhile: How Temporal Workload Shifting Can Reduce Carbon Emissions in the Cloud", Middleware 2021, https://arxiv.org/abs/2110.13234 | Analyses the potential of shifting flexible workloads in time in Germany, Great Britain, France and California (2020); runs scenarios to see how time constraints, scheduling strategy and forecast accuracy matter. Abstract gives no savings number. | Abstract opened | We use 2023-2026 data, a strictly later held-out test year, simple baselines with intervals, a household framing, and a Virginia focus. We do not claim temporal shifting as new. |
| Joseph, Savadi, Souza, "LiteCast: A Lightweight Forecaster for Carbon Optimizations", arXiv 2511.06187 (v2, Nov 2025) | Savings depend on ranking of hours more than forecast error; across 50 regions a lightweight forecaster reportedly gets 20% more savings than state-of-the-art forecasters and 97% of the attainable maximum. | Abstract opened | Our "better forecast is not a better choice" observation is consistent with this and is not new. Our additions: a held-out 2026 test, and the boundary condition that ranking-focused training helped only in the flattest grid (E1). |
| Radovanović et al., "Carbon-Aware Computing for Datacenters", arXiv 2106.11750 (Google) | Describes a production system that sets hourly capacity limits for flexible workloads from next-day carbon-intensity forecasts and day-ahead demand, keeping total daily capacity so flexible work finishes within a day. | Search result summary (abstract level), not the full paper | Same decision (shift flexible work using a day-ahead forecast); ours is a public-data, open reimplementation-style study with baselines, plus households. |
| Decision-focused carbon forecasting for data-center job placement (PESGM 2026, https://sites.ualberta.ca/~oardakan/files/PESGM26.pdf) and Chen et al., Applied Energy 2025 (prediction-optimization fusion for carbon-aware shiftable load) | Reportedly: higher forecast accuracy does not necessarily give lower emissions; decision-focused training can help. | NOT opened (search snippets only); do not cite claims beyond this until read | Our E1 tests a simple decision-focused second stage across five grids and finds the benefit is not universal. |

## Proposed README paragraph
Already in README "Related work". If C verifies the last row by opening the papers, add them there.

## What is genuinely ours (say it modestly)
Public data only; five grids with one primary region (Northern Virginia); strictly later held-out test with four baselines and block-bootstrap intervals;
negative and mixed results kept (E1-E4); a household-facing tool. None of the underlying ideas (temporal shifting, ranking over error) is new.
