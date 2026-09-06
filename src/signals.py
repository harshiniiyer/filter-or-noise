def momentum_scores(prices):
    """
    12-minus-1 month momentum signal.
    Returns the %gain from 12 months ago to 1 month ago.
    Excluding the most recent month avoids short-term reversal bias --
    this is standard practice in academic momentum research.
    """
    # shift(21) =1 month ago, shift(252) = 12 months ago
    return prices.shift(21)/prices.shift(252)-1
def sma_regime(spy):
    """
    200-day SMA regime regime filter on SPY.
    Bull market=SPY above its 200-day moving average → invest
    Bear market=SPY below its 200-day moving average → stay in cash
    We use a price-based trend signal rather than VIX (a sentiment measure) because trend is backward-looking and objective.
    """
    sma_200=spy.rolling(200).mean()
    return spy>sma_200
def compute_rsi(prices,period=14):
    """RSI above 70= overbought. We filter out ETFs above 70 as they have likely already run too far and are risky to buy."""
    delta=prices.diff()
    gain=delta.clip(lower=0).rolling(period).mean()
    loss=(-delta.clip(upper=0)).rolling(period).mean()
    rs=gain/loss
    return 100-(100/(1+rs))

def trailing_stop_ok(prices, lookback_days=63, stop_pct=0.10):
    """Returns True when price is within stop_pct of its 3 month high. 63 trading days is roughly 3 months. If an EFT has dropped more than 10% from its recent peak, stop loss triggers. (do not buy)"""
    rolling_high=prices.rolling(lookback_days).max()
    return (prices/rolling_high-1)>-stop_pct