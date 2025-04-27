from fastapi import FastAPI, HTTPException
import numpy as np
from app.strategy import (
    get_trading_signal, 
    get_stock_indicators, 
    analyze_indicators, 
    StockRequest,
    IndicatorData,
)
from app.util import fetch_stock_data
from app.sentiment_analysis import analyze_sentiment
from app.strategy import get_enhanced_signal

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Stock Trading Signal API!"}

@app.get("/get_signal")
def get_signal(stock_symbol: str):
    stock_data = fetch_stock_data(stock_symbol)
    signal, reason = get_trading_signal(stock_data)
    return {
        "stock_symbol": stock_symbol,
        "signal": signal,
        "reason": reason
    }

@app.post("/get_indicators")
def get_indicators(request: StockRequest):
    stock_data, todays_volume, avg_volume_20 = fetch_stock_data(request.stock_symbol)
    indicators = get_stock_indicators(stock_data)
    
    # Adding volume data
    indicators["todays_volume"] = float(todays_volume) if not np.isnan(todays_volume) else None
    indicators["avg_volume_20"] = float(avg_volume_20) if not np.isnan(avg_volume_20) else None
    
    serializable_indicators = {}
    for k, v in indicators.items():
        if hasattr(v, "item"):
            v = v.item()
        
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            serializable_indicators[k] = None
        else:
            serializable_indicators[k] = v
    
    return {
        "stock_symbol": request.stock_symbol,
        "indicators": serializable_indicators
    }


@app.post("/analyze_stock")
async def analyze_stock(indicator_data: IndicatorData):
    action, reasons = analyze_indicators(indicator_data.indicators)
    return {
        "stock": indicator_data.stock_symbol,
        "action": action,
        "reasons": reasons
    }

@app.get("/analyze_sentiment")
def get_sentiment(stock_symbol: str):
    sentiment, news_titles = analyze_sentiment(stock_symbol)
    return {
        "stock_symbol": stock_symbol,
        "sentiment": sentiment,
        "news_titles": news_titles
    }

@app.post("/final_verdict")
def final_verdict(stock_symbol: str):
    # Step 1: Fetch Historical Stock Data
    stock_data, todays_volume, avg_volume_20 = fetch_stock_data(stock_symbol)
    
    # Step 2: Get Indicators
    indicators = get_stock_indicators(stock_data)
    
    # Don't forget to add volume also to indicators
    indicators['todays_volume'] = todays_volume
    indicators['avg_volume_20'] = avg_volume_20
    
    # Step 3: Analyze Technicals
    technical_action, technical_reasons = analyze_indicators(indicators)
    
    # Step 4: Analyze Sentiment
    sentiment, news_titles = analyze_sentiment(stock_symbol)

    # Step 5: Logic for final verdict
    if technical_action == "BUY":
        if sentiment == "Positive":
            final_action = "STRONG BUY"
        elif sentiment == "Negative":
            final_action = "HOLD / CAUTION"
        else:
            final_action = "BUY"
    elif technical_action == "HOLD":
        if sentiment == "Positive":
            final_action = "SMALL BUY / WATCHLIST"
        elif sentiment == "Negative":
            final_action = "AVOID"
        else:
            final_action = "HOLD"
    else:  # technical_action == "SELL"
        if sentiment == "Positive":
            final_action = "HOLD / WAIT"
        else:
            final_action = "STRONG SELL"

    return {
        "stock_symbol": stock_symbol,
        "technical_action": technical_action,
        "technical_reasons": technical_reasons,
        "sentiment": sentiment,
        "news_titles": news_titles,
        "final_action": final_action
    }
