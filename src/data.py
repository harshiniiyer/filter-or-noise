import datetime
import yfinance as yf
import pandas as pd
# The 6 ETFs we test the momentum across
#SPY=S&P500, QQQ
#QQQ= TEch
#IWM= Small Cap
#GLD= Gold
#TLT= Bonds
#EFA= International
TICKERS=['SPY','QQQ','IWM','GLD','TLT','EFA']
START= '2005-01-01'
END=datetime.date.today()
def get_prices():
    """Download monthly closing prices for all the EFTs."""
    data = yf.download(TICKERS, start=START, end=END,
                       auto_adjust=True, progress=False)
    prices = data['Close']
    prices = prices.dropna(how='all')
    return prices

def get_spy():
    """Download SPY separately for all the regime filter."""
    data = yf.download('SPY', start=START, end=END,
                       auto_adjust=True, progress=False)
    return data['Close'].squeeze()
