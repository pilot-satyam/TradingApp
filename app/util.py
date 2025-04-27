import yfinance as yf
import pandas as pd

def fetch_stock_data(stock_symbol: str,period: str = "1y", interval: str = "1d"):
    stock = yf.Ticker(stock_symbol)
    # stock_data = stock.history(period="1y")
    data = stock.history(period=period, interval=interval)
    if data.empty:
        raise ValueError(f"No data found for symbol: {stock_symbol}")
    #Calculating average volume of 20 days
    data['AvgVolume20'] = data['Volume'].rolling(window=20).mean()
    #Today's live data
    todays_volume = data['Volume'].iloc[-1]
    avg_volume_20 = data['AvgVolume20'].iloc[-1]
    return data, todays_volume, avg_volume_20