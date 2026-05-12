"""
Data Loader - Yahoo Finance integration
"""

import yfinance as yf
import streamlit as st
from typing import Dict, Optional


@st.cache_data(ttl=300)
def get_latest_prices(tickers: list) -> Dict[str, Dict[str, Optional[float]]]:
    """Fetch latest prices from Yahoo Finance."""
    prices = {}
    
    for ticker in tickers:
        try:
            yf_ticker = yf.Ticker(ticker)
            hist = yf_ticker.history(period="5d")
            
            if not hist.empty:
                last_price = hist["Close"].iloc[-1]
                last_date = hist.index[-1].strftime("%Y-%m-%d")
                prices[ticker] = {
                    "price": float(last_price),
                    "date": last_date
                }
            else:
                prices[ticker] = {"price": None, "date": None}
                
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            prices[ticker] = {"price": None, "date": None}
    
    return prices


def get_benchmark_price() -> Optional[float]:
    """Fetch COLCAP index price."""
    from tickers import BENCHMARK_TICKER
    
    try:
        yf_ticker = yf.Ticker(BENCHMARK_TICKER)
        hist = yf_ticker.history(period="1d")
        
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return None
        
    except Exception as e:
        print(f"Error fetching benchmark: {e}")
        return None
def get_benchmark_performance() -> dict:
    """
    Get COLCAP performance metrics.
    
    Returns:
        dict with: {
            'current': float,
            'previous_close': float,
            'day_change': float (percentage),
            'start_date': str,
            'start_price': float,
            'total_change': float (percentage)
        }
    """
    from tickers import BENCHMARK_TICKER
    
    try:
        yf_ticker = yf.Ticker(BENCHMARK_TICKER)
        # Get last 30 days to calculate changes
        hist = yf_ticker.history(period="30d")
        
        if hist.empty or len(hist) < 2:
            return None
        
        # Current price (last available)
        current_price = float(hist["Close"].iloc[-1])
        
        # Previous close (day before)
        previous_close = float(hist["Close"].iloc[-2])
        day_change = ((current_price - previous_close) / previous_close) * 100
        
        # Start price (30 days ago or earliest available)
        start_price = float(hist["Close"].iloc[0])
        start_date = hist.index[0].strftime("%Y-%m-%d")
        total_change = ((current_price - start_price) / start_price) * 100
        
        return {
            'current': current_price,
            'previous_close': previous_close,
            'day_change': day_change,
            'start_date': start_date,
            'start_price': start_price,
            'total_change': total_change,
        }
        
    except Exception as e:
        print(f"Error fetching benchmark performance: {e}")
        return None
