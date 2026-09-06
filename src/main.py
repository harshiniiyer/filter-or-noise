import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from data import get_prices, get_spy
from backtest import run_backtest, run_enhanced_backtest, spy_benchmark
from metrics  import print_report

def main():
    print("Downloading data...")
    prices = get_prices()
    spy    = get_spy()

    print("Running original backtest...")
    original  = run_backtest(prices, spy)

    print("Running enhanced backtest (RSI + stop loss)...")
    enhanced  = run_enhanced_backtest(prices, spy)
    benchmark = spy_benchmark(spy)

    # Align all three to common dates
    common    = original.index.intersection(enhanced.index).intersection(benchmark.index)
    original  = original.loc[common]
    enhanced  = enhanced.loc[common]
    benchmark = benchmark.loc[common]

    # Print results for both
    print("\n─── ORIGINAL STRATEGY ───")
    print_report(original, benchmark)
    print("\n─── ENHANCED STRATEGY (RSI + Stop Loss) ───")
    print_report(enhanced, benchmark)

    # Three-line chart
    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(benchmark.index, benchmark.values,
            label='SPY Buy & Hold',
            color='#8b949e', linewidth=1.5, linestyle='--')

    ax.plot(original.index, original.values,
            label='Momentum Strategy (original)',
            color='#58a6ff', linewidth=2)

    ax.plot(enhanced.index, enhanced.values,
            label='Enhanced Strategy (+ RSI + Stop Loss)',
            color='#3fb950', linewidth=2.5)

    ax.set_yscale('log')
    ax.set_title('Momentum Factor Audit: Original vs Enhanced Strategy',
                 fontsize=14, fontweight='bold')
    ax.set_xlabel('Year')
    ax.set_ylabel('Portfolio Value ($) — Log Scale')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig('results.png', dpi=150, bbox_inches='tight')
    print("\nChart saved as results.png")
    plt.show()

if __name__ == '__main__':
    main()