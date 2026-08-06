from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import get_db, SessionLocal
from models_v2 import StockWatchlist, StockAnalysisHistory, Task
from advanced_stock_agent import DeepStockResearcher
from datetime import datetime

router = APIRouter()

class WatchlistCreate(BaseModel):
    name: str = "Default Watchlist"
    stocks: List[str] = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"]
    risk_tolerance: str = "moderate"
    sectors_focus: List[str] = []
    min_market_cap: float = 0

class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    stocks: Optional[List[str]] = None
    risk_tolerance: Optional[str] = None
    sectors_focus: Optional[List[str]] = None
    min_market_cap: Optional[float] = None

@router.get("/watchlists")
def get_watchlists(db: Session = Depends(get_db)):
    """Get all configured stock watchlists"""
    return db.query(StockWatchlist).all()

@router.get("/watchlists/{watchlist_id}")
def get_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    """Get a specific watchlist"""
    wl = db.query(StockWatchlist).filter(StockWatchlist.id == watchlist_id).first()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return wl

@router.post("/watchlists")
def create_watchlist(watchlist: WatchlistCreate, db: Session = Depends(get_db)):
    """Create a new stock watchlist"""
    db_wl = StockWatchlist(**watchlist.dict())
    db.add(db_wl)
    db.commit()
    db.refresh(db_wl)
    return db_wl

@router.put("/watchlists/{watchlist_id}")
def update_watchlist(watchlist_id: int, updates: WatchlistUpdate, db: Session = Depends(get_db)):
    """Update an existing watchlist"""
    db_wl = db.query(StockWatchlist).filter(StockWatchlist.id == watchlist_id).first()
    if not db_wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    for key, value in updates.dict(exclude_unset=True).items():
        setattr(db_wl, key, value)
    
    db.commit()
    db.refresh(db_wl)
    return db_wl

@router.delete("/watchlists/{watchlist_id}")
def delete_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    """Delete a watchlist"""
    db_wl = db.query(StockWatchlist).filter(StockWatchlist.id == watchlist_id).first()
    if not db_wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    db.delete(db_wl)
    db.commit()
    return {"message": "Watchlist deleted"}

@router.post("/analyze/run")
def run_deep_analysis(watchlist_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Run deep stock analysis immediately"""
    # Get watchlist
    if watchlist_id:
        wl = db.query(StockWatchlist).filter(StockWatchlist.id == watchlist_id).first()
        if not wl:
            raise HTTPException(status_code=404, detail="Watchlist not found")
        stocks = wl.stocks
    else:
        stocks = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"]
    
    # Run analysis
    researcher = DeepStockResearcher(db)
    result = researcher.analyze_and_advise(watchlist=stocks)
    
    # Store in history
    for rec in result.get("recommendations", []):
        history_entry = StockAnalysisHistory(
            task_id=None,  # Will be linked if run from a task
            ticker=rec["ticker"],
            price_at_analysis=rec.get("price"),
            recommended_action=rec.get("action"),
            reasoning=rec.get("reasons", []),
            sentiment_score=0.0  # Would need to extract from search_data
        )
        db.add(history_entry)
    
    db.commit()
    return result

@router.get("/history")
def get_analysis_history(limit: int = 50, db: Session = Depends(get_db)):
    """Get historical analysis results"""
    return db.query(StockAnalysisHistory).order_by(StockAnalysisHistory.analysis_date.desc()).limit(limit).all()

@router.get("/history/accuracy")
def get_accuracy_stats(db: Session = Depends(get_db)):
    """Calculate accuracy statistics of past recommendations"""
    history = db.query(StockAnalysisHistory).filter(
        StockAnalysisHistory.actual_price_after_1d != None
    ).all()
    
    if not history:
        return {"total_predictions": 0, "accuracy": None}
    
    correct = 0
    total = len(history)
    
    for h in history:
        if h.recommended_action == "BUY" and h.actual_price_after_1d > h.price_at_analysis:
            correct += 1
        elif h.recommended_action == "SELL" and h.actual_price_after_1d < h.price_at_analysis:
            correct += 1
        elif h.recommended_action == "HOLD":
            # Consider HOLD correct if price didn't move significantly (>5%)
            change_pct = abs((h.actual_price_after_1d - h.price_at_analysis) / h.price_at_analysis)
            if change_pct < 0.05:
                correct += 1
    
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    return {
        "total_predictions": total,
        "correct_predictions": correct,
        "accuracy_percentage": round(accuracy, 2)
    }
