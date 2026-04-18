"""
Portfolio calculations: value, returns, performance metrics
"""

import pandas as pd
from datetime import datetime
from tickers import INITIAL_CAPITAL


def calculate_portfolio_value(portfolio: dict, prices: dict) -> float:
    """
    portfolio = {ticker: quantity}
    prices = {ticker: {"price": float, ...}}
    """
    total = 0.0
    for ticker, qty in portfolio.items():
        if qty > 0 and ticker in prices and prices[ticker].get("price"):
            total += qty * prices[ticker]["price"]
    return total


def portfolio_composition(portfolio: dict, prices: dict) -> pd.DataFrame:
    """
    Retorna DataFrame con composición del portafolio.
    """
    rows = []
    total = calculate_portfolio_value(portfolio, prices)

    for ticker, qty in portfolio.items():
        if qty > 0 and ticker in prices and prices[ticker].get("price"):
            price = prices[ticker]["price"]
            value = qty * price
            weight = (value / total * 100) if total > 0 else 0
            rows.append({
                "Ticker": ticker,
                "Cantidad": qty,
                "Precio": price,
                "Valor (COP)": value,
                "Peso (%)": weight,
            })
    return pd.DataFrame(rows)


def calculate_return(current_value: float, initial: float = INITIAL_CAPITAL) -> float:
    """Return as percentage"""
    if initial == 0:
        return 0.0
    return (current_value - initial) / initial * 100


def get_leaderboard(groups: dict, portfolios: dict, prices: dict) -> pd.DataFrame:
    """
    Ranking por total return.
    groups = {group_num: {...}}
    portfolios = {group_num: {ticker: qty}}
    """
    rows = []
    for key, group in groups.items():
        portfolio = portfolios.get(key, {})
        current_val = calculate_portfolio_value(portfolio, prices)
        ret = calculate_return(current_val, group.get("initial_capital", INITIAL_CAPITAL))
        rows.append({
            "Grupo": f"Grupo {group['group_number']}",
            "Nickname": group["nickname"],
            "Capitán": group["captain"],
            "Valor Actual (COP)": current_val,
            "Return Total (%)": ret,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values("Return Total (%)", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Posición"
    return df


def benchmark_return(prices_bench: dict, start_price: float) -> float:
    """COLCAP return from start_price to current"""
    if not prices_bench or not start_price:
        return 0.0
    current = prices_bench.get("price")
    if not current:
        return 0.0
    return (current - start_price) / start_price * 100
