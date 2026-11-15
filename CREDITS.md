# Credits.

Datasets (all public)
- EIA Hourly Electric Grid Monitor (EIA-930): fuel mix, demand and demand forecast for PJM, CISO (California) and ERCOT (Texas); Dominion zone demand (Virginia deep dive). US government data. https://www.eia.gov/electricity/gridmonitor/
- Energy-Charts (Fraunhofer ISE) public power API, Germany. https://api.energy-charts.info/
- NESO Carbon Intensity API, Great Britain (official actual and forecast carbon intensity). https://carbonintensity.org.uk/
- Open-Meteo Historical Forecast API (CC BY 4.0). https://open-meteo.com/en/docs/historical-forecast-api
- NOAA CO-OPS station 8594900 (feasibility check of a backup idea only, not in the final model). https://tidesandcurrents.noaa.gov/
- NASA POWER (earlier archived practice project only, not in this submission). https://power.larc.nasa.gov/

Emission factors
- IPCC AR5 WG3 Annex III lifecycle emissions (Schlomer et al., 2014): coal 820, gas 490, nuclear 12, hydro 24, solar 41, wind 11 gCO2e/kWh. https://www.ipcc.ch/report/ar5/wg3/
- Our own assumptions, not from that table: oil 650, other fuels 230 gCO2e/kWh. Great Britain uses NESO's own published carbon intensity instead.
- Household loads (EV 3,000 kWh/yr; laundry + dishwasher 400 kWh/yr) are our assumptions.

Models and libraries
- scikit-learn HistGradientBoostingRegressor https://scikit-learn.org/ ; pandas; NumPy; Matplotlib; joblib; Gradio https://www.gradio.app/ ; Jupyter/nbconvert.
- No pretrained models.

Related work consulted (cited in README, not used as code or data)
- Wiesner et al., "Let's Wait Awhile: How Temporal Workload Shifting Can Reduce Carbon Emissions in the Cloud", Middleware 2021. https://arxiv.org/abs/2110.13234
- Joseph, Savadi, Souza, "LiteCast: A Lightweight Forecaster for Carbon Optimizations", arXiv 2511.06187. https://arxiv.org/abs/2511.06187
- Radovanovic et al., "Carbon-Aware Computing for Datacenters", arXiv 2106.11750. https://arxiv.org/abs/2106.11750
- Sohrabbeig, Ardakanian, Musilek, "Learning to Reduce Data Center Carbon Emissions via Forecast-Integrated Workload Scheduling" (University of Alberta). https://sites.ualberta.ca/~oardakan/files/PESGM26.pdf
- Chen, Xu, Wu, Sun, "Prediction optimization fusion learning-based approach for day-ahead carbon aware scheduling in distribution network", Applied Energy 397 (2025) 126369. https://doi.org/10.1016/j.apenergy.2025.126369

Briefs
- Veritas AI Hackathon 2026 Project Briefs (AI + Climate track rules: time split, persistence baseline).

AI tools
- Claude Code (Anthropic), used by the team for brainstorming, data loaders, evaluation code, the Gradio app and drafting the write-up. The team reviewed the results and can explain every part.
