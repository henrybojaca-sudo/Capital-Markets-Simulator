"""
Portfolio calculations: value = invested + cash
"""

import pandas as pd
from tickers import INITIAL_CAPITAL
from storage import get_cash


def calculate_invested_value(portfolio: dict, prices: dict) -> float:
    """Value of positions only (without cash)"""
    total = 0.0
    for ticker, qty in portfolio.items():
        if qty > 0 and ticker in prices and prices[ticker].get("price"):
            total += qty * prices[ticker]["price"]
    return total


def calculate_total_value(group_number: int, portfolio: dict, prices: dict) -> float:
    """Total = invested + cash"""
    invested = calculate_invested_value(portfolio, prices)
    cash = get_cash(group_number)
    return invested + cash


def portfolio_composition(portfolio: dict, prices: dict) -> pd.DataFrame:
    rows = []
    total_invested = calculate_invested_value(portfolio, prices)

    for ticker, qty in portfolio.items():
        if qty > 0 and ticker in prices and prices[ticker].get("price"):
            price = prices[ticker]["price"]
            value = qty * price
            weight = (value / total_invested * 100) if total_invested > 0 else 0
            rows.append({
                "Ticker": ticker,
                "Cantidad": qty,
                "Precio": price,
                "Valor (COP)": value,
                "Peso (%)": weight,
            })
    return pd.DataFrame(rows)


def calculate_return(total_value: float, initial: float = INITIAL_CAPITAL) -> float:
    if initial == 0:
        return 0.0
    return (total_value - initial) / initial * 100


def get_leaderboard(groups: dict, portfolios: dict, prices: dict) -> pd.DataFrame:
    rows = []
    for key, group in groups.items():
        portfolio = portfolios.get(key, {})
        group_num = int(key)
        invested = calculate_invested_value(portfolio, prices)
        cash = get_cash(group_num)
        total = invested + cash
        ret = calculate_return(total, group.get("initial_capital", INITIAL_CAPITAL))
        rows.append({
            "Grupo": f"Grupo {group['group_number']}",
            "Nickname": group["nickname"],
            "Capitán": group["captain"],
            "Invertido": invested,
            "Efectivo": cash,
            "Valor Total": total,
            "Return (%)": ret,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df.sort_values("Return (%)", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Pos"
    return df
