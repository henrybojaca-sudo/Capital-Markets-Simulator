"""
Data Loader - Yahoo Finance integration

Todas las descargas se hacen en lote (una sola petición para todos los
tickers) y se guardan en caché, en lugar de una petición por activo.
"""

from typing import Dict, Optional

import pandas as pd
import streamlit as st
import yfinance as yf

PRICE_TTL = 300        # precios actuales: 5 minutos
HISTORY_TTL = 1800     # históricos para gráficos: 30 minutos


def _extract_closes(raw: pd.DataFrame, tickers: list) -> pd.DataFrame:
    """Devuelve un DataFrame de cierres (filas = fechas, columnas = tickers)."""
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = raw.columns.get_level_values(0)
        if "Close" in level0:
            closes = raw["Close"]
        else:  # group_by="ticker"
            closes = raw.xs("Close", axis=1, level=1)
    else:
        closes = raw[["Close"]].rename(columns={"Close": tickers[0]})
    closes = closes.copy()
    closes.index = pd.to_datetime(closes.index).tz_localize(None).normalize()
    return closes.apply(pd.to_numeric, errors="coerce")


def _download_closes(tickers: list, **kwargs) -> pd.DataFrame:
    try:
        raw = yf.download(
            tickers=list(tickers),
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
            **kwargs,
        )
        return _extract_closes(raw, list(tickers))
    except Exception as e:
        print(f"Error descargando precios en lote: {e}")
        return pd.DataFrame()


def _single_last_close(ticker: str):
    """Respaldo individual para tickers que no llegaron en el lote."""
    try:
        hist = yf.Ticker(ticker).history(period="1mo")
        hist = hist["Close"].dropna()
        if not hist.empty:
            return float(hist.iloc[-1]), hist.index[-1].strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
    return None, None


@st.cache_data(ttl=PRICE_TTL, show_spinner=False)
def get_latest_prices(tickers: list) -> Dict[str, Dict[str, Optional[float]]]:
    """Último cierre disponible de cada ticker.

    Usa el último precio válido del último mes, así un día sin datos en Yahoo
    no deja una posición valorada en 0.
    """
    tickers = list(tickers)
    closes = _download_closes(tickers, period="1mo")
    prices = {}
    for t in tickers:
        series = closes[t].dropna() if t in closes.columns else pd.Series(dtype=float)
        if not series.empty and series.iloc[-1] > 0:
            prices[t] = {
                "price": float(series.iloc[-1]),
                "date": series.index[-1].strftime("%Y-%m-%d"),
            }
        else:
            price, date = _single_last_close(t)
            prices[t] = {"price": price, "date": date}
    return prices


@st.cache_data(ttl=HISTORY_TTL, show_spinner=False)
def get_price_history(tickers: tuple, start_date: str) -> pd.DataFrame:
    """Cierres diarios desde start_date (YYYY-MM-DD) para los gráficos.

    Los huecos se rellenan con el último precio conocido.
    """
    if not tickers:
        return pd.DataFrame()
    start = (pd.to_datetime(start_date) - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    closes = _download_closes(list(tickers), start=start)
    if closes.empty:
        return closes
    return closes.sort_index().ffill()


def get_benchmark_performance(start_date: str = None) -> dict:
    """Métricas del COLCAP (ETF ICOLCAP) desde start_date o últimos días."""
    from tickers import BENCHMARK_TICKER

    try:
        if start_date:
            hist = get_price_history((BENCHMARK_TICKER,), start_date)
            if not hist.empty:
                hist = hist[hist.index >= pd.to_datetime(start_date) - pd.Timedelta(days=4)]
        else:
            hist = _download_closes([BENCHMARK_TICKER], period="5d")
        if hist.empty or BENCHMARK_TICKER not in hist.columns:
            return None
        series = hist[BENCHMARK_TICKER].dropna()
        if len(series) < 2:
            return None

        current_price = float(series.iloc[-1])
        previous_close = float(series.iloc[-2])
        day_change = (current_price - previous_close) / previous_close * 100

        if start_date:
            # Primer precio disponible desde el inicio del juego (igual que antes)
            after = series[series.index >= pd.to_datetime(start_date)]
            start_idx = after.index[0] if not after.empty else series.index[0]
        else:
            start_idx = series.index[-3] if len(series) >= 3 else series.index[0]
        start_price = float(series.loc[start_idx])
        total_change = (current_price - start_price) / start_price * 100

        return {
            "current": current_price,
            "current_date": series.index[-1].strftime("%d/%m/%Y"),
            "previous_close": previous_close,
            "day_change": day_change,
            "start_date": start_idx.strftime("%d/%m/%Y"),
            "start_price": start_price,
            "total_change": total_change,
        }
    except Exception as e:
        print(f"Error fetching benchmark performance: {e}")
        return None
