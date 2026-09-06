"""
drawdown_stats.py
------------------
Turns the two charts (results.png and drawdowns.png) into actual numbers,
so you're not just eyeballing "that dip looks like -20%".

Run it exactly like the other scripts:
    python drawdown_stats.py

Put this in the SAME folder as data.py / backtest.py / metrics.py (your src folder).
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from data     import get_prices, get_spy
from backtest import run_backtest, run_enhanced_backtest, spy_benchmark
from metrics  import drawdown_series, sharpe_ratio, total_return


def time_underwater_pct(dd_series):
    """
    % of all days where you're below the previous peak (i.e. dd < 0).
    A high number means you spend most of your time "recovering"
    rather than sitting at a new high.
    """
    return (dd_series < -0.01).mean() * 100  # -0.01 to ignore tiny float noise


def count_big_drawdowns(dd_series, threshold=-10):
    """
    Counts how many SEPARATE drawdown episodes went below `threshold`%.
    Not just "how many days" — counts distinct dips, so a single long
    slump only counts once, not once per day.
    """
    below = dd_series < threshold
    # A new episode starts whenever we cross from "not below" to "below"
    starts = below & (~below.shift(1).fillna(False))
    return int(starts.sum())


def calmar_ratio(values):
    """
    Annualised return divided by max drawdown (as a positive number).
    Higher is better: it means you earned more return per unit of
    'worst pain' you had to sit through.
    """
    years = (values.index[-1] - values.index[0]).days / 365.25
    total_ret = (values.iloc[-1] / values.iloc[0]) ** (1 / years) - 1
    peak = values.cummax()
    max_dd = abs(((values - peak) / peak).min())
    if max_dd == 0:
        return 0
    return total_ret / max_dd


def print_stats(name, values, dd_series):
    ret = values.pct_change().dropna()
    print(f"\n--- {name} ---")
    print(f"  Total Return          : {total_return(values):.1f}%")
    print(f"  Sharpe Ratio          : {sharpe_ratio(ret):.2f}")
    print(f"  Calmar Ratio          : {calmar_ratio(values):.2f}")
    print(f"  Max Drawdown          : {dd_series.min():.1f}%")
    print(f"  Average Drawdown      : {dd_series[dd_series < 0].mean():.1f}%")
    print(f"  Time Underwater       : {time_underwater_pct(dd_series):.1f}% of all days")
    print(f"  Drawdowns worse than -10% (count): {count_big_drawdowns(dd_series, -10)}")


def main():
    print("Downloading data...")
    prices = get_prices()
    spy    = get_spy()

    print("Running backtests...")
    original  = run_backtest(prices, spy)
    enhanced  = run_enhanced_backtest(prices, spy)
    benchmark = spy_benchmark(spy)

    common    = original.index.intersection(enhanced.index).intersection(benchmark.index)
    original  = original.loc[common]
    enhanced  = enhanced.loc[common]
    benchmark = benchmark.loc[common]

    dd_original  = drawdown_series(original)
    dd_enhanced  = drawdown_series(enhanced)
    dd_benchmark = drawdown_series(benchmark)

    print("\n" + "=" * 50)
    print("QUANTITATIVE COMPARISON")
    print("=" * 50)
    print_stats("SPY Buy & Hold", benchmark, dd_benchmark)
    print_stats("Momentum Strategy (original)", original, dd_original)
    print_stats("Enhanced Strategy (+ RSI + Stop Loss)", enhanced, dd_enhanced)
    print("\n" + "=" * 50)


if __name__ == '__main__':
    main()