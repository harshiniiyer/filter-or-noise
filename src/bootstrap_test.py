"""
bootstrap_test.py (CORRECTED VERSION)
---------------------------------------
The previous version shuffled the ORDER of returns, which doesn't
actually change anything (multiplication doesn't care about order —
that's why it gave a suspicious, meaningless p=1.0000 every time).
 
This version instead RESAMPLES WITH REPLACEMENT: it builds thousands
of "alternate histories" by randomly picking months from your actual
data, allowing the same month to be picked more than once (and other
months to be skipped). This DOES change the outcome each time, so it
actually tests something real.
 
IMPORTANT: for each simulated "alternate history," we apply the SAME
randomly-picked months to BOTH strategies (original and enhanced).
This keeps the pairing intact — e.g. if we happen to pick "March 2020"
three times, both strategies see three copies of THEIR OWN March 2020
return, not a mismatched pair. This is what lets us fairly ask "does
original still beat enhanced" under randomized versions of history.
 
Run it exactly like your other scripts, from inside src:
    python bootstrap_test.py
"""
 
import sys, os
import numpy as np
import pandas as pd
from data import get_prices, get_spy
 
sys.path.insert(0, os.path.dirname(__file__))
 
from data     import get_prices, get_spy
from backtest import run_backtest, run_enhanced_backtest
from metrics  import sharpe_ratio
 
N_SIMULATIONS = 5000
 
 
def final_value_from_returns(returns_array, start=10000):
    """Turns an array of monthly returns into one final dollar value."""
    return start * np.prod(1 + returns_array)
 
 
def main():
    print("Downloading data...")
    prices = get_prices()
    spy    = get_spy()

    print("Running backtests...")
    original = run_backtest(prices, spy)
    enhanced = run_enhanced_backtest(prices, spy, rsi_limit=75, stop_pct=0.05)

    # Align both strategies to the same dates
    common   = original.index.intersection(enhanced.index)
    original = original.loc[common]
    enhanced = enhanced.loc[common]

    # Convert portfolio $ values into monthly % returns
    original_returns = original.pct_change().dropna()
    enhanced_returns  = enhanced.pct_change().dropna()

    # Re-align returns (pct_change drops the first row) and convert to plain arrays
    common_returns = original_returns.index.intersection(enhanced_returns.index)
    original_returns = original_returns.loc[common_returns].values
    enhanced_returns  = enhanced_returns.loc[common_returns].values
    n_months = len(original_returns)

    real_original_final = final_value_from_returns(original_returns)
    real_enhanced_final  = final_value_from_returns(enhanced_returns)
    real_gap = real_original_final - real_enhanced_final
    sharpe_original = sharpe_ratio(pd.Series(original_returns))
    sharpe_enhanced = sharpe_ratio(pd.Series(enhanced_returns))

    print(f"\nReal final value — Original strategy : ${real_original_final:,.0f}")
    print(f"Real final value — Enhanced strategy : ${real_enhanced_final:,.0f}")
    print(f"Real gap (original minus enhanced)    : ${real_gap:,.0f}")
    print(f"Sharpe — Original strategy             : {sharpe_original:.2f}")
    print(f"Sharpe — Enhanced strategy              : {sharpe_enhanced:.2f}")

    print(f"\nRunning {N_SIMULATIONS} bootstrap resamples (with replacement)...")
    rng = np.random.default_rng(seed=42)  # fixed seed = same result every time you run this

    bootstrap_gaps = np.empty(N_SIMULATIONS)
    for i in range(N_SIMULATIONS):
        # Pick n_months random month-indices, WITH repeats allowed
        random_idx = rng.integers(0, n_months, size=n_months)

        # Apply the SAME random picks to both strategies (keeps pairing intact)
        sim_original_final = final_value_from_returns(original_returns[random_idx])
        sim_enhanced_final  = final_value_from_returns(enhanced_returns[random_idx])

        bootstrap_gaps[i] = sim_original_final - sim_enhanced_final

    # How often did the resampled "alternate history" NOT favor original
    # (i.e. enhanced tied or beat it)? This is our p-value.
    p_value = np.mean(bootstrap_gaps <= 0)

    # A 90% confidence interval on the gap itself
    ci_low, ci_high = np.percentile(bootstrap_gaps, [5, 95])

    print("\n" + "=" * 55)
    print("BOOTSTRAP SIGNIFICANCE TEST RESULT (corrected)")
    print("=" * 55)
    print(f"Real observed gap                : ${real_gap:,.0f}")
    print(f"Average bootstrap gap            : ${bootstrap_gaps.mean():,.0f}")
    print(f"90% confidence interval for gap  : ${ci_low:,.0f}  to  ${ci_high:,.0f}")
    print(f"P-value (chance enhanced ties/beats original): {p_value:.4f}")
    print("=" * 55)

    if ci_low > 0:
        print("\n=> The ENTIRE 90% confidence interval is above $0.")
        print("   This means original beats enhanced in the vast majority of")
        print("   simulated alternate histories — a fairly robust finding.")
    elif p_value < 0.05:
        print("\n=> p < 0.05: Original beating enhanced looks statistically robust,")
        print("   though the confidence interval does dip toward/below $0 sometimes.")
    else:
        print("\n=> The confidence interval includes $0 (or goes negative) often")
        print("   enough that we can't be fully confident this gap is a stable,")
        print("   repeatable effect rather than noise from a limited history.")
 
if __name__ == '__main__':
    main()
   