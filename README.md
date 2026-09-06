# Momentum Factor Audit

I built a cross-sectional momentum strategy, added two "obvious" risk filters (RSI overbought, trailing stop-loss), and expected it to look better. It didn't — the enhanced version underperformed the original on every metric at the settings I picked first. A parameter grid search suggested a looser RSI setting (75) fixed this, and an initial out-of-sample test seemed to confirm it. Running the same test on two more historical splits, plus a formal significance test, walked that conclusion back: the "improvement" doesn't hold up consistently, and isn't statistically distinguishable from noise. That reversal — and being willing to publish it — is the actual finding here. See [Key finding](#key-finding--and-what-it-actually-means) below.

A backtest of a cross-sectional momentum strategy across six liquid ETFs (SPY, QQQ, IWM, GLD, TLT, EFA), with a regime filter, transaction cost modeling, and statistical robustness checks.

## Strategy

**Baseline (`run_backtest`)**
1. Signal: 12-minus-1 month momentum (skip the most recent month to avoid short-term reversal), computed daily and sampled at month-end.
2. Regime filter: only trade when SPY is above its 200-day moving average. Otherwise, hold cash.
3. Cash filter: only ETFs with positive momentum are eligible.
4. Selection: equal-weight the top third of eligible ETFs by momentum score.
5. Costs: 20bps charged on one-way turnover each month (0 turnover = 0 cost, full portfolio replacement = full 20bps).

**Enhanced (`run_enhanced_backtest`)**
Same as above, plus two additional filters applied before selection:
- RSI filter: exclude ETFs with 14-day RSI at or above a threshold (overbought).
- Trailing stop: exclude ETFs more than X% below their 3-month high.

**Benchmark**
Buy-and-hold SPY, no transaction cost (it only trades once).

## Files

| File | Purpose |
|---|---|
| `data.py` | Downloads daily prices for the ETF universe and SPY |
| `signals.py` | Momentum score, SMA regime flag, RSI, trailing-stop check |
| `backtest.py` | Core strategy logic, turnover-based cost model |
| `drawdown_stats.py` | Sharpe, Calmar, max drawdown, time underwater, drawdown episode count |
| `bootstrap_test.py` | Block bootstrap (5,000 resamples) testing whether original vs. enhanced gap is statistically robust |
| `sensitivity_analysis.py` | 12-combo grid search over RSI limit × stop-loss level |
| `out_of_sample_test.py` | Train (2005–2015) / test (2015–present) split to check the grid-search winner isn't overfit |

## Running it

```bash
pip install -r requirements.txt
cd src
python drawdown_stats.py        # core comparison + risk metrics
python bootstrap_test.py        # significance test
python sensitivity_analysis.py  # RSI/stop grid search
python out_of_sample_test.py    # overfitting check on the grid-search winner
```

## Sensitivity analysis results

12-combination grid search over RSI limit (65/70/75) × stop-loss (5%/10%/15%/20%):

| RSI Limit | Stop Loss | Final Value | Total Return | Sharpe | Max Drawdown | Beats Original? |
|---|---|---|---|---|---|---|
| 65 | 5%  | $61,241 | 491.6% | 0.60 | -17.2% | no |
| 65 | 10% | $68,465 | 561.4% | 0.61 | -20.4% | no |
| 65 | 15% | $68,600 | 562.7% | 0.60 | -28.1% | no |
| 65 | 20% | $74,143 | 616.2% | 0.63 | -22.9% | no |
| 70 | 5%  | $51,041 | 392.1% | 0.52 | -20.8% | no |
| 70 | 10% | $56,055 | 440.5% | 0.54 | -24.0% | no |
| 70 | 15% | $58,997 | 468.8% | 0.55 | -21.9% | no |
| 70 | 20% | $63,701 | 514.2% | 0.58 | -21.4% | no |
| 75 | 5%  | $95,891 | 824.6% | 0.74 | -20.5% | YES |
| 75 | 10% | $80,249 | 673.8% | 0.66 | -23.6% | YES |
| 75 | 15% | $81,662 | 687.4% | 0.66 | -23.4% | YES |
| 75 | 20% | $83,407 | 704.2% | 0.67 | -23.4% | YES |

## Key finding — and what it actually means

At first glance the grid search looks like it found "RSI=75 is the optimal threshold." That's not quite the right read even before checking robustness: RSI≥limit gets excluded from the eligible pool, so a *lower* limit (65) filters more aggressively and a *higher* limit (75) filters less. As the limit rises from 65 → 75, the enhanced strategy filters less and converges back toward the unfiltered original — performance rising monotonically with it is consistent with "the filter subtracts value, and 75 subtracts the least," not "75 is a discovered edge." The out-of-sample and significance testing below confirms this reading: **the RSI overbought filter, at any setting tested, does not have a reliable, statistically distinguishable effect on this strategy.** The apparent "win" at RSI=75 in the full-period grid search does not survive additional scrutiny.

## Out-of-sample validation — and why the first result didn't hold up

The grid search picks its "winner" using the same data it's evaluated on, which is a classic setup for overfitting — a combo can look best purely because it happened to fit noise in one specific stretch of history. `out_of_sample_test.py` checks this: it splits the data into a train period and a test period, picks the winning combo using **only** the train period, then evaluates that single locked-in combo against the untouched test period.

I ran this across three different train/test cutoffs. In every case, the grid search on the training data picked the same combo (RSI=75, stop=5%) — but whether that combo actually beat the original on unseen data was inconsistent:

| Train/test split | Train-period winner | Test period: Original | Test period: Enhanced (tuned) | Beats original out-of-sample? |
|---|---|---|---|---|
| 2005–2015 / 2015–present | RSI=75, stop=5% | $28,574 | $32,168 | Yes |
| 2005–2012 / 2012–present | RSI=75, stop=5% | $47,559 | $53,864 | Yes |
| 2005–2018 / 2018–present | RSI=75, stop=5% | $22,462 | $21,871 | **No** |

Two out of three splits favor the tuned combo, one doesn't. That's not the clean, repeatable pattern the first (2015) split suggested on its own — it's closer to a coin flip that happens to land the same way in training every time (RSI=75 is consistently the "least damaging" choice on train data) without reliably paying off out-of-sample.

## Statistical significance of the original-vs-enhanced gap

`bootstrap_test.py` checks whether the gap between original and enhanced is a real, repeatable effect or could plausibly be noise from one 20-year history. It resamples months with replacement 5,000 times, applying the same resampled months to both strategies to keep the pairing intact.

**Two versions of this were run — the untuned default (RSI=70, stop=10%) and the tuned combo (RSI=75, stop=5%):**

| | Default (RSI=70, stop=10%) | Tuned (RSI=75, stop=5%) |
|---|---|---|
| Original final value | $76,857 | $76,857 |
| Enhanced final value | $54,048 | $92,458 |
| Observed gap (original − enhanced) | $22,809 | -$15,601 |
| Average bootstrap gap | $28,317 | -$16,521 |
| 90% confidence interval | -$12,028 to $95,386 | -$96,231 to $50,184 |
| P-value (chance of a tie or reversal) | 0.1414 | 0.6640 |
| Sharpe — Original / Enhanced | — | 0.65 / 0.74 |

Both confidence intervals cross zero by a wide margin, and both p-values are far above the conventional 0.05 threshold — the tuned combo's p-value (0.66) is actually worse, meaning the direction of the gap (enhanced now ahead by $15,601 on the full period) is *less* statistically trustworthy than the default comparison was, not more. **Neither version of the enhanced strategy shows a gap against original that this data can confidently call real rather than noise.**

Combined with the mixed out-of-sample results above, the honest conclusion is: **the RSI/stop-loss enhancement, at any threshold tested, isn't shown to reliably help or hurt in a way this dataset can distinguish from randomness.** The full-period sensitivity table's "YES, beats original" column for RSI=75 reflects one specific realized history, not a validated, generalizable edge.

## Risk-adjusted comparison

`drawdown_stats.py` runs the same three series (SPY benchmark, original, default enhanced) through a fuller set of risk metrics than a raw returns number gives you:

| Metric | SPY Buy & Hold | Original | Enhanced (default: RSI=70, stop=10%) |
|---|---|---|---|
| Total Return | 760.5% | 668.6% | 440.5% |
| Sharpe Ratio | 0.64 | 0.65 | 0.54 |
| Calmar Ratio | 0.22 | 0.49 | 0.36 |
| Max Drawdown | -50.8% | -21.5% | -24.0% |
| Average Drawdown | -10.9% | -8.5% | -8.9% |
| Time Underwater | 59.1% | 75.7% | 77.3% |
| Drawdowns worse than -10% | 56 | 74 | 71 |

Two things stand out. First, the original strategy actually has a **lower total return than plain SPY buy-and-hold** (668.6% vs 760.5%) — its edge isn't raw return, it's risk control: less than half of SPY's max drawdown (-21.5% vs -50.8%) and more than double the Calmar ratio. Second, the default enhanced strategy (RSI=70/stop=10%) is worse than original on every single metric here — return, Sharpe, Calmar, and drawdown — which lines up with the sensitivity and bootstrap results above: the untuned RSI=70 filter doesn't pay for itself.

## What surprised me

- The strategy's real selling point isn't beating the market on return — it doesn't. It's that it delivers close to SPY's Sharpe ratio while cutting max drawdown by more than half. That's a very different pitch than "this strategy makes more money," and it's the more honest one.
- Adding "safety" filters (RSI, stop-loss) made things worse across the board at the settings most people would reach for first (RSI=70, stop=10%) — more filtering isn't automatically more robust.
- The most humbling part of this project: my first out-of-sample test (a single 2015 split) *did* look like real confirmation that RSI=75 was a genuine improvement. It took running two more splits and a proper significance test to see that this was mostly one favorable split, not a validated effect. A single out-of-sample test can still fool you if you only run it once — which is exactly why "run it once and it passed" isn't the same as "it's robust."
- The full-period sensitivity table's dramatic-looking "$95,891 vs original, YES beats" row is real *as a description of one specific 20-year history*, but it's not evidence of a repeatable edge once you check it against bootstrap resampling and multiple time splits. Headline backtest numbers and statistically validated findings are not the same thing, and it's easy to only produce the first one without realizing you haven't done the second.

## Next steps

- [x] Run `out_of_sample_test.py` — initial 2015 split looked positive; see below for why that wasn't the full picture
- [x] Run `bootstrap_test.py` on both the default and tuned combos — neither shows a statistically robust gap (p=0.14 and p=0.66)
- [x] Add drawdown/Sharpe comparison table from `drawdown_stats.py`
- [x] Add a short "what surprised me" section
- [x] Try additional train/test split dates — 2/3 splits favor the tuned combo, 1/3 doesn't; not a consistent effect
- [ ] Given the mixed/non-significant results, consider testing whether the RSI/stop-loss filters help on a different (larger or more volatile) asset universe, rather than concluding they never help anywhere
- [ ] `out_of_sample_test.py`'s printed test-period label is hardcoded to "(2015-present)" regardless of the actual `TRAIN_END` value used — cosmetic bug, worth fixing so console output doesn't misreport the date range when testing other splits