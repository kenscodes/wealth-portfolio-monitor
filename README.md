# Private Wealth Portfolio Health Monitor

A production-grade portfolio analysis tool that monitors holdings health, benchmarks performance against the S&P 500, surfaces risk signals, and exports structured data for Tableau dashboards.

Built to provide comprehensive portfolio health visibility, combining quantitative rigor with actionable, data-driven insights.

---

## Key Metrics Computed

| # | Metric | Description |
|---|--------|-------------|
| 1 | **Cumulative Returns** | Compounded returns vs SPY benchmark over 2 years |
| 2 | **Sharpe Ratio** | Risk-adjusted return per unit of volatility (annualized) |
| 3 | **Max Drawdown** | Largest peak-to-trough decline — measures downside risk |
| 4 | **Portfolio Beta** | Systematic risk relative to S&P 500 |
| 5 | **Allocation Drift** | Actual vs target sector weights with 5% drift flags |
| 6 | **Portfolio Health Score** | Composite score from normalized Sharpe, drawdown, and drift |

---

## Tools & Technologies

- **Python 3.10+** — core language
- **yfinance** — real-time and historical market data
- **Pandas & NumPy** — data manipulation and quantitative computation
- **Plotly** — interactive charts in Jupyter
- **Matplotlib & Seaborn** — static visualizations (fallback)
- **Tableau** — interactive dashboard visualization

---

## Live Dashboard

[View the interactive Tableau Dashboard here](https://public.tableau.com/app/profile/shashank.kanojiya1043/viz/PWMWealthPortfolioMonitor/PrivateWealthPortfoliohealthMonitor)

---

## Screenshots

![Portfolio Analysis Dashboard](assets/portfolio_analysis.png)

---

## How to Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Analysis Notebook
```bash
jupyter notebook analysis.ipynb
```
Run all cells sequentially. The notebook will:
- Fetch 2 years of market data via yfinance
- Compute all metrics
- Generate interactive Plotly charts
- Export 4 CSVs to the `data/` folder

### 3. Open Tableau Dashboard
1. Open Tableau
2. Import the 4 CSVs from `data/`
3. Connect the data sources to visualize the metrics and allocation drift.

---

## Project Structure

```
wealth-portfolio-monitor/
├── analysis.ipynb         ← main analysis notebook (6 sections)
├── portfolio_config.py    ← portfolio definition & targets
├── metrics.py             ← pure calculation functions (8 functions)
├── export.py              ← CSV export logic (4 exports)
├── data/
│   ├── daily_returns.csv
│   ├── portfolio_summary.csv
│   ├── allocation_drift.csv
│   └── cumulative_returns.csv
├── requirements.txt
└── README.md
```

---

## License

This project is for educational and portfolio demonstration purposes.
