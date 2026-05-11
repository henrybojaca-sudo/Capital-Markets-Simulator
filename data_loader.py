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
