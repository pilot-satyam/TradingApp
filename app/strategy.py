import pandas as pd
from pydantic import BaseModel
from app.util import fetch_stock_data
from app.sentiment_analysis import analyze_sentiment

class StockRequest(BaseModel):
    stock_symbol: str

class IndicatorData(BaseModel):
    stock_symbol: str
    indicators: dict

def calculate_rsi(data :pd.Series, window: int = 14)-> float:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_macd(data: pd.Series):
    short_ema = data.ewm(span=12, adjust=False).mean()
    long_ema = data.ewm(span=26, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd.iloc[-1], signal.iloc[-1]

def calculate_bollinger_bands(data: pd.Series, window: int = 20):
    sma = data.rolling(window=window).mean()
    std = data.rolling(window=window).std()
    upper_band = sma + (2 * std)
    lower_band = sma - (2 * std)
    return upper_band.iloc[-1], lower_band.iloc[-1]

def get_stock_indicators(stock_data: pd.DataFrame):
    indicators = {}

    indicators['short_ma'] = stock_data['Close'].rolling(window=50).mean().iloc[-1]
    indicators['long_ma'] = stock_data['Close'].rolling(window=200).mean().iloc[-1]
    indicators['rsi'] = calculate_rsi(stock_data['Close'])
    macd, signal = calculate_macd(stock_data['Close'])
    indicators['macd'] = macd
    indicators['macd_signal'] = signal
    upper_band, lower_band = calculate_bollinger_bands(stock_data['Close'])
    indicators['upper_band'] = upper_band
    indicators['lower_band'] = lower_band
    indicators['last_close'] = stock_data['Close'].iloc[-1]

    return indicators

def get_trading_signal(stock_data: pd.DataFrame):
    short_ma = stock_data['Close'].rolling(window=50).mean().iloc[-1]
    long_ma = stock_data['Close'].rolling(window=200).mean().iloc[-1]
    rsi = calculate_rsi(stock_data['Close'])

    if rsi < 30:
        return "BUY", f"RSI ({rsi:.2f}) indicates oversold conditions."
    elif rsi > 70:
        return "SELL", f"RSI ({rsi:.2f}) indicates overbought conditions."
    else:
        if short_ma > long_ma:
            return "BUY", f"Short-term MA ({short_ma:.2f}) crossed above Long-term MA ({long_ma:.2f})."
        else:
            return "HOLD", f"Short-term MA ({short_ma:.2f}) is below Long-term MA ({long_ma:.2f})."
        
def analyze_indicators(indicators: dict):
    analysis = []
    action = "HOLD"

    if indicators['rsi'] < 30:
        action = "BUY"
        analysis.append(f"RSI ({indicators['rsi']:.2f}) indicates oversold.")
    elif indicators['rsi'] > 70:
        action = "SELL"
        analysis.append(f"RSI ({indicators['rsi']:.2f}) indicates overbought.")
    else:
        analysis.append(f"RSI ({indicators['rsi']:.2f}) is neutral.")

    if indicators['short_ma'] > indicators['long_ma']:
        if action != "SELL":
            action = "BUY"
        analysis.append(f"Short MA ({indicators['short_ma']:.2f}) above Long MA ({indicators['long_ma']:.2f}).")
    else:
        if action != "BUY":
            action = "HOLD"
        analysis.append(f"Short MA ({indicators['short_ma']:.2f}) below Long MA ({indicators['long_ma']:.2f}).")

    if indicators['macd'] > indicators['macd_signal']:
        if action != "SELL":
            action = "BUY"
        analysis.append(f"MACD ({indicators['macd']:.2f}) above Signal Line ({indicators['macd_signal']:.2f}).")
    else:
        if action != "BUY":
            action = "SELL"
        analysis.append(f"MACD ({indicators['macd']:.2f}) below Signal Line ({indicators['macd_signal']:.2f}).")

    if indicators['last_close'] < indicators['lower_band']:
        action = "BUY"
        analysis.append(f"Price ({indicators['last_close']:.2f}) near or below lower Bollinger Band ({indicators['lower_band']:.2f}).")
    elif indicators['last_close'] > indicators['upper_band']:
        action = "SELL"
        analysis.append(f"Price ({indicators['last_close']:.2f}) near or above upper Bollinger Band ({indicators['upper_band']:.2f}).")
    else:
        analysis.append(f"Price ({indicators['last_close']:.2f}) between Bollinger Bands.")

    return action, analysis

#TODO: Need to decide on this
def get_enhanced_signal(stock_symbol: str):
    # Fetch data
    stock_data, volume, avg_volume = fetch_stock_data(stock_symbol)
    sentiment, titles = analyze_sentiment(stock_symbol)
    indicators = get_stock_indicators(stock_data)
    
    # Score-based decision
    score = 0
    reasons = []
    
    # Technical Rules
    if indicators["rsi"] < 30:
        score += 2
        reasons.append("Oversold (RSI < 30)")
    if indicators["short_ma"] > indicators["long_ma"]:
        score += 1
        reasons.append("Bullish MA Crossover")
    
    # Sentiment Rules
    if sentiment == "Positive":
        score += 1
        reasons.append("Positive News Sentiment")
    
    # Volume Confirmation
    if volume > avg_volume * 1.5:  # 50% higher than average
        score += 1
        reasons.append("High Volume Confirmation")
    
    # Final Decision
    if score >= 4:
        return "STRONG BUY", reasons
    elif score >= 2:
        return "BUY", reasons
    else:
        return "HOLD", reasons
    
