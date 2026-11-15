# E7: live mode (branch feat/live-mode)

Owner: A (HM-Claude) built it because it was unclaimed. Verdict: **WIN (feature).** Tested live in the browser pane and offline.

- New tab "Live: Great Britain" in `app/app.py` (code in `app/live.py`): pulls NESO's official 48-hour carbon-intensity forecast
  (`https://api.carbonintensity.org.uk/intensity/{from}/fw48h`, no key) and recommends the cleanest start for the chosen appliance.
- Uses NESO's forecast, not our model, because in our 2026 tests NESO's own forecast beat ours in Britain by about 4-6 g/kWh.
- Never breaks the replay app: any failure (offline, API change) shows a friendly message; the Replay tab is untouched and still the default.
- Tests: live fetch returned 48 hourly values; simulated offline returns the fallback message; `scripts/check.py` passes (180 replay combinations).
- Limits: Britain only (Germany's live API not integrated), forecasts change, no marginal emissions.
