"""
out_of_sample_test.py
------------------------
Answers: "Was RSI=75 actually a genuinely better threshold, or did the
sensitivity analysis just pick whatever happened to fit this specific
20-year history best (hindsight bias)?"
 
HOW IT WORKS (plain-English):
1. Split all your data into two non-overlapping chunks:
     TRAIN period : 2005-01-01 to 2015-01-01  (used to CHOOSE the best RSI/stop combo)
     TEST period  : 2015-01-01 to today       (used to CHECK if that choice was actually good)
2. Run the same 12-combination grid search, but only look at TRAIN period
   results to decide which RSI/stop-loss combo "wins."
3. Take ONLY that winning combo (don't look at any other combo again) and
   run it on the TEST period, which it has never been evaluated against.
4. Compare that combo's TEST period performance to the ORIGINAL strategy's
   TEST period performance.
 
If the winning combo STILL beats original on the unseen test period,
that's real evidence it's a genuinely better setting. If it does WORSE
than original on the test period, the earlier finding was likely just
fitting to the training history's specific pattern of returns.
 
Run it exactly like your other scripts, from inside src:
    python out_of_sample_test.py
"""
 
import sys, os
import pandas as pd
 
sys.path.insert(0, os.path.dirname(__file__))
 
from data     import get_prices, get_spy
from backtest import run_backtest, run_enhanced_backtest
from metrics  import total_return
 
TRAIN_END = '2015-01-01'  # everything before this = training data
RSI_LIMITS = [65, 70, 75]
STOP_LOSSES = [0.05, 0.10, 0.15, 0.20]
 
 
def slice_period(series, start=None, end=None):
    """Cuts a pandas Series/DataFrame down to a date range."""
    if start:
        series = series[series.index >= start]
    if end:
        series = series[series.index < end]
    return series
 
 
def final_value_over_period(portfolio_series, start_date, end_date):
    """
    Recomputes 'growth of $10,000' but ONLY over a specific date window,
    so training-period trading doesn't leak into the test-period number.
    """
    window = slice_period(portfolio_series, start_date, end_date)
    if len(window) < 2:
        return None
    return 10000 * (window.iloc[-1] / window.iloc[0])
 
 
def main():
    print("Downloading full data (once)...")
    prices = get_prices()
    spy    = get_spy()
 
    print(f"Splitting into TRAIN (before {TRAIN_END}) and TEST (after {TRAIN_END})\n")
 
    # ---------- STEP 1: Grid search, but score combos using TRAIN period only ----------
    print("Running grid search on TRAINING period only...")
    train_results = []
 
    for rsi_limit in RSI_LIMITS:
        for stop_pct in STOP_LOSSES:
            enhanced = run_enhanced_backtest(prices, spy,
                                              rsi_limit=rsi_limit,
                                              stop_pct=stop_pct)
            train_value = final_value_over_period(enhanced, None, TRAIN_END)
            train_results.append({
                'RSI Limit': rsi_limit,
                'Stop Loss': stop_pct,
                'Train Final Value': train_value,
            })
            print(f"  RSI={rsi_limit}, stop={stop_pct:.0%}: "
                  f"train value = ${train_value:,.0f}")
 
    train_df = pd.DataFrame(train_results)
 
    # Pick whichever combo did best DURING TRAINING ONLY
    best_row = train_df.loc[train_df['Train Final Value'].idxmax()]
    best_rsi  = int(best_row['RSI Limit'])
    best_stop = float(best_row['Stop Loss'])
 
    print(f"\n>>> Best combo found on TRAINING data: "
          f"RSI={best_rsi}, stop-loss={best_stop:.0%} "
          f"(train value: ${best_row['Train Final Value']:,.0f})")
 
    # ---------- STEP 2: Run ONLY that winning combo on the unseen TEST period ----------
    print("\nRunning the winning combo AND the original strategy on the TEST period...")
 
    best_enhanced = run_enhanced_backtest(prices, spy,
                                           rsi_limit=best_rsi,
                                           stop_pct=best_stop)
    original = run_backtest(prices, spy)
 
    test_value_enhanced = final_value_over_period(best_enhanced, TRAIN_END, None)
    test_value_original  = final_value_over_period(original, TRAIN_END, None)
 
    print("\n" + "=" * 60)
    print("OUT-OF-SAMPLE TEST RESULT")
    print("=" * 60)
    print(f"Winning combo (chosen using TRAIN data only): "
          f"RSI={best_rsi}, stop-loss={best_stop:.0%}")
    print(f"\nTEST PERIOD ({TRAIN_END}-present) performance, $10,000 start:")
    print(f"  Original strategy      : ${test_value_original:,.0f}")
    print(f"  Enhanced (tuned combo) : ${test_value_enhanced:,.0f}")
    print("=" * 60)
 
    if test_value_enhanced > test_value_original:
        print("\n=> The tuned combo BEATS original on unseen test data.")
        print("   This is real evidence the combo found in training generalizes —")
        print("   not just a fit to one specific historical stretch.")
    else:
        print("\n=> The tuned combo does NOT beat original on unseen test data,")
        print("   even though it looked best during training. This confirms the")
        print("   earlier sensitivity analysis finding was likely overfit to the")
        print("   training period's specific pattern of returns, rather than a")
        print("   genuinely better rule.")
 
 
if __name__ == '__main__':
    main()
 
