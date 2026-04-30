"""Generate the analysis.ipynb notebook programmatically."""
import json

def md(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.split('\n')}

def code(source):
    return {"cell_type": "code", "metadata": {}, "source": source.split('\n'), "outputs": [], "execution_count": None}

cells = []

cells.append(md("# Private Wealth Portfolio Health Monitor\n\n**A Goldman Sachs–grade portfolio analysis tool** — benchmarking against S&P 500, surfacing risk signals, and exporting structured data for Power BI dashboards.\n\n---"))

cells.append(md("## Section 1 — Setup & Data Fetch"))

cells.append(code("""# Standard libraries
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns

# Project modules
from portfolio_config import PORTFOLIO, TARGET_ALLOCATION, BENCHMARK_TICKER, ANALYSIS_PERIOD, RISK_FREE_RATE
from metrics import (
    fetch_price_data,
    calculate_daily_returns,
    calculate_cumulative_returns,
    calculate_portfolio_value,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_allocation_drift,
    calculate_portfolio_beta,
    compute_portfolio_returns,
)
from export import (
    export_daily_returns,
    export_portfolio_summary,
    export_allocation_drift,
    export_cumulative_returns,
)

# Plotly dark theme
import plotly.io as pio
pio.templates.default = 'plotly_dark'

print(" All modules loaded successfully")"""))

cells.append(code("""# Fetch 2 years of adjusted close prices
tickers = list(PORTFOLIO.keys())
price_data = fetch_price_data(tickers, ANALYSIS_PERIOD, BENCHMARK_TICKER)

# Summary
print(f" Date Range: {price_data.index[0].strftime('%Y-%m-%d')} → {price_data.index[-1].strftime('%Y-%m-%d')}")
print(f" Trading Days: {len(price_data):,}")
print(f" Tickers Loaded: {', '.join(price_data.columns.tolist())}")
print(f" Benchmark: {BENCHMARK_TICKER}")

price_data.tail()"""))

cells.append(md("---\n## Section 2 — Portfolio Snapshot"))

cells.append(code("""# Calculate current portfolio value
pv = calculate_portfolio_value(price_data, PORTFOLIO)
holdings = pv['holdings']
weights = pv['weights']
total_value = pv['total_value']

print(f" Total Portfolio Value: ${total_value:,.2f}")
print()
holdings.style.format({
    'purchase_price': '${:,.2f}',
    'current_price': '${:,.2f}',
    'current_value': '${:,.2f}',
    'cost_basis': '${:,.2f}',
    'total_return_pct': '{:+.2f}%',
    'weight_pct': '{:.2f}%',
}).set_caption(" Portfolio Holdings")"""))

cells.append(code("""# Bar Chart — Current Value per Holding
colors = px.colors.qualitative.Set2

fig = go.Figure(
    data=[go.Bar(
        x=holdings['ticker'],
        y=holdings['current_value'],
        text=holdings['current_value'].apply(lambda x: f'${x:,.0f}'),
        textposition='outside',
        marker=dict(
            color=colors[:len(holdings)],
            line=dict(color='rgba(255,255,255,0.3)', width=1)
        ),
        hovertemplate='<b>%{x}</b><br>Value: $%{y:,.2f}<br>Weight: %{customdata:.1f}%<extra></extra>',
        customdata=holdings['weight_pct'],
    )]
)
fig.update_layout(
 title=dict(text=' Current Value per Holding', font=dict(size=20)),
    xaxis_title='Ticker',
    yaxis_title='Value ($)',
    yaxis=dict(tickformat='$,.0f'),
    height=500,
    showlegend=False,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)
fig.show()"""))

cells.append(code("""# Pie Chart — Sector Allocation
sector_values = holdings.groupby('sector')['current_value'].sum().reset_index()
sector_values['pct'] = sector_values['current_value'] / sector_values['current_value'].sum() * 100

fig = go.Figure(
    data=[go.Pie(
        labels=sector_values['sector'],
        values=sector_values['current_value'],
        hole=0.45,
        textinfo='label+percent',
        textfont=dict(size=13),
        marker=dict(
            colors=px.colors.qualitative.Pastel,
            line=dict(color='rgba(255,255,255,0.6)', width=2)
        ),
        hovertemplate='<b>%{label}</b><br>Value: $%{value:,.2f}<br>Weight: %{percent}<extra></extra>',
    )]
)
fig.update_layout(
 title=dict(text=' Sector Allocation', font=dict(size=20)),
    height=500,
    annotations=[dict(text=f'${total_value:,.0f}', x=0.5, y=0.5, font_size=18, showarrow=False)],
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)
fig.show()"""))

cells.append(md("---\n## Section 3 — Performance Analysis"))

cells.append(code("""# Calculate returns
daily_returns = calculate_daily_returns(price_data)
cumulative_returns = calculate_cumulative_returns(daily_returns)

# Portfolio-level returns (weighted)
portfolio_daily = compute_portfolio_returns(daily_returns, weights)
portfolio_cumulative = (1 + portfolio_daily).cumprod() - 1

print(f" Portfolio Cumulative Return: {portfolio_cumulative.iloc[-1]*100:+.2f}%")
print(f" SPY Cumulative Return: {cumulative_returns['SPY'].iloc[-1]*100:+.2f}%")"""))

cells.append(code("""# Line Chart — Portfolio vs SPY Cumulative Return
fig = go.Figure()

# Portfolio line (navy blue)
fig.add_trace(go.Scatter(
    x=portfolio_cumulative.index,
    y=portfolio_cumulative.values * 100,
    name='Portfolio',
    line=dict(color='#1a3a5c', width=3),
    hovertemplate='Date: %{x|%Y-%m-%d}<br>Return: %{y:.2f}%<extra>Portfolio</extra>',
))

# SPY line (grey)
fig.add_trace(go.Scatter(
    x=cumulative_returns.index,
    y=cumulative_returns['SPY'].values * 100,
    name='SPY (Benchmark)',
    line=dict(color='#888888', width=2, dash='dot'),
    hovertemplate='Date: %{x|%Y-%m-%d}<br>Return: %{y:.2f}%<extra>SPY</extra>',
))

# End annotations
port_final = portfolio_cumulative.iloc[-1] * 100
spy_final = cumulative_returns['SPY'].iloc[-1] * 100

fig.add_annotation(x=portfolio_cumulative.index[-1], y=port_final,
                   text=f'{port_final:+.1f}%', showarrow=True, arrowhead=2,
                   font=dict(size=14, color='#1a3a5c'), ax=40, ay=-30)
fig.add_annotation(x=cumulative_returns.index[-1], y=spy_final,
                   text=f'{spy_final:+.1f}%', showarrow=True, arrowhead=2,
                   font=dict(size=14, color='#888888'), ax=40, ay=30)

fig.update_layout(
 title=dict(text=' Portfolio vs S&P 500 — Cumulative Return (2 Years)', font=dict(size=20)),
    xaxis_title='Date',
    yaxis_title='Cumulative Return (%)',
    yaxis=dict(ticksuffix='%'),
    height=550,
    hovermode='x unified',
    legend=dict(x=0.01, y=0.99),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)
fig.show()"""))

cells.append(code("""# Bar Chart — Individual Holding Returns (Green/Red)
return_colors = ['#2ecc71' if r > 0 else '#e74c3c' for r in holdings['total_return_pct']]

fig = go.Figure(
    data=[go.Bar(
        x=holdings['ticker'],
        y=holdings['total_return_pct'],
        text=holdings['total_return_pct'].apply(lambda x: f'{x:+.1f}%'),
        textposition='outside',
        marker=dict(color=return_colors, line=dict(color='rgba(255,255,255,0.3)', width=1)),
        hovertemplate='<b>%{x}</b><br>Return: %{y:+.2f}%<extra></extra>',
    )]
)
fig.update_layout(
 title=dict(text=' Individual Holding Returns (Purchase → Today)', font=dict(size=20)),
    xaxis_title='Ticker',
    yaxis_title='Total Return (%)',
    yaxis=dict(ticksuffix='%', zeroline=True, zerolinecolor='rgba(255,255,255,0.3)'),
    height=500,
    showlegend=False,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)
fig.show()"""))

cells.append(md("---\n## Section 4 — Risk Metrics"))

cells.append(code("""# Sharpe Ratios
sharpe_ratios = calculate_sharpe_ratio(daily_returns, weights, RISK_FREE_RATE)

sharpe_df = pd.DataFrame([
    {'Ticker': k, 'Sharpe Ratio': v} for k, v in sharpe_ratios.items()
])

def color_sharpe(val):
    if val > 1:
        return 'background-color: #27ae60; color: white'
    elif val < 0:
        return 'background-color: #e74c3c; color: white'
    return ''

sharpe_df.style.applymap(color_sharpe, subset=['Sharpe Ratio']).format({
    'Sharpe Ratio': '{:.4f}'
}).set_caption(" Annualised Sharpe Ratio per Holding")"""))

cells.append(md("""### Sharpe Ratio Interpretation

The **Sharpe Ratio** measures risk-adjusted return — how much excess return you earn per unit of volatility.

| Sharpe | Interpretation |
|--------|---------------|
| > 1.0 | Excellent — strong risk-adjusted returns |
| 0.5–1.0 | ️ Acceptable — moderate risk efficiency |
| < 0 | Negative — losing money after accounting for risk |

> *A portfolio Sharpe below 1.0 means the advisor should review whether the risk taken is being adequately compensated.*"""))

cells.append(code("""# Max Drawdown
max_drawdowns = calculate_max_drawdown(cumulative_returns)

# Also compute portfolio drawdown
port_cum_df = pd.DataFrame({'PORTFOLIO': portfolio_cumulative})
port_dd = calculate_max_drawdown(port_cum_df)
max_drawdowns.update(port_dd)

dd_df = pd.DataFrame([
    {'Ticker': k, 'Max Drawdown (%)': v} for k, v in max_drawdowns.items()
])

def color_drawdown(val):
    if val < -20:
        return 'background-color: #e74c3c; color: white'
    elif val < -10:
        return 'background-color: #f39c12; color: white'
    return ''

dd_df.style.applymap(color_drawdown, subset=['Max Drawdown (%)']).format({
    'Max Drawdown (%)': '{:.2f}%'
}).set_caption(" Maximum Drawdown per Holding")"""))

cells.append(md("""### Max Drawdown Interpretation

**Max Drawdown** measures the largest peak-to-trough decline — it tells you the worst-case loss an investor would have experienced.

| Drawdown | Interpretation |
|----------|---------------|
| < -10% | ️ Moderate — typical for equity holdings |
| < -20% | Severe — significant capital impairment risk |
| < -30% | Critical — may trigger client concern |

> *Holdings with drawdowns exceeding -20% may warrant hedging strategies or position sizing review.*"""))

cells.append(code("""# Portfolio Beta
portfolio_beta = calculate_portfolio_beta(portfolio_daily, daily_returns['SPY'])

print(f" Portfolio Beta vs S&P 500: {portfolio_beta:.4f}")
print()
if portfolio_beta > 1:
 print("️ Beta > 1 — Portfolio is MORE volatile than the market.")
    print("   In a market downturn, expect amplified losses.")
elif portfolio_beta < 1:
 print(" Beta < 1 — Portfolio is LESS volatile than the market.")
    print("   Provides some downside cushion in corrections.")
else:
 print("️ Beta ≈ 1 — Portfolio moves roughly in line with the market.")"""))

cells.append(md("---\n## Section 5 — Allocation Drift Analysis"))

cells.append(code("""# Allocation Drift
drift_df = calculate_allocation_drift(price_data, PORTFOLIO, TARGET_ALLOCATION)

def highlight_drift(row):
    if row['flag'] == 'Over':
        return ['background-color: rgba(231,76,60,0.3)'] * len(row)
    elif row['flag'] == 'Under':
        return ['background-color: rgba(241,196,15,0.3)'] * len(row)
    return [''] * len(row)

drift_df.style.apply(highlight_drift, axis=1).format({
    'target_pct': '{:.2f}%',
    'actual_pct': '{:.2f}%',
    'drift_pct': '{:+.2f}%',
}).set_caption(" Target vs Actual Sector Allocation")"""))

cells.append(code("""# Grouped Bar Chart — Target vs Actual Allocation
fig = go.Figure()

fig.add_trace(go.Bar(
    x=drift_df['sector'],
    y=drift_df['target_pct'],
    name='Target',
    marker_color='#3498db',
    text=drift_df['target_pct'].apply(lambda x: f'{x:.1f}%'),
    textposition='outside',
))

fig.add_trace(go.Bar(
    x=drift_df['sector'],
    y=drift_df['actual_pct'],
    name='Actual',
    marker_color='#e67e22',
    text=drift_df['actual_pct'].apply(lambda x: f'{x:.1f}%'),
    textposition='outside',
))

fig.update_layout(
 title=dict(text=' Target vs Actual Sector Allocation', font=dict(size=20)),
    xaxis_title='Sector',
    yaxis_title='Allocation (%)',
    yaxis=dict(ticksuffix='%'),
    barmode='group',
    height=500,
    legend=dict(x=0.01, y=0.99),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
)
fig.show()"""))

cells.append(code("""# Rebalancing Recommendations
print(" REBALANCING RECOMMENDATIONS")
print("=" * 50)
for _, row in drift_df.iterrows():
    if row['flag'] == 'Over':
        sector = row['sector']
        drift = row['drift_pct']
        tickers_in_sector = [t for t, info in PORTFOLIO.items() if info['sector'] == sector]
 print(f"\\n {sector} is OVERWEIGHT by {drift:+.1f}%")
        print(f"   → Consider trimming: {', '.join(tickers_in_sector)}")
    elif row['flag'] == 'Under':
        sector = row['sector']
        drift = row['drift_pct']
        tickers_in_sector = [t for t, info in PORTFOLIO.items() if info['sector'] == sector]
 print(f"\\n {sector} is UNDERWEIGHT by {abs(drift):.1f}%")
        print(f"   → Consider adding to: {', '.join(tickers_in_sector)}")"""))

cells.append(md("---\n## Section 6 — Advisor Summary"))

cells.append(code("""# Master Summary Table
summary_data = []
for _, row in holdings.iterrows():
    t = row['ticker']
    drift_flag = drift_df[drift_df['sector'] == row['sector']]['flag'].values[0] if row['sector'] in drift_df['sector'].values else 'N/A'
    summary_data.append({
        'Ticker': t,
        'Sector': row['sector'],
        'Current Value': row['current_value'],
        'Return %': row['total_return_pct'],
        'Sharpe': sharpe_ratios.get(t, 'N/A'),
        'Max Drawdown %': max_drawdowns.get(t, 'N/A'),
        'Drift Flag': drift_flag,
    })

summary_df = pd.DataFrame(summary_data)

def style_summary(row):
    sharpe = row['Sharpe']
    if isinstance(sharpe, (int, float)):
        if sharpe > 1:
            return ['background-color: rgba(46,204,113,0.2)'] * len(row)
        elif sharpe < 0:
            return ['background-color: rgba(231,76,60,0.2)'] * len(row)
    return [''] * len(row)

summary_df.style.apply(style_summary, axis=1).format({
    'Current Value': '${:,.2f}',
    'Return %': '{:+.2f}%',
    'Sharpe': '{:.4f}',
    'Max Drawdown %': '{:.2f}%',
}).set_caption(" Complete Portfolio Summary — Advisor View")"""))

cells.append(code("""# Portfolio Health Score
# Formula: weighted average of normalised metrics

port_sharpe = sharpe_ratios.get('PORTFOLIO', 0)
port_dd = max_drawdowns.get('PORTFOLIO', 0)
avg_drift = drift_df['drift_pct'].abs().mean()

sharpe_score = min(max(port_sharpe / 2.0, 0), 1)  # 0 to 1
dd_score = min(max(1 + port_dd / 50, 0), 1)       # 0 to 1 (-50% = 0, 0% = 1)
drift_score = min(max(1 - avg_drift / 20, 0), 1)   # 0 to 1 (20% drift = 0)

health_score = (sharpe_score * 0.4 + dd_score * 0.3 + drift_score * 0.3) * 100

print(" PORTFOLIO HEALTH SCORE")
print("=" * 50)
print(f"   Sharpe Component  (40%):  {sharpe_score:.2f}  (Sharpe = {port_sharpe:.4f})")
print(f"   Drawdown Component (30%): {dd_score:.2f}  (Max DD = {port_dd:.2f}%)")
print(f"   Drift Component   (30%):  {drift_score:.2f}  (Avg Drift = {avg_drift:.2f}%)")
print(f"")
print(f" Overall Health Score: {health_score:.1f} / 100")
print()

if health_score >= 75:
 print(" Portfolio is in GOOD health")
elif health_score >= 50:
 print(" ️ Portfolio needs ATTENTION — review risk metrics")
else:
 print(" Portfolio is UNDERPERFORMING — rebalancing recommended")"""))

cells.append(code("""# 3 Advisor Recommendations
print(" TOP 3 ADVISOR RECOMMENDATIONS")
print("=" * 50)

recommendations = []

# 1. Performance vs benchmark
alpha = (portfolio_cumulative.iloc[-1] - cumulative_returns['SPY'].iloc[-1]) * 100
if alpha > 0:
 recommendations.append(f"1. Portfolio has OUTPERFORMED SPY by {alpha:.1f}pp over the analysis period. Current strategy is generating alpha — maintain positioning.")
else:
 recommendations.append(f"1. ️ Portfolio has UNDERPERFORMED SPY by {abs(alpha):.1f}pp. Review sector tilts and consider increasing broad market exposure via VTI.")

# 2. Risk assessment
if port_sharpe < 1:
 recommendations.append(f"2. Portfolio Sharpe of {port_sharpe:.2f} is below the 1.0 threshold — the portfolio earns {port_sharpe:.2f} units of return per unit of risk. Consider reducing exposure to high-volatility holdings or adding hedged positions.")
else:
 recommendations.append(f"2. Portfolio Sharpe of {port_sharpe:.2f} exceeds the 1.0 threshold — strong risk-adjusted performance. Maintain current risk profile.")

# 3. Allocation drift
over_sectors = drift_df[drift_df['flag'] == 'Over']
under_sectors = drift_df[drift_df['flag'] == 'Under']
if len(over_sectors) > 0:
    worst = over_sectors.iloc[0]
    tickers_in_sector = [t for t, info in PORTFOLIO.items() if info['sector'] == worst['sector']]
 recommendations.append(f"3. {worst['sector']} is overweight by {worst['drift_pct']:+.1f}%. Consider trimming {', '.join(tickers_in_sector)} to bring allocation back to the {worst['target_pct']:.0f}% target.")
elif len(under_sectors) > 0:
    worst = under_sectors.iloc[0]
    tickers_in_sector = [t for t, info in PORTFOLIO.items() if info['sector'] == worst['sector']]
 recommendations.append(f"3. {worst['sector']} is underweight by {abs(worst['drift_pct']):.1f}%. Consider adding to {', '.join(tickers_in_sector)} to reach the {worst['target_pct']:.0f}% target.")
else:
 recommendations.append("3. All sector allocations are within 5% of target — no rebalancing needed at this time.")

for rec in recommendations:
    print(f"\\n{rec}")"""))

cells.append(md("---\n## CSV Exports for Power BI"))

cells.append(code("""# POWER BI EXPORT — Export all 4 CSVs
path1 = export_daily_returns(daily_returns, portfolio_daily)
path2 = export_portfolio_summary(holdings, sharpe_ratios, max_drawdowns)
path3 = export_allocation_drift(drift_df)
path4 = export_cumulative_returns(cumulative_returns, portfolio_cumulative)

print(" All CSVs exported to data/ folder:")
print(f" {path1}")
print(f" {path2}")
print(f" {path3}")
print(f" {path4}")"""))

cells.append(md("""---
## Power BI Dashboard Setup Instructions

### Page 1 — Portfolio Overview
1. Import `portfolio_summary.csv` and `cumulative_returns.csv`
2. **KPI Cards**: Total Portfolio Value, Portfolio Return %, Portfolio Sharpe Ratio, Portfolio Max Drawdown
3. **Line Chart**: PORTFOLIO vs SPY from `cumulative_returns.csv` (date on X axis, cumulative return on Y)
4. **Bar Chart**: total_return_pct per ticker from `portfolio_summary.csv`, conditional colour (green if positive, red if negative)

### Page 2 — Risk & Allocation
1. Import `allocation_drift.csv`
2. **Donut Chart**: actual_pct by sector
3. **Clustered Bar Chart**: target_pct vs actual_pct per sector
4. **Table**: allocation_drift.csv with conditional formatting — red background where flag = "Over" or "Under"
5. **KPI Cards**: Portfolio Beta, Best Sharpe Holding, Worst Max Drawdown Holding

### Page 3 — Advisor Rebalancing Alerts
1. Import `portfolio_summary.csv` and `allocation_drift.csv`
2. **Table**: Full portfolio summary with all metrics
3. **Colour-code rows**: green (Sharpe > 1), amber (0 < Sharpe < 1), red (Sharpe < 0)
4. **Slicer**: filter by sector
5. **Text box**: Paste the 3 plain English recommendations from Section 6 above"""))

# Build notebook
notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    },
    "cells": cells,
}

# Fix: each source line needs newline except last
for cell in notebook['cells']:
    src = cell['source']
    cell['source'] = [line + '\n' if i < len(src) - 1 else line for i, line in enumerate(src)]

with open('analysis.ipynb', 'w') as f:
    json.dump(notebook, f, indent=1)

print(" analysis.ipynb created successfully")
