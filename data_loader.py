"""
Módulo de datos: obtiene precios de cierre desde Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st


@st.cache_data(ttl=3600)  # Cache 1 hora
def get_latest_prices(tickers: list) -> dict:
    """
    Obtiene el último precio de cierre disponible para cada ticker.
    Retorna: {ticker: {"price": float, "date": str}}
    """
    prices = {}
    for ticker in tickers:
        try:
            data = yf.Ticker(ticker).history(period="5d")
            if not data.empty:
                prices[ticker] = {
                    "price": float(data["Close"].iloc[-1]),
                    "date": data.index[-1].strftime("%Y-%m-%d"),
                }
            else:
                prices[ticker] = {"price": None, "date": None}
        except Exception as e:
            prices[ticker] = {"price": None, "date": None, "error": str(e)}
    return prices


@st.cache_data(ttl=3600)
def get_historical_prices(tickers: list, start_date: str, end_date: str = None) -> pd.DataFrame:
    """
    Obtiene precios históricos de cierre.
    """
    if end_date is None:
        end_date = datetime.today().strftime("%Y-%m-%d")

    data = yf.download(
        tickers,
        start=start_date,
        end=end_date,
        progress=False,
        auto_adjust=True,
    )

    if "Close" in data.columns.get_level_values(0):
        close = data["Close"]
    else:
        close = data

    if isinstance(close, pd.Series):
        close = close.to_frame(name=tickers[0] if isinstance(tickers, list) else tickers)

    return close


def get_price_on_date(ticker: str, date: str) -> float | None:
    """
    Obtiene el precio de cierre en una fecha específica (o más cercana anterior).
    """
    try:
        target = pd.to_datetime(date)
        start = (target - timedelta(days=7)).strftime("%Y-%m-%d")
        end = (target + timedelta(days=1)).strftime("%Y-%m-%d")

        data = yf.Ticker(ticker).history(start=start, end=end)
        if data.empty:
            return None

        data.index = data.index.tz_localize(None) if data.index.tz else data.index
        valid = data.loc[data.index <= target]
        if valid.empty:
            return None
        return float(valid["Close"].iloc[-1])
    except Exception:
        return None
