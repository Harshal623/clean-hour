# Credits

Datasets
- EIA Hourly Electric Grid Monitor (EIA-930): PJM fuel mix, demand and demand forecast, plus Dominion (DOM) zone demand. US government public data. https://www.eia.gov/electricity/gridmonitor/
- Open-Meteo Historical Forecast API (CC BY 4.0). https://open-meteo.com/en/docs/historical-forecast-api
- NOAA CO-OPS Tides and Currents, station 8594900 Washington DC. Used only for a backup-idea feasibility check, not in the final model. https://tidesandcurrents.noaa.gov/
- NASA POWER. Used only in an earlier archived practice project, not in this submission. https://power.larc.nasa.gov/

Emission factors
- IPCC AR5 WG3 Annex III lifecycle emissions (Schlomer et al., 2014): coal 820, gas 490, nuclear 12, hydro 24, solar 41, wind 11 gCO2e/kWh. https://www.ipcc.ch/report/ar5/wg3/
- Our own assumptions, not from that table: oil 650, other fuels 230. Sensitivity in results/ef_sensitivity.csv.

Models and libraries
- scikit-learn HistGradientBoostingRegressor https://scikit-learn.org/ ; pandas; NumPy; Matplotlib; joblib; Gradio https://www.gradio.app/ ; Jupyter/nbconvert.
- No pretrained models.

Briefs
- Veritas AI Hackathon 2026 Project Briefs (AI + Climate track rules: time split, persistence baseline).

AI tools
- Claude Code (Anthropic) assisted with brainstorming, the data loader, evaluation code, the Gradio app and drafting the write-up. The team reviewed the results and can explain every part.
