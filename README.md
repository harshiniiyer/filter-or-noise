# Momentum Factor Audit

I built a cross-sectional momentum strategy, added two "obvious" risk filters (RSI overbought, trailing stop-loss), and expected it to look better. It didn't — the enhanced version underperformed the original on every metric at the settings I picked first. Instead of rewriting the conclusion to fit what I wanted, I built out a full audit trail to find out why: a 12-combination parameter grid search, an out-of-sample validation split, and a bootstrap significance test. The answer turned out to be more interesting than "pick better numbers" — see [Key finding](#key-finding--and-what-it-actually-means) below.

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

At first glance this looks like "RSI=75 is the optimal threshold." That's not quite the right read. RSI≥limit gets excluded from the eligible pool, so a *lower* limit (65) filters more aggressively and a *higher* limit (75) filters less. As the limit rises from 65 → 75, the enhanced strategy filters less and converges back toward the unfiltered original — and performance rises monotonically with it. The stop-loss column, by contrast, shows no clean pattern.

The honest interpretation: **the RSI overbought filter is actively hurting performance in this dataset, and the least damage comes from applying it least.** This is a more useful (and more defensible) research conclusion than "75 is the best parameter" — it says something about whether the filter concept adds value at all, not just where to tune a knob.

## Out-of-sample validation

The grid search above picks its "winner" using the same data it's evaluated on, which is a classic setup for overfitting — a combo can look best purely because it happened to fit noise in one specific stretch of history, not because it's a genuinely better rule. `out_of_sample_test.py` checks this directly: it splits the data into train (2005–2015) and test (2015–present), picks the winning combo using **only** the train period, then evaluates that single locked-in combo against the untouched test period.

Result:

| Strategy | Test period (2015–present) final value, $10,000 start |
|---|---|
| Original | $28,574 |
| Enhanced (RSI=75, stop=5% — the train-period winner) | $32,168 |

The tuned combo, chosen without ever looking at the test period, still beat the original on unseen data. That's real evidence the RSI=75 pattern (a lighter-touch filter outperforming a more aggressive one) isn't just an artifact of one full-period grid search — it held up out-of-sample.

**Caveats on this result:**
- This is a single train/test split, not multiple folds. It rules out the crudest form of overfitting (reporting an in-sample-only number as if it generalizes) but doesn't confirm the effect holds across every possible historical cutoff. A useful follow-up would be walking the split date back and forth (e.g. 2012, 2018) to see if RSI=75 keeps winning.
- The edge here is real but more modest than the full-period headline number suggests — the full 2005–present backtest showed RSI=75/stop=5% turning $10k into ~$96k, but that number reflects two decades of compounding, not the strength of the effect in any one stretch. The test-period comparison above ($28,574 vs $32,168) is the more honest measure of the actual edge.

## Statistical significance of the original-vs-enhanced gap

`bootstrap_test.py` checks whether original beating enhanced is a real, repeatable effect or could plausibly be noise from one 20-year history. It resamples months with replacement 5,000 times, applying the same resampled months to both strategies to keep the pairing intact.

**Important: this run tests the *default* enhanced strategy (RSI=70, stop=10%) — not the RSI=75 combo from the sensitivity/out-of-sample sections above.** It's answering a different question: "is original's edge over the naive enhanced strategy robust?", not "is the RSI=75 tuned combo's edge robust?"

Result:

| | Value |
|---|---|
| Original strategy final value | $76,857 |
| Enhanced (default: RSI=70, stop=10%) final value | $54,048 |
| Observed gap | $22,809 |
| Average bootstrap gap | $28,317 |
| 90% confidence interval | -$12,028 to $95,386 |
| P-value (chance enhanced ties/beats original) | 0.1414 |

The confidence interval crosses zero, and the p-value is well above the conventional 0.05 threshold. **This means original's outperformance over the default (untuned) enhanced strategy is not statistically robust** — it's plausible that a different 20-year stretch of history would have shown enhanced doing as well or better, purely from noise. This doesn't contradict the RSI=75 out-of-sample finding above (that's a separate, better-supported result); it's a caveat specifically about the naive RSI=70/stop=10% configuration most people would try first.

A natural follow-up: re-run this same bootstrap test but with `run_enhanced_backtest` parameterized to RSI=75/stop=5%, to see whether *that* gap (tuned enhanced vs. original) is more statistically robust than the untuned one.

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
- Adding "safety" filters (RSI, stop-loss) made things *worse* across the board at the settings most people would reach for first (RSI=70, stop=10%) — more filtering isn't automatically more robust. The only version of the filter that helped was the one that barely filtered anything.
- The one time the enhanced strategy did show a real, out-of-sample-validated edge (RSI=75/stop=5%), it wasn't from a "smarter" filter — it was from a filter so loose it mostly stayed out of the original momentum strategy's way.
- The default-parameter comparison ($22,809 gap, "enhanced looks clearly worse") and the tuned-parameter comparison (enhanced beats original out-of-sample) are both true at the same time, about the same two strategies, just at different settings. That's a good reminder that "does X help" is often the wrong question — it depends entirely on how X is configured, and a single headline number can hide that.

## Next steps

- [x] Run `out_of_sample_test.py` — RSI=75 finding held up on unseen data (see above)
- [x] Run `bootstrap_test.py` — original vs. default (untuned) enhanced is not statistically significant (p=0.14); still need to re-run with the tuned RSI=75 combo
- [x] Add drawdown/Sharpe comparison table from `drawdown_stats.py`
- [x] Add a short "what surprised me" section
- [ ] Re-run `bootstrap_test.py` with `run_enhanced_backtest` parameterized to RSI=75/stop=5%, to check whether the tuned combo's edge is statistically robust (not just out-of-sample-positive once)
- [ ] Try additional train/test split dates to check robustness of the RSI=75 result beyond a single cutoff