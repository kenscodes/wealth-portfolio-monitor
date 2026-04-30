"""
CSV Export Logic — Private Wealth Portfolio Health Monitor
==========================================================

Functions to export analysis results as clean CSVs for Power BI ingestion.
All exports are saved to the `data/` directory relative to this file.

Each function follows the convention:
  - Takes pre-computed DataFrames/dicts as input
  - Writes a single CSV to data/
  - Returns the output file path for confirmation
"""

import os
from pathlib import Path

import pandas as pd


# Output directory
DATA_DIR = Path(__file__).parent / 'data'


def _ensure_data_dir() -> None:
    """Create the data/ directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# POWER BI EXPORT — Daily Returns
# ---------------------------------------------------------------------------

def export_daily_returns(
    daily_returns: pd.DataFrame,
    portfolio_returns: pd.Series,
) -> str:
    """
    Export daily returns for all tickers, portfolio, and SPY.

    Parameters
    ----------
    daily_returns : pd.DataFrame
        Daily returns per ticker (must include SPY column).
    portfolio_returns : pd.Series
        Weighted daily portfolio returns.

    Returns
    -------
    str  Path to the exported CSV file.

    Output Columns
    --------------
    date, AAPL, MSFT, JPM, GLD, BND, VTI, AMZN, JNJ, PORTFOLIO, SPY
    """
    _ensure_data_dir()

    df = daily_returns.copy()
    df['PORTFOLIO'] = portfolio_returns

    # Ensure SPY is last column
    cols = [c for c in df.columns if c != 'SPY'] + ['SPY']
    cols = [c for c in cols if c in df.columns]
    df = df[cols]

    df.index.name = 'date'
    path = DATA_DIR / 'daily_returns.csv'
    df.to_csv(path, float_format='%.6f')
    return str(path)


# ---------------------------------------------------------------------------
# POWER BI EXPORT — Portfolio Summary
# ---------------------------------------------------------------------------

def export_portfolio_summary(
    holdings: pd.DataFrame,
    sharpe_ratios: dict,
    max_drawdowns: dict,
) -> str:
    """
    Export per-holding summary with key metrics.

    Parameters
    ----------
    holdings : pd.DataFrame
        From calculate_portfolio_value() — must have ticker, sector, shares,
        purchase_price, current_price, current_value, weight_pct, total_return_pct.
    sharpe_ratios : dict
        {ticker: sharpe_ratio}.
    max_drawdowns : dict
        {ticker: max_drawdown_pct}.

    Returns
    -------
    str  Path to the exported CSV file.

    Output Columns
    --------------
    ticker, sector, shares, purchase_price, current_price, current_value,
    weight_pct, total_return_pct, sharpe_ratio, max_drawdown_pct
    """
    _ensure_data_dir()

    df = holdings[['ticker', 'sector', 'shares', 'purchase_price',
                   'current_price', 'current_value', 'weight_pct',
                   'total_return_pct']].copy()
    df['sharpe_ratio'] = df['ticker'].map(sharpe_ratios)
    df['max_drawdown_pct'] = df['ticker'].map(max_drawdowns)

    path = DATA_DIR / 'portfolio_summary.csv'
    df.to_csv(path, index=False, float_format='%.4f')
    return str(path)


# ---------------------------------------------------------------------------
# POWER BI EXPORT — Allocation Drift
# ---------------------------------------------------------------------------

def export_allocation_drift(drift_df: pd.DataFrame) -> str:
    """
    Export sector allocation drift analysis.

    Parameters
    ----------
    drift_df : pd.DataFrame
        From calculate_allocation_drift() — columns: sector, target_pct,
        actual_pct, drift_pct, flag.

    Returns
    -------
    str  Path to the exported CSV file.
    """
    _ensure_data_dir()

    path = DATA_DIR / 'allocation_drift.csv'
    drift_df.to_csv(path, index=False, float_format='%.2f')
    return str(path)


# ---------------------------------------------------------------------------
# POWER BI EXPORT — Cumulative Returns
# ---------------------------------------------------------------------------

def export_cumulative_returns(
    cumulative_returns: pd.DataFrame,
    portfolio_cumulative: pd.Series,
) -> str:
    """
    Export cumulative returns for all tickers, portfolio, and SPY.

    Parameters
    ----------
    cumulative_returns : pd.DataFrame
        Cumulative returns per ticker (must include SPY column).
    portfolio_cumulative : pd.Series
        Cumulative returns for the weighted portfolio.

    Returns
    -------
    str  Path to the exported CSV file.

    Output Columns
    --------------
    date, AAPL, MSFT, JPM, GLD, BND, VTI, AMZN, JNJ, PORTFOLIO, SPY
    """
    _ensure_data_dir()

    df = cumulative_returns.copy()
    df['PORTFOLIO'] = portfolio_cumulative

    # Ensure SPY is last column
    cols = [c for c in df.columns if c != 'SPY'] + ['SPY']
    cols = [c for c in cols if c in df.columns]
    df = df[cols]

    df.index.name = 'date'
    path = DATA_DIR / 'cumulative_returns.csv'
    df.to_csv(path, float_format='%.6f')
    return str(path)
