import pandas as pd
import numpy as np
from signals import momentum_scores, sma_regime
 
 
def calc_turnover(old_picks, new_picks):
    """
    Measures how much of the portfolio actually changed this month.
 
    Both old_picks and new_picks are lists of tickers, each assumed
    to be held at EQUAL weight (that's what your strategy already does).
 
    Returns a number between 0 and 1:
      0.0 = held the exact same ETFs as last month, nothing traded
      1.0 = sold everything and bought a completely different set
 
    This is the standard "one-way turnover" definition used in
    academic backtesting papers.
    """
    old_weight = 1 / len(old_picks) if len(old_picks) > 0 else 0
    new_weight = 1 / len(new_picks) if len(new_picks) > 0 else 0
 
    all_tickers = set(old_picks) | set(new_picks)
    total_change = 0.0
    for ticker in all_tickers:
        w_old = old_weight if ticker in old_picks else 0
        w_new = new_weight if ticker in new_picks else 0
        total_change += abs(w_new - w_old)
 
    return total_change / 2  # divide by 2 so fully-different portfolios = 1.0, not 2.0
 
 
def run_backtest(prices, spy, cost_per_turnover=0.002):
    """
    Monthly momentum strategy with regime and cash filters.
    Starts with $10,000 and simulates trades month by month.
 
    cost_per_turnover: the cost, as a fraction, of completely turning
    over your whole portfolio in one month (buying everything new AND
    selling everything old). 0.002 = 20 basis points = a common
    real-world estimate for ETF trading costs + slippage combined.
    If your turnover this month is only 50% (turnover=0.5), you pay
    half of that: 0.001, i.e. 0.1% of your portfolio value.
    """
    # Calculate signals on daily data
    scores_daily = momentum_scores(prices)
    bull_daily = sma_regime(spy)
    # Resample everything to month end
    monthly_prices = prices.resample('ME').last()
    monthly_scores = scores_daily.resample('ME').last()
    monthly_bull = bull_daily.resample('ME').last()
 
    portfolio_values = []
    portfolio_dates = []
    cash = 10000
    prev_picks = []  # NEW: remember last month's holdings so we can measure turnover
 
    # start after 13 months of warmup
    for i in range(13, len(monthly_prices) - 1):
        today = monthly_prices.index[i]
        tomorrow = monthly_prices.index[i + 1]
        if today not in monthly_scores.index:
            continue
        scores = monthly_scores.loc[today]
        is_bull = monthly_bull.get(today, False)
 
        # Cash filter: only ETFs with positive momentum
        valid = scores[scores > 0]
        if not is_bull or valid.empty:
            # regime says bear market or no positive momentum means to hold cash
            month_return = 0
            current_picks = []  # NEW: holding cash = holding nothing
        else:
            # select top third by momentum score
            n_picks = max(1, len(valid) // 3)
            picks = valid.nlargest(n_picks).index
            current_picks = list(picks)  # NEW
 
            # Equal weight return over the month
            p0 = monthly_prices.loc[today, picks]
            p1 = monthly_prices.loc[tomorrow, picks]
            month_return = ((p1 / p0) - 1).mean()
 
        # NEW: charge a transaction cost based on how much changed since last month
        turnover = calc_turnover(prev_picks, current_picks)
        trading_cost = turnover * cost_per_turnover
        month_return = month_return - trading_cost
 
        cash = cash * (1 + month_return)
        portfolio_values.append(cash)
        portfolio_dates.append(tomorrow)
        prev_picks = current_picks  # NEW: remember for next loop
 
    strategy = pd.Series(portfolio_values, index=portfolio_dates,
                         name='Momentum Strategy')
    return strategy
 
 
def spy_benchmark(spy, start=10000):
    """Simple buy-and-hold SPY-the benchmark we compare against.
    No transaction cost added here on purpose — buy-and-hold only
    trades once at the very start, so a monthly cost doesn't apply."""
    monthly = spy.resample('ME').last()
    returns = monthly.pct_change().dropna()
    values = (1 + returns).cumprod() * start
    values.name = ('SPY Buy & Hold')
    return values
 
 
def run_enhanced_backtest(prices, spy, rsi_limit=70, stop_pct=0.10, cost_per_turnover=0.002):
    """
    Enhanced strategy: original momentum + two new filters.
    RSI filter    : skip any ETF with RSI >= 70 (overbought, rally likely exhausted).
    Trailing stop : skip any ETF down more than 10% from its 3-month high.
 
    cost_per_turnover: same meaning as in run_backtest above. The RSI and
    stop-loss filters will likely cause MORE turnover than the original
    strategy (more frequent switching in/out of positions), so this cost
    is expected to hurt the enhanced strategy more.
    """
    from signals import momentum_scores, sma_regime, compute_rsi, trailing_stop_ok
 
    scores_daily = momentum_scores(prices)
    bull_daily = sma_regime(spy)
    rsi_daily = prices.apply(compute_rsi)
    stop_daily = prices.apply(lambda col: trailing_stop_ok(col, stop_pct=stop_pct))
 
    monthly_prices = prices.resample('ME').last()
    monthly_scores = scores_daily.resample('ME').last()
    monthly_bull = bull_daily.resample('ME').last()
    monthly_rsi = rsi_daily.resample('ME').last()
    monthly_stop = stop_daily.resample('ME').last()
    portfolio_values = []
    portfolio_dates = []
    cash = 10000.0
    prev_picks = []  # NEW
 
    for i in range(13, len(monthly_prices) - 1):
        today = monthly_prices.index[i]
        tomorrow = monthly_prices.index[i + 1]
 
        if today not in monthly_scores.index:
            continue
 
        scores = monthly_scores.loc[today]
        is_bull = monthly_bull.get(today, False)
        valid = scores[scores > 0]
 
        if not is_bull or valid.empty:
            month_return = 0.0
            current_picks = []  # NEW
        else:
            # RSI filter — remove overbought ETFs
            if today in monthly_rsi.index:
                rsi_ok = monthly_rsi.loc[today] < rsi_limit
                valid = valid[rsi_ok.reindex(valid.index).fillna(False)]
 
            # Stop loss filter — remove ETFs below trailing stop
            if today in monthly_stop.index:
                stop_ok = monthly_stop.loc[today]
                valid = valid[stop_ok.reindex(valid.index).fillna(False)]
 
            if valid.empty:
                month_return = 0.0
                current_picks = []  # NEW
            else:
                n_picks = max(1, len(valid) // 3)
                picks = valid.nlargest(n_picks).index
                current_picks = list(picks)  # NEW
                p0 = monthly_prices.loc[today, picks]
                p1 = monthly_prices.loc[tomorrow, picks]
                month_return = ((p1 / p0) - 1).mean()
 
        # NEW: same transaction cost logic as the original strategy
        turnover = calc_turnover(prev_picks, current_picks)
        trading_cost = turnover * cost_per_turnover
        month_return = month_return - trading_cost
 
        cash = cash * (1 + month_return)
        portfolio_values.append(cash)
        portfolio_dates.append(tomorrow)
        prev_picks = current_picks  # NEW
 
    return pd.Series(portfolio_values, index=portfolio_dates,
                     name='Enhanced Strategy (RSI + Stop Loss)')
 
