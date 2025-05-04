import urllib.parse
from textblob import TextBlob
import yfinance as yf
from datetime import datetime, timedelta
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

#TODO: Move this to a config file
NEWS_API_KEY = "b9615c22162c4ab8a9667822d0bc2e85"

def get_company_name(stock_symbol: str) -> str:
    try:
        stock = yf.Ticker(stock_symbol)
        info = stock.info
        print(f"Company Info: {info}") 
        return info.get("longName",stock_symbol)
    except:
        print(f"Error fetching company name for {stock_symbol}: {e}")
        return stock_symbol

# def fetch_news(stock_symbol: str):
#     company_name = get_company_name(stock_symbol)
#     clean_symbol = stock_symbol.split('.')[0]  # Remove suffix like .NS
#     query = f'"{company_name}" OR "{clean_symbol}" AND (stock OR market OR earnings)'
#     today = datetime.now().strftime("%Y-%m-%d")
#     last_week = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
#     url = (
#         f"https://newsapi.org/v2/everything?"
#         f"q={query}&"
#         # f"from={last_week}&"
#         # f"to={today}&"
#         f"sortBy=publishedAt&"
#         f"apiKey={NEWS_API_KEY}&"
#         f"language=en"
#     )
#     response = requests.get(url)
#     print(f"News API Response: {response.status_code}, {response.json()}") 
#     data = response.json()
#     return data.get("articles", [])

def fetch_news(stock_symbol: str):
    company_name = get_company_name(stock_symbol)
    clean_symbol = stock_symbol.split('.')[0]  # Remove suffix like .NS
    query = f"{company_name} OR {clean_symbol} stock"
    encoded_query = urllib.parse.quote(query)  # Encode the query string
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    print(f"Fetching news from Google News RSS with query: {query}")
    print(f"Encoded Request URL: {url}")
    
    feed = feedparser.parse(url)
    articles = []
    
    for entry in feed.entries[:12]:  # Limit to top 12 articles
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.published
        })
    
    if not articles:
        print(f"No articles found for query: {query}")
        return [{"title": "No relevant news articles found."}]
    
    return articles

def analyze_sentiment(stock_symbol: str):
    analyzer = SentimentIntensityAnalyzer()
    company_name = get_company_name(stock_symbol)
    articles = fetch_news(stock_symbol)

    if not articles or articles[0].get("title") == "No relevant news articles found.":
        return "Neutral", ["No relevant news articles found."]
    
    sentiments = []
    titles = []

    # Analyze sentiment of top articles
    for article in articles:
        title = article['title']
        if title not in titles:  # Avoid duplicate titles
            titles.append(title)
            sentiment_score = analyzer.polarity_scores(title)['compound']
            sentiments.append(sentiment_score)
    
    if not sentiments:  # Handle case where no valid sentiments are found
        return "Neutral", titles

    avg_sentiment = sum(sentiments) / len(sentiments)
    print(f"Sentiment scores: {sentiments}") 

    if avg_sentiment > 0.1:
        return "Positive", titles
    elif avg_sentiment < -0.1:
        return "Negative", titles
    else:
        return "Neutral", titles