# E6: which workloads can wait? (replaces the uncited sentence in DECISION.md)

Owner: A (HM-Claude), Saturday night. Evidence is weaker than we would like; limits stated.

## Evidence found
- Google's production carbon-aware system delays "temporally flexible" workloads and keeps daily capacity so they finish within a day (Radovanović et al., arXiv 2106.11750, https://arxiv.org/pdf/2106.11750; abstract-level read). This supports 12-24 h of slack for a real share of data-center work, but the paper's savings are not quoted here.
- A survey of measurement-based data-center control reports that in Azure VM traces about 68% of core hours are "delay-insensitive" (batch and internal), about 28% interactive and about 4% uncategorised (https://arxiv.org/pdf/2408.09497, secondary source, not checked against the original trace paper). "Delay-insensitive" is not the same as "has a known deadline with slack", so treat 68% as an upper bound on deferrability.
- Providers rarely publish production traces (privacy, competition), so no public number tells us how much slack typical batch jobs have.

## What we can and cannot say
- Reasonable: some batch and internal work (training chunks, backups, data processing) can tolerate 12-24 h; this is how Google's system works.
- Not supported by anything we found: a specific share of Loudoun's load that is flexible, or that 48-72 h slack is common. Treat our 3-day results as "if a job could wait that long", not a claim about typical jobs.
- Households: EV charging and dishwasher/laundry are deferrable by definition when the user allows it; our app lets the user choose 12 h, 24 h or 3 days.

## Proposed DECISION.md / README wording
"Which jobs can wait is an assumption, not our finding: Google's production system delays flexible work by up to a day, and one survey of Azure traces counts about 68% of core hours as delay-insensitive (an upper bound on deferrable work). We do not know the real share for Loudoun."
