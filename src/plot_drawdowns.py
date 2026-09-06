"""
plot_drawdowns.py
-----------------
Same idea as main.py, but instead of plotting portfolio $ value,
this plots DRAWDOWN (% below peak) over time — i.e. the "losses" chart.
 
Run it exactly like main.py:
    python plot_drawdowns.py
 
It reuses your existing data.py / backtest.py / metrics.py — nothing
in those files needs to change except adding drawdown_series() to
metrics.py (see the updated metrics.py provided alongside this file).
"""
 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sys, os
 
sys.path.insert(0, os.path.dirname(__file__))
 
from data import get_prices, get_spy
from backtest import run_backtest, run_enhanced_backtest, spy_benchmark
from metrics import drawdown_series
 
 
def main():
    print("Downloading data...")
    prices = get_prices()
    spy    = get_spy()
 
    print("Running original backtest...")
    original  = run_backtest(prices, spy)
 
    print("Running enhanced backtest (RSI + stop loss)...")
    enhanced  = run_enhanced_backtest(prices, spy)
    benchmark = spy_benchmark(spy)
 
    # Align all three to common dates (same as main.py)
    common    = original.index.intersection(enhanced.index).intersection(benchmark.index)
    original  = original.loc[common]
    enhanced  = enhanced.loc[common]
    benchmark = benchmark.loc[common]
 
    # --- THE ONLY REAL DIFFERENCE FROM main.py ---
    # Convert each $ value series into a drawdown-% series before plotting.
    dd_benchmark = drawdown_series(benchmark)
    dd_original  = drawdown_series(original)
    dd_enhanced  = drawdown_series(enhanced)
 
    # Print the single worst drawdown for each, as a quick sanity check
    print("\n─── MAX DRAWDOWNS ───")
    print(f"SPY Buy & Hold      : {dd_benchmark.min():.1f}%")
    print(f"Momentum (original) : {dd_original.min():.1f}%")
    print(f"Enhanced (RSI+Stop) : {dd_enhanced.min():.1f}%")
 
    # Same figure size, same colors, same legend labels as main.py,
    # so the two charts sit side by side and look like a matched pair.
    fig, ax = plt.subplots(figsize=(14, 7))
 
    ax.fill_between(dd_benchmark.index, dd_benchmark.values, 0,
                     color='#8b949e', alpha=0.15)
    ax.plot(dd_benchmark.index, dd_benchmark.values,
            label='SPY Buy & Hold',
            color='#8b949e', linewidth=1.5, linestyle='--')
 
    ax.fill_between(dd_original.index, dd_original.values, 0,
                     color='#58a6ff', alpha=0.15)
    ax.plot(dd_original.index, dd_original.values,
            label='Momentum Strategy (original)',
            color='#58a6ff', linewidth=2)
 
    ax.fill_between(dd_enhanced.index, dd_enhanced.values, 0,
                     color='#3fb950', alpha=0.15)
    ax.plot(dd_enhanced.index, dd_enhanced.values,
            label='Enhanced Strategy (+ RSI + Stop Loss)',
            color='#3fb950', linewidth=2.5)
 
    ax.axhline(0, color='black', linewidth=0.8)  # 0% line = "at a new peak"
 
    # No log scale here on purpose — drawdown is already a % scale (0 to
    # roughly -60), a log scale doesn't make sense for negative numbers.
    ax.set_title('Momentum Factor Audit: Drawdowns (Original vs Enhanced)',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Year')
    ax.set_ylabel('Drawdown from Peak (%)')
    ax.legend(fontsize=11, loc='lower left')
    ax.grid(True, alpha=0.3)
 
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    plt.xticks(rotation=45)
    plt.tight_layout()
 
    plt.savefig('drawdowns.png', dpi=150, bbox_inches='tight')
    print("\nChart saved as drawdowns.png")
    plt.show()
 
 
if __name__ == '__main__':
    main()
 
