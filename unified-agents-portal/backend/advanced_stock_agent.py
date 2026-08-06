import yfinance as yf
from ddgs import DDGS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re

class DeepStockResearcher:
    def __init__(self, db_session=None):
        self.db = db_session
        self.ddgs = DDGS()

    def get_live_data(self, ticker):
        """Fetches real-time price, history, and key stats"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            info = stock.info
            
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change_pct = ((current_price - prev_close) / prev_close) * 100
            
            # Basic Technicals
            sma_50 = hist['Close'].rolling(window=20).mean().iloc[-1] # Using 20 as proxy for short term
            sma_200 = hist['Close'].rolling(window=50).mean().iloc[-1] # Using 50 as proxy for long term (limited history)
            
            return {
                "price": current_price,
                "change_pct": round(change_pct, 2),
                "volume": hist['Volume'].iloc[-1],
                "pe_ratio": info.get('forwardPE', 'N/A'),
                "market_cap": info.get('marketCap', 'N/A'),
                "sector": info.get('sector', 'N/A'),
                "sma_short": round(sma_50, 2),
                "sma_long": round(sma_200, 2),
                "52_week_high": info.get('fiftyTwoWeekHigh', 'N/A'),
                "52_week_low": info.get('fiftyTwoWeekLow', 'N/A')
            }
        except Exception as e:
            return {"error": str(e)}

    def deep_web_search(self, ticker, company_name):
        """Performs deep search on News, Management, and Growth"""
        queries = [
            f"{company_name} stock news latest",
            f"{company_name} earnings report growth",
            f"{company_name} management CEO scandal",
            f"{ticker} stock analyst rating buy sell"
        ]
        
        results = {
            "news": [],
            "sentiment_score": 0, # -1 (Negative) to 1 (Positive)
            "key_events": []
        }
        
        try:
            for query in queries:
                search_results = self.ddgs.text(query, max_results=3)
                for res in search_results:
                    title = res.get('title', '')
                    body = res.get('body', '')
                    url = res.get('href', '')
                    
                    # Simple sentiment keyword analysis
                    score = 0
                    positive_words = ['growth', 'beat', 'surge', 'buy', 'upgrade', 'profit', 'record']
                    negative_words = ['loss', 'scandal', 'lawsuit', 'drop', 'sell', 'downgrade', 'risk']
                    
                    text = (title + " " + body).lower()
                    if any(word in text for word in positive_words): score += 1
                    if any(word in text for word in negative_words): score -= 1
                    
                    results["news"].append({"title": title, "source": url, "sentiment": score})
                    results["sentiment_score"] += score
                    
                    if any(word in title.lower() for word in ['earnings', 'ceo', 'launch', 'acquisition']):
                        results["key_events"].append(title)
            
            # Normalize sentiment
            total_news = len(results["news"])
            if total_news > 0:
                results["sentiment_score"] = max(-1, min(1, results["sentiment_score"] / total_news))
                
        except Exception as e:
            results["error"] = str(e)
            
        return results

    def analyze_and_advise(self, watchlist=None):
        """Main orchestration function"""
        if not watchlist:
            watchlist = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"] # Default watchlist
            
        report = {
            "timestamp": datetime.now().isoformat(),
            "market_summary": "",
            "recommendations": [],
            "deep_dive": {}
        }
        
        print(f"🔍 Starting Deep Research for {len(watchlist)} stocks...")
        
        top_pick = None
        top_score = -100
        
        for stock_ticker in watchlist:
            print(f"  -> Analyzing {stock_ticker}...")
            try:
                stock_info = yf.Ticker(stock_ticker)
                name = stock_info.info.get('shortName', stock_ticker)
                
                # 1. Get Live Data
                data = self.get_live_data(stock_ticker)
                if "error" in data: continue
                
                # 2. Deep Search
                search_data = self.deep_web_search(stock_ticker, name)
                
                # 3. Scoring Logic (The "Brain")
                score = 0
                reasons = []
                
                # Technical Score
                if data['price'] > data['sma_short']: score += 2; reasons.append("Price above short-term trend")
                if data['price'] > data['sma_long']: score += 3; reasons.append("Price above long-term trend")
                if data['change_pct'] > 2: score += 1; reasons.append("Strong momentum today")
                
                # Fundamental/Sentiment Score
                if isinstance(search_data.get('sentiment_score'), (int, float)):
                    score += (search_data['sentiment_score'] * 5) # Weight sentiment heavily
                    if search_data['sentiment_score'] > 0.5: reasons.append("Very positive news sentiment")
                    if search_data['sentiment_score'] < -0.5: reasons.append("Negative news detected")
                
                if data.get('pe_ratio') and data['pe_ratio'] != 'N/A' and data['pe_ratio'] < 20:
                    score += 1; reasons.append("Reasonable valuation (PE < 20)")
                
                # Determine Action
                action = "HOLD"
                if score >= 6: action = "STRONG BUY"
                elif score >= 3: action = "BUY"
                elif score <= -3: action = "SELL"
                
                stock_analysis = {
                    "ticker": stock_ticker,
                    "name": name,
                    "price": data['price'],
                    "change": f"{data['change_pct']}%",
                    "action": action,
                    "score": score,
                    "reasons": reasons,
                    "news_headlines": [n['title'] for n in search_data.get('news', [])[:3]],
                    "risks": search_data.get('key_events', [])
                }
                
                report["recommendations"].append(stock_analysis)
                
                if score > top_score and action in ["BUY", "STRONG BUY"]:
                    top_score = score
                    top_pick = stock_analysis
                    
            except Exception as e:
                print(f"Error analyzing {stock_ticker}: {e}")
        
        # Final Summary
        if top_pick:
            report["market_summary"] = f"Market shows opportunity in {top_pick['ticker']}. {top_pick['reasons'][0] if top_pick['reasons'] else 'General positive outlook'}."
            report["top_pick"] = top_pick
        else:
            report["market_summary"] = "Market conditions are mixed. No strong buy signals detected. Caution advised."
            
        return report

# Example Usage for Testing
if __name__ == "__main__":
    researcher = DeepStockResearcher()
    # Test with a small list
    result = researcher.analyze_and_advise(watchlist=["AAPL", "NVDA", "TSLA"])
    print(json.dumps(result, indent=2))
