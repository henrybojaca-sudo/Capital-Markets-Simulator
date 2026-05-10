"""
Data Loader - Yahoo Finance integration
Fetches real-time prices for BVC stocks using correct Yahoo Finance symbols
"""

import yfinance as yf
import streamlit as st
from typing import Dict, Optional


@st.cache_data(ttl=300)
def get_latest_prices(tickers: list) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Fetch latest prices from Yahoo Finance.
    
    Args:
        tickers: List of internal ticker symbols (e.g., ["ECOPETROL.CL", "CIBEST.CL"])
    
    Returns:
        Dict with structure:
        {
            "ECOPETROL.CL": {"price": 2620.0, "date": "2025-05-10"},
            "CIBEST.CL": {"price": 74000.0, "date": "2025-05-10"},
            ...
        }
    """
    from tickers import TRADEABLE_ASSETS
    
    prices = {}
    
    for ticker in tickers:
        try:
            # Get the Yahoo Finance symbol from TRADEABLE_ASSETS config
            asset_info = TRADEABLE_ASSETS.get(ticker, {})
            yahoo_symbol = asset_info.get("yahoo_symbol", ticker)
            
            # Fetch price data from Yahoo Finance
            yf_ticker = yf.Ticker(yahoo_symbol)
            hist = yf_ticker.history(period="5d")
            
            if not hist.empty:
                last_price = hist["Close"].iloc[-1]
                last_date = hist.index[-1].strftime("%Y-%m-%d")
                prices[ticker] = {
                    "price": float(last_price),
                    "date": last_date
                }
            else:
                # No data available
                prices[ticker] = {
                    "price": None,
                    "date": None
                }
                
        except Exception as e:
            # Error fetching data
            print(f"Error fetching price for {ticker} (yahoo: {yahoo_symbol}): {e}")
            prices[ticker] = {
                "price": None,
                "date": None
            }
    
    return prices


def get_benchmark_price() -> Optional[float]:
    """
    Fetch COLCAP index price.
    
    Returns:
        Current COLCAP value or None if unavailable
    """
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
