import requests
from textblob import TextBlob
import yfinance as yf

#TODO: Move this to a config file
NEWS_API_KEY = "b9615c22162c4ab8a9667822d0bc2e85"

def get_company_name(stock_symbol: str) -> str:
    try:
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        print(f"Company Info: {info}")  # Debugging line
        return info.get("longName",stock_symbol)
    except:
        print(f"Error fetching company name for {stock_symbol}: {e}")
        return stock_symbol

def fetch_news(stock_symbol: str):
    url = f"https://newsapi.org/v2/everything?q={stock_symbol}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=en"
    response = requests.get(url)
    print(f"News API Response: {response.status_code}, {response.json()}") 
    data = response.json()
    return data.get("articles", [])

def analyze_sentiment(stock_symbol: str):
    company_name = get_company_name(stock_symbol)
    articles = fetch_news(company_name)

    if not articles:
        return "Neutral", []
    
    sentiments = []
    titles = []

    #analyzing top5 articles
    for article in articles[:12]:
        title = article['title']
        titles.append(title)
        blob = TextBlob(title)
        sentiments.append(blob.sentiment.polarity)
    avg_sentiment = sum(sentiments) / len(sentiments)

    if avg_sentiment > 0.1:
        return "Positive", titles
    elif avg_sentiment < -0.1:
        return "Negative", titles
    else:
        return "Neutral", titles