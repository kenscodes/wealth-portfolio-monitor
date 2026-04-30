"""
Portfolio Configuration — Private Wealth Portfolio Health Monitor
================================================================

Defines the client portfolio holdings, target sector allocation,
and benchmark parameters. This configuration drives the entire
analysis pipeline.

Modelled after the kind of structured portfolio definition a
Goldman Sachs PWM advisor would maintain for a high-net-worth client.
"""

# Client Portfolio Holdings
# Each entry: ticker → {shares held, average purchase price, sector}

PORTFOLIO = {
    'AAPL': {'shares': 50,  'purchase_price': 150.00,  'sector': 'Technology'},
    'MSFT': {'shares': 30,  'purchase_price': 280.00,  'sector': 'Technology'},
    'JPM':  {'shares': 40,  'purchase_price': 130.00,  'sector': 'Financials'},
    'GLD':  {'shares': 20,  'purchase_price': 170.00,  'sector': 'Commodities'},
    'BND':  {'shares': 100, 'purchase_price': 75.00,   'sector': 'Fixed Income'},
    'VTI':  {'shares': 60,  'purchase_price': 200.00,  'sector': 'Broad Market'},
    'AMZN': {'shares': 15,  'purchase_price': 3200.00, 'sector': 'Technology'},
    'JNJ':  {'shares': 35,  'purchase_price': 160.00,  'sector': 'Healthcare'},
}

# Target Sector Allocation (must sum to 1.0)

TARGET_ALLOCATION = {
    'Technology':   0.40,
    'Financials':   0.15,
    'Commodities':  0.10,
    'Fixed Income': 0.20,
    'Broad Market': 0.10,
    'Healthcare':   0.05,
}

# Benchmark & Analysis Parameters

BENCHMARK_TICKER = 'SPY'       # S&P 500 ETF as benchmark
ANALYSIS_PERIOD  = '2y'        # 2 years of historical data
RISK_FREE_RATE   = 0.05        # Annualised risk-free rate (US 10Y approx.)
