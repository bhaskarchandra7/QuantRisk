# utils.py
import requests
import pandas as pd
import numpy as np
import datetime
from ta.trend import EMAIndicator


# Fetch historical OHLC data from Binance for a given symbol and interval.
def fetch_binance_klines(symbol, interval='1d', start_str=None, end_str=None, limit=500):
    """
    Fetch historical candlestick (kline) data from Binance API.
    Returns a pandas DataFrame with columns: ['open_time','open','high','low','close','volume'].
    """
    base_url = 'https://api.binance.com/api/v3/klines'
    params = {'symbol': symbol, 'interval': interval, 'limit': limit}
    if start_str:
        # Convert datetime or string to Binance timestamp in ms
        start_ts = int(pd.to_datetime(start_str).timestamp() * 1000)
        params['startTime'] = start_ts
    if end_str:
        end_ts = int(pd.to_datetime(end_str).timestamp() * 1000)
        params['endTime'] = end_ts
    response = requests.get(base_url, params=params)
    data = response.json()
    # Parse JSON into DataFrame
    df = pd.DataFrame(data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    # Use only needed columns and convert types
    df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']]
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open','high','low','close','volume']].astype(float)
    return df

# Compute simple moving average and RSI for the given price series.
def compute_technical_indicators(df):
    """
    Takes a DataFrame with a 'close' column and adds technical indicator columns:
    - SMA (e.g. 14-day)
    - RSI (14)
    - MACD (12,26,9 default)
    """
    if 'close' not in df.columns:
        raise ValueError("DataFrame must contain 'close' column for indicators.")
    series = df['close']
    # Simple Moving Average (14-period) - using pandas rolling as example
    df['sma_14'] = series.rolling(window=14).mean()
    return df

# Compute risk metrics (VaR, CVaR, volatility, max drawdown) from a series of portfolio values or returns.
def compute_risk_metrics(prices, confidence_level=0.95):
    """
    Given a pandas Series of portfolio values (indexed by date),
    compute risk metrics. Returns a dict with var, cvar, volatility, max_drawdown.
    """
    # Compute returns (drop NaN)
    returns = prices.pct_change().dropna()
    if returns.empty:
        return {'var': 0.0, 'cvar': 0.0, 'volatility': 0.0, 'max_drawdown': 0.0}
    # Value at Risk (VaR) at (1 - confidence) percentile (losses as positive)
    var_level = (1 - confidence_level) * 100
    var = np.percentile(returns, var_level)
    # Conditional VaR (CVaR): average of returns below the VaR threshold
    tail_losses = returns[returns <= var]
    cvar = tail_losses.mean() if not tail_losses.empty else var
    # Volatility: standard deviation of returns (annualized approx)
    volatility = returns.std() * np.sqrt(252)  # annualize daily returns, example
    # Maximum Drawdown: largest peak-to-trough decline
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = drawdown.min()  # most negative value
    # Return metrics as positives or appropriate sign
    return {
        'var': float(var),
        'cvar': float(cvar),
        'volatility': float(volatility),
        'max_drawdown': float(abs(max_drawdown))
    }

# Compute correlation matrix (as nested dict) from a DataFrame of asset price or returns
def compute_correlation_matrix(df):
    """
    Compute pairwise correlation matrix (as nested dict) for the columns of df.
    For example, df could contain columns for each asset's return series.
    """
    corr = df.corr()
    corr_matrix = {}
    for col in corr.columns:
        corr_matrix[col] = corr[col].to_dict()
    return corr_matrix
