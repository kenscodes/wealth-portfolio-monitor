"""
Metrics Engine — Private Wealth Portfolio Health Monitor
========================================================

Pure calculation functions for portfolio analysis. Each function:
  - Takes clean inputs (DataFrames, dicts)
  - Returns a DataFrame or dict
  - Has no side effects (no file I/O, no prints)
  - Is individually testable

Functions
---------
1. fetch_price_data          — pull adjusted close via yfinance
2. calculate_daily_returns   — daily percentage returns
3. calculate_cumulative_returns — cumulative compounded returns
4. calculate_portfolio_value — current holdings valuation
5. calculate_sharpe_ratio    — annualised Sharpe per ticker + portfolio
6. calculate_max_drawdown    — max peak-to-trough drawdown
7. calculate_allocation_drift — sector drift vs target weights
8. calculate_portfolio_beta  — portfolio beta vs benchmark
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf


# ---------------------------------------------------------------------------
# 1. Price Data Fetch
# ---------------------------------------------------------------------------

def fetch_price_data(tickers: list[str], period: str, benchmark: str = 'SPY') -> pd.DataFrame:
    """
    Download adjusted close prices for *tickers* + *benchmark* over *period*.

    Parameters
    ----------
    tickers : list[str]
        Portfolio tickers, e.g. ['AAPL', 'MSFT', ...].
    period : str
        yfinance period string, e.g. '2y'.
    benchmark : str
        Benchmark ticker to include (default 'SPY').

    Returns
    -------
    pd.DataFrame
        Columns = tickers + benchmark, indexed by date.
        Forward-filled, remaining NaNs dropped.
    """
    all_tickers = list(dict.fromkeys(tickers + [benchmark]))  # deduplicate, preserve order
    raw = yf.download(all_tickers, period=period, auto_adjust=True, progress=False)

    # yfinance returns multi-level columns when multiple tickers requested
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw['Close']
    else:
        prices = raw[['Close']].rename(columns={'Close': all_tickers[0]})

    # Clean up
    prices = prices.ffill().dropna()
    return prices


# ---------------------------------------------------------------------------
# 2. Daily Returns
# ---------------------------------------------------------------------------

def calculate_daily_returns(price_data: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily percentage returns from price data.

    Parameters
    ----------
    price_data : pd.DataFrame
        Adjusted close prices (output of fetch_price_data).

    Returns
    -------
    pd.DataFrame
        Daily percentage returns, first row dropped (NaN).
    """
    returns = price_data.pct_change().dropna()
    return returns


# ---------------------------------------------------------------------------
# 3. Cumulative Returns
# ---------------------------------------------------------------------------

def calculate_cumulative_returns(daily_returns: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cumulative compounded returns from daily returns.

    Formula: (1 + r1) * (1 + r2) * ... - 1

    Parameters
    ----------
    daily_returns : pd.DataFrame
        Daily percentage returns (output of calculate_daily_returns).

    Returns
    -------
    pd.DataFrame
        Cumulative returns, same columns as input.
    """
    cumulative = (1 + daily_returns).cumprod() - 1
    return cumulative


# ---------------------------------------------------------------------------
# 4. Portfolio Value
# ---------------------------------------------------------------------------

def calculate_portfolio_value(
    price_data: pd.DataFrame,
    portfolio: dict,
) -> dict:
    """
    Compute current portfolio valuation from latest prices.

    Parameters
    ----------
    price_data : pd.DataFrame
        Adjusted close prices.
    portfolio : dict
        {ticker: {'shares': int, 'purchase_price': float, 'sector': str}}.

    Returns
    -------
    dict with keys:
        'total_value'    : float — total portfolio market value
        'holdings'       : pd.DataFrame — ticker, sector, shares,
                           purchase_price, current_price, current_value
        'weights'        : pd.Series — weight per ticker (sums to 1)
    """
    latest_prices = price_data.iloc[-1]
    rows = []
    for ticker, info in portfolio.items():
        current_price = latest_prices.get(ticker, np.nan)
        current_value = info['shares'] * current_price
        cost_basis = info['shares'] * info['purchase_price']
        total_return_pct = ((current_price - info['purchase_price'])
                           / info['purchase_price'] * 100)
        rows.append({
            'ticker':          ticker,
            'sector':          info['sector'],
            'shares':          info['shares'],
            'purchase_price':  info['purchase_price'],
            'current_price':   round(current_price, 2),
            'current_value':   round(current_value, 2),
            'cost_basis':      round(cost_basis, 2),
            'total_return_pct': round(total_return_pct, 2),
        })

    holdings = pd.DataFrame(rows)
    total_value = holdings['current_value'].sum()
    holdings['weight_pct'] = round(holdings['current_value'] / total_value * 100, 2)

    weights = holdings.set_index('ticker')['weight_pct'] / 100

    return {
        'total_value': round(total_value, 2),
        'holdings':    holdings,
        'weights':     weights,
    }


# ---------------------------------------------------------------------------
# 5. Sharpe Ratio
# ---------------------------------------------------------------------------

def calculate_sharpe_ratio(
    daily_returns: pd.DataFrame,
    portfolio_weights: pd.Series | None = None,
    risk_free_rate: float = 0.05,
) -> dict:
    """
    Annualised Sharpe Ratio per ticker and for the overall portfolio.

    Formula: (mean_daily - rfr/252) / std_daily * sqrt(252)

    Parameters
    ----------
    daily_returns : pd.DataFrame
        Daily returns (output of calculate_daily_returns).
    portfolio_weights : pd.Series, optional
        Weights per ticker for computing portfolio-level Sharpe.
    risk_free_rate : float
        Annualised risk-free rate (default 5%).

    Returns
    -------
    dict  {ticker: sharpe_ratio, 'PORTFOLIO': sharpe_ratio}
    """
    daily_rf = risk_free_rate / 252
    sharpe = {}

    # Exclude benchmark from per-ticker Sharpe (but include if present)
    for col in daily_returns.columns:
        excess = daily_returns[col] - daily_rf
        if excess.std() == 0:
            sharpe[col] = 0.0
        else:
            sharpe[col] = round(
                (excess.mean() / excess.std()) * np.sqrt(252), 4
            )

    # Portfolio-level Sharpe
    if portfolio_weights is not None:
        tickers_in_common = [t for t in portfolio_weights.index
                             if t in daily_returns.columns]
        w = portfolio_weights[tickers_in_common]
        w = w / w.sum()  # re-normalise in case of missing tickers
        portfolio_daily = (daily_returns[tickers_in_common] * w).sum(axis=1)
        excess_port = portfolio_daily - daily_rf
        if excess_port.std() == 0:
            sharpe['PORTFOLIO'] = 0.0
        else:
            sharpe['PORTFOLIO'] = round(
                (excess_port.mean() / excess_port.std()) * np.sqrt(252), 4
            )

    return sharpe


# ---------------------------------------------------------------------------
# 6. Max Drawdown
# ---------------------------------------------------------------------------

def calculate_max_drawdown(cumulative_returns: pd.DataFrame) -> dict:
    """
    Max peak-to-trough drawdown for each column.

    Formula: max( (peak - value) / peak ) over rolling window.

    Parameters
    ----------
    cumulative_returns : pd.DataFrame
        Cumulative returns (output of calculate_cumulative_returns).

    Returns
    -------
    dict  {column: max_drawdown_pct}  (negative values, e.g. -15.3)
    """
    wealth = 1 + cumulative_returns  # wealth index
    peak = wealth.cummax()
    drawdown = (wealth - peak) / peak
    max_dd = drawdown.min()  # most negative value per column

    return {col: round(val * 100, 2) for col, val in max_dd.items()}


# ---------------------------------------------------------------------------
# 7. Allocation Drift
# ---------------------------------------------------------------------------

def calculate_allocation_drift(
    price_data: pd.DataFrame,
    portfolio: dict,
    target_allocation: dict,
) -> pd.DataFrame:
    """
    Compare actual sector allocation vs target and flag drift.

    Parameters
    ----------
    price_data : pd.DataFrame
        Adjusted close prices.
    portfolio : dict
        Portfolio config dict.
    target_allocation : dict
        {sector: target_weight} (0-1 scale).

    Returns
    -------
    pd.DataFrame
        Columns: sector, target_pct, actual_pct, drift_pct, flag
        flag ∈ {'Over', 'Under', 'OK'}
        Drift > 5% absolute triggers Over/Under.
    """
    latest_prices = price_data.iloc[-1]

    # Compute actual sector values
    sector_values = {}
    for ticker, info in portfolio.items():
        sector = info['sector']
        value = info['shares'] * latest_prices.get(ticker, 0)
        sector_values[sector] = sector_values.get(sector, 0) + value

    total_value = sum(sector_values.values())

    rows = []
    for sector, target_w in target_allocation.items():
        actual_value = sector_values.get(sector, 0)
        actual_w = actual_value / total_value if total_value > 0 else 0
        drift = actual_w - target_w

        if drift > 0.05:
            flag = 'Over'
        elif drift < -0.05:
            flag = 'Under'
        else:
            flag = 'OK'

        rows.append({
            'sector':     sector,
            'target_pct': round(target_w * 100, 2),
            'actual_pct': round(actual_w * 100, 2),
            'drift_pct':  round(drift * 100, 2),
            'flag':       flag,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 8. Portfolio Beta
# ---------------------------------------------------------------------------

def calculate_portfolio_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
) -> float:
    """
    Beta of the portfolio vs the benchmark.

    Formula: Cov(portfolio, benchmark) / Var(benchmark)

    Parameters
    ----------
    portfolio_returns : pd.Series
        Daily returns of the weighted portfolio.
    benchmark_returns : pd.Series
        Daily returns of the benchmark (SPY).

    Returns
    -------
    float  Portfolio beta.
    """
    aligned = pd.DataFrame({
        'portfolio': portfolio_returns,
        'benchmark': benchmark_returns,
    }).dropna()

    cov_matrix = aligned.cov()
    beta = cov_matrix.loc['portfolio', 'benchmark'] / cov_matrix.loc['benchmark', 'benchmark']
    return round(beta, 4)


# ---------------------------------------------------------------------------
# Helper: Weighted Portfolio Returns
# ---------------------------------------------------------------------------

def compute_portfolio_returns(
    daily_returns: pd.DataFrame,
    weights: pd.Series,
) -> pd.Series:
    """
    Compute weighted daily portfolio returns.

    Parameters
    ----------
    daily_returns : pd.DataFrame
        Daily returns per ticker.
    weights : pd.Series
        Portfolio weights per ticker.

    Returns
    -------
    pd.Series  Weighted daily portfolio returns.
    """
    tickers = [t for t in weights.index if t in daily_returns.columns]
    w = weights[tickers]
    w = w / w.sum()
    return (daily_returns[tickers] * w).sum(axis=1)
