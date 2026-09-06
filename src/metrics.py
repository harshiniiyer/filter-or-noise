import numpy as np
 
def total_return(values):
    """Total %return from start to end."""
    return (values.iloc[-1]/values.iloc[0]-1)*100
 
def sharpe_ratio(returns, risk_free_annual=0.02):
    """Annualised Sharpe ratio.
    Measures return earned per unit of risk taken.
    Risk-free rate defaults to 2% annually (0.02/12 per month).
    Multiply by sqrt(12) to annualize from monthly returns.
    """
    rf_monthly=risk_free_annual/12
    excess=returns-rf_monthly
    if excess.std()==0:
        return 0
    return (excess.mean()/ excess.std())*np.sqrt(12)
 
def max_drawdown(values):
    """
    Maximum drawdown: the worst peak-to-trough decline.
    A value of -0.25 means the strategy lost 25% from its peak
    at some point. Smaller (less negative) is better.
    """
    peak=values.cummax()
    drawdown=(values-peak)/peak
    return drawdown.min()
 
def drawdown_series(values):
    """
    NEW: Returns the FULL drawdown history (in %), not just the worst point.
    At every date, this tells you: "how far below my all-time-high (so far)
    am I right now?" This is what you plot to SEE the losses over time,
    instead of just knowing the single worst number.
 
    Example: -15.0 means "currently 15% below the peak reached so far."
    A value of 0 means "at a new all-time high right now."
    """
    peak = values.cummax()
    drawdown = (values - peak) / peak
    return drawdown * 100  # as a percentage, e.g. -15.0 not -0.15
 
def print_report(strategy,benchmark):
    """Print a clean side-by-side comparison."""
    s_ret=strategy.pct_change().dropna()
    b_ret=benchmark.pct_change().dropna()
    common=s_ret.index.intersection(b_ret.index)
 
    print("="*45)
    print("MOMENTUM FACTOR AUDIT-RESULTS")
    print("="*45)
    print(f"\n Strategy")
    print(f"  Total Return : {total_return(strategy):.1f}%")
    print(f"  Sharpe Ratio : {sharpe_ratio(s_ret.loc[common]):.2f}")
    print(f"  Max Drawdown : {max_drawdown(strategy):.1%}")
    print(f"\n  SPY Buy & Hold (benchmark)")
    print(f"  Total Return : {total_return(benchmark):.1f}%")
    print(f"  Sharpe Ratio : {sharpe_ratio(b_ret.loc[common]):.2f}")
    print(f"  Max Drawdown : {max_drawdown(benchmark):.1%}")
    print("=" * 45)
    mdd=abs(max_drawdown(strategy))
 
