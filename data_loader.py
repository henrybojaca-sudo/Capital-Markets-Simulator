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


def get_benchmark_performance(start_date: str = None) -> dict:
    """
    Get COLCAP performance metrics.
    
    Args:
        start_date: Optional start date in 'YYYY-MM-DD' format for total_change calculation
    
    Returns:
        dict with benchmark metrics or None if error
    """
    from tickers import BENCHMARK_TICKER
    
    try:
        yf_ticker = yf.Ticker(BENCHMARK_TICKER)
        
        # Determine period based on start_date
        if start_date:
            # Get data from start_date to now
            hist = yf_ticker.history(start=start_date)
        else:
            # Default: last 5 days
            hist = yf_ticker.history(period="5d")
        
        if hist.empty or len(hist) < 2:
            return None
        
        # Current price (most recent)
        current_price = float(hist["Close"].iloc[-1])
        current_date = hist.index[-1].strftime("%d/%m/%Y")
        
        # Previous close (day before)
        previous_close = float(hist["Close"].iloc[-2])
        day_change = ((current_price - previous_close) / previous_close) * 100
        
        # Start price and total change
        if start_date and len(hist) > 2:
            # Use first available price after start_date
            start_price = float(hist["Close"].iloc[0])
            start_date_formatted = hist.index[0].strftime("%d/%m/%Y")
            total_change = ((current_price - start_price) / start_price) * 100
        else:
            # Fallback: use 2 days ago
            start_idx = -3 if len(hist) >= 3 else -2
            start_price = float(hist["Close"].iloc[start_idx])
            start_date_formatted = hist.index[start_idx].strftime("%d/%m/%Y")
            total_change = ((current_price - start_price) / start_price) * 100
        
        return {
            'current': current_price,
            'current_date': current_date,
            'previous_close': previous_close,
            'day_change': day_change,
            'start_date': start_date_formatted,
            'start_price': start_price,
            'total_change': total_change,
        }
        
    except Exception as e:
        print(f"Error fetching benchmark performance: {e}")
        return None


def get_benchmark_performance_auto() -> dict:
    """
    Get COLCAP performance with automatic start date (last 7 days).
    """
    from tickers import BENCHMARK_TICKER
    
    try:
        yf_ticker = yf.Ticker(BENCHMARK_TICKER)
        
        # Get last 7 days of data
        hist = yf_ticker.history(period="7d")
        
        if hist.empty or len(hist) < 2:
            return None
        
        # Current price (most recent)
        current_price = float(hist["Close"].iloc[-1])
        
        # Previous close (day before)
        previous_close = float(hist["Close"].iloc[-2])
        day_change = ((current_price - previous_close) / previous_close) * 100
        
        # Start price (oldest in 7 days)
        start_price = float(hist["Close"].iloc[0])
        start_date = hist.index[0].strftime("%d/%m/%Y")
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
