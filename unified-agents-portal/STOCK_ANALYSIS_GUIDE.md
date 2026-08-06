# 🚀 Deep Stock Analysis Agent - Complete Setup Guide

## ✅ What's Been Built

Your **Advanced Stock Analysis Agent** is now fully operational with:

### 🔍 Core Capabilities
1. **Live Market Data** - Fetches real-time prices from Yahoo Finance
2. **Deep Web Search** - Searches news, earnings, management updates via DuckDuckGo
3. **Sentiment Analysis** - Analyzes news sentiment (positive/negative)
4. **Technical Indicators** - Calculates moving averages, momentum
5. **Automated Scoring** - Ranks stocks based on multiple factors
6. **Learning System** - Stores historical predictions for accuracy tracking
7. **Configurable Watchlists** - Create custom stock lists via dashboard

---

## 📊 How It Works

### Analysis Process (Automatic)
```
1. Fetch Live Price Data → Yahoo Finance API
2. Search Web News → DuckDuckGo (earnings, management, scandals)
3. Sentiment Scoring → Keyword analysis (-1 to +1)
4. Technical Analysis → Moving averages, momentum
5. Valuation Check → PE ratio analysis
6. Generate Score → Combine all factors
7. Recommend Action → BUY / SELL / HOLD
8. Store Results → Database for learning
```

### Scoring Algorithm
- **Price above short-term trend**: +2 points
- **Price above long-term trend**: +3 points
- **Strong daily momentum (>2%)**: +1 point
- **Positive news sentiment**: Up to +5 points
- **Reasonable valuation (PE < 20)**: +1 point

**Actions:**
- **STRONG BUY**: Score ≥ 6
- **BUY**: Score ≥ 3
- **HOLD**: Score between -3 and 3
- **SELL**: Score ≤ -3

---

## 🎯 API Endpoints

### 1. Create Watchlist
```bash
curl -X POST http://localhost:8000/api/stocks/watchlists \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Tech Stocks",
    "stocks": ["AAPL", "MSFT", "NVDA"],
    "risk_tolerance": "moderate",
    "sectors_focus": ["Technology"],
    "min_market_cap": 100
  }'
```

### 2. Run Deep Analysis
```bash
# Using specific watchlist
curl -X POST "http://localhost:8000/api/stocks/analyze/run?watchlist_id=1"

# Using default list
curl -X POST http://localhost:8000/api/stocks/analyze/run
```

### 3. View History
```bash
curl http://localhost:8000/api/stocks/history
```

### 4. Check Accuracy Stats
```bash
curl http://localhost:8000/api/stocks/history/accuracy
```

### 5. Update Watchlist
```bash
curl -X PUT http://localhost:8000/api/stocks/watchlists/1 \
  -H "Content-Type: application/json" \
  -d '{
    "stocks": ["AAPL", "TSLA", "AMD", "GOOGL"]
  }'
```

---

## 🖥️ Dashboard Integration

### Frontend UI Features (Coming Soon)
The dashboard will include:
- **Watchlist Manager**: Add/remove stocks visually
- **Analysis Results Table**: See BUY/HOLD/SELL recommendations
- **News Feed**: Latest headlines for each stock
- **Accuracy Chart**: Track prediction success rate
- **Schedule Settings**: Configure daily run time

---

## ⏰ Automated Daily Schedule

To schedule the agent to run daily after market hours (4:30 PM EST):

### Option 1: Via Dashboard Tasks Tab
1. Go to **Tasks** tab in dashboard
2. Click **+ New Task**
3. Fill in:
   - Name: `Daily Stock Analysis`
   - Agent: Select your stock agent
   - Schedule: `30 16 * * 1-5` (Weekdays at 4:30 PM)

### Option 2: Via API
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Post-Market Analysis",
    "agent_id": YOUR_AGENT_ID,
    "schedule": "30 16 * * 1-5"
  }'
```

---

## 🧠 Learning & Improvement

### How Learning Works
1. **Store Predictions**: Every analysis is saved with price at time of recommendation
2. **Track Outcomes**: System can compare predicted vs actual prices later
3. **Calculate Accuracy**: Measures how often BUY recommendations went up, SELL went down
4. **Improve Scoring**: Future versions will auto-adjust weights based on accuracy

### View Your Accuracy
```bash
curl http://localhost:8000/api/stocks/history/accuracy
```

Response:
```json
{
  "total_predictions": 50,
  "correct_predictions": 32,
  "accuracy_percentage": 64.0
}
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| `advanced_stock_agent.py` | Core analysis engine with live data & search |
| `models_v2.py` | Database models for watchlists & history |
| `routes/stock_routes.py` | API endpoints for stock features |
| `main.py` | Updated to include stock routes |
| `models.py` | Updated init_db to create new tables |

---

## 🔧 Customization Options

### Adjust Scoring Weights
Edit `advanced_stock_agent.py`, line ~135:
```python
if data['price'] > data['sma_short']: score += 2  # Change weight here
if data['price'] > data['sma_long']: score += 3   # Change weight here
score += (search_data['sentiment_score'] * 5)     # Change sentiment weight
```

### Change Default Watchlist
Edit line ~95 in `advanced_stock_agent.py`:
```python
watchlist = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"]
```

### Modify Buy/Sell Thresholds
Edit lines ~148-151 in `advanced_stock_agent.py`:
```python
if score >= 6: action = "STRONG BUY"  # Change threshold
elif score >= 3: action = "BUY"
elif score <= -3: action = "SELL"
```

---

## 🚨 Important Notes

### Data Sources
- **Prices**: Yahoo Finance (free, delayed 15 min)
- **News**: DuckDuckGo Search (free, no API key needed)
- **No API Keys Required** for basic functionality!

### Limitations
- Market data has 15-minute delay (free tier)
- Sentiment analysis uses simple keyword matching
- No options/futures analysis
- Historical accuracy tracking requires manual price updates (future enhancement)

### Best Practices
1. **Review Before Acting**: Always verify recommendations with your own research
2. **Diversify**: Don't rely on single agent for all investments
3. **Monitor Performance**: Check accuracy stats regularly
4. **Update Watchlists**: Keep your stock list relevant to your strategy

---

## 🎉 Quick Start Test

Run this now to see it in action:
```bash
# 1. Create watchlist
curl -X POST http://localhost:8000/api/stocks/watchlists \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "stocks": ["AAPL", "NVDA", "TSLA"]}'

# 2. Run analysis
curl -X POST "http://localhost:8000/api/stocks/analyze/run?watchlist_id=LAST_ID"

# 3. See results
curl http://localhost:8000/api/stocks/history | python -m json.tool
```

---

## 📞 Support & Next Steps

### Ready to Use
✅ Backend running on port 8000  
✅ Deep analysis working  
✅ Watchlists configurable  
✅ History tracking active  

### Next Enhancements (Optional)
- [ ] Add frontend UI for stock dashboard
- [ ] Integrate paid APIs for real-time data
- [ ] Add machine learning for better sentiment
- [ ] Email/SMS alerts for strong buy signals
- [ ] Portfolio tracking integration

**Your autonomous stock analyst is ready to work for you!** 🚀📈
