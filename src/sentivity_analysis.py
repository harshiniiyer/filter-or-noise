"""
sensitivity_analysis.py
-------------------------
Answers: "Did I just get unlucky picking RSI=70 and stop=10%? Or does
the enhanced strategy underperform the original no matter which
reasonable thresholds I use?"

HOW IT WORKS (plain-English):
We already know: enhanced (RSI=70, stop=10%) underperformed original
by about $22,800. But maybe a DIFFERENT choice of RSI/stop-loss would
have done better. This script tries a small grid of combinations
(3 RSI limits x 4 stop-loss levels = 12 total) and prints a table
showing the final $ value for each combination, so you can see the
whole picture at once instead of guessing from one setting.

Run it exactly like your other scripts, from inside src:
    python sensitivity_analysis.py

NOTE: this downloads data ONCE, then runs the backtest 12 times using
that same data (so it's not 12x slower to download — just 12x slower
to compute, which is quick).
"""

import sys, os
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from data     import get_prices, get_spy
from backtest import run_backtest, run_enhanced_backtest
from metrics  import total_return, sharpe_ratio, max_drawdown

# The grid of settings to test. Feel free to add more values later,
# but start small — each extra value adds more run time.
RSI_LIMITS = [65, 70, 75]
STOP_LOSSES = [0.05, 0.10, 0.15, 0.20]


def main():
    print("Downloading data (once)...")
    prices = get_prices()
    spy    = get_spy()

    print("Running original strategy (the baseline we compare against)...")
    original = run_backtest(prices, spy)
    original_final = original.iloc[-1]
    print(f"Original strategy final value: ${original_final:,.0f}\n")

    results = []  # we'll collect one row per combination tested

    total_combos = len(RSI_LIMITS) * len(STOP_LOSSES)
    combo_num = 0

    for rsi_limit in RSI_LIMITS:
        for stop_pct in STOP_LOSSES:
            combo_num += 1
            print(f"Testing combo {combo_num}/{total_combos}: "
                  f"RSI limit={rsi_limit}, stop-loss={stop_pct:.0%}...")

            enhanced = run_enhanced_backtest(prices, spy,
                                              rsi_limit=rsi_limit,
                                              stop_pct=stop_pct)

            final_value = enhanced.iloc[-1]
            ret_pct     = total_return(enhanced)
            mdd_pct     = max_drawdown(enhanced) * 100
            monthly_ret = enhanced.pct_change().dropna()
            sharpe      = sharpe_ratio(monthly_ret)

            beats_original = final_value > original_final

            results.append({
                'RSI Limit': rsi_limit,
                'Stop Loss': f"{stop_pct:.0%}",
                'Final Value': final_value,
                'Total Return %': ret_pct,
                'Sharpe': sharpe,
                'Max Drawdown %': mdd_pct,
                'Beats Original?': 'YES' if beats_original else 'no',
            })

    # Turn the results into a clean table
    df = pd.DataFrame(results)

    print("\n" + "=" * 90)
    print("SENSITIVITY ANALYSIS RESULTS")
    print("=" * 90)
    print(f"(Original strategy for comparison: ${original_final:,.0f})\n")

    # Format nicely for printing
    df_display = df.copy()
    df_display['Final Value']   = df_display['Final Value'].map(lambda x: f"${x:,.0f}")
    df_display['Total Return %'] = df_display['Total Return %'].map(lambda x: f"{x:.1f}%")
    df_display['Sharpe']         = df_display['Sharpe'].map(lambda x: f"{x:.2f}")
    df_display['Max Drawdown %'] = df_display['Max Drawdown %'].map(lambda x: f"{x:.1f}%")

    print(df_display.to_string(index=False))
    print("=" * 90)

    # Quick summary: how many of the 12 combos actually beat original?
    n_beats = (df['Final Value'] > original_final).sum()
    print(f"\n{n_beats} out of {total_combos} combinations beat the original strategy.")

    if n_beats == 0:
        print("=> The original strategy beats EVERY enhanced combination tested.")
        print("   This strengthens the finding: it's not about picking the 'wrong'")
        print("   RSI/stop-loss numbers — the enhancement approach itself seems")
        print("   to underperform regardless of threshold choice.")
    elif n_beats == total_combos:
        print("=> Every enhanced combination beat the original.")
        print("   This suggests RSI=70/stop=10% (your original enhanced settings)")
        print("   may have been an unusually poor choice, not representative of")
        print("   the enhancement approach in general.")
    else:
        print(f"=> Results are mixed ({n_beats}/{total_combos} beat original).")
        print("   This suggests the enhancement's performance is sensitive to")
        print("   the exact threshold chosen, rather than consistently good or bad.")

    # Save the full table to a CSV too, so you have it for a writeup/report
    df.to_csv('sensitivity_results.csv', index=False)
    print("\nFull results also saved to sensitivity_results.csv")


if __name__ == '__main__':
    main()