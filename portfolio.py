"""
Portfolio calculations: value = invested + cash
"""

import pandas as pd
from tickers import INITIAL_CAPITAL, TRADEABLE_ASSETS
from storage import get_cash


def _price_of(prices: dict, ticker: str):
    p = prices.get(ticker)
    if isinstance(p, dict) and p.get("price"):
        return p["price"]
    return None


def calculate_invested_value(portfolio: dict, prices: dict) -> float:
    """Value of positions only (without cash)"""
    total = 0.0
    for ticker, qty in portfolio.items():
        price = _price_of(prices, ticker)
        if qty > 0 and price:
            total += qty * price
    return total


def portfolio_composition(portfolio: dict, prices: dict) -> pd.DataFrame:
    rows = []
    total_invested = calculate_invested_value(portfolio, prices)

    for ticker, qty in portfolio.items():
        price = _price_of(prices, ticker)
        if qty > 0 and price:
            value = qty * price
            weight = (value / total_invested * 100) if total_invested > 0 else 0
            rows.append({
                "Ticker": ticker,
                "Empresa": TRADEABLE_ASSETS.get(ticker, {}).get("name", ticker),
                "Sector": TRADEABLE_ASSETS.get(ticker, {}).get("sector", "Otros"),
                "Cantidad": qty,
                "Precio": price,
                "Valor (COP)": value,
                "Peso (%)": weight,
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("Valor (COP)", ascending=False).reset_index(drop=True)
    return df


def sector_composition(comp_df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa la composición por sector."""
    if comp_df.empty:
        return comp_df
    return (
        comp_df.groupby("Sector", as_index=False)["Valor (COP)"].sum()
        .sort_values("Valor (COP)", ascending=False)
    )


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
            "% Efectivo": (cash / total * 100) if total > 0 else 0,
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


def portfolio_history(trades: list, closes: pd.DataFrame, start_date: str,
                      initial: float = INITIAL_CAPITAL) -> pd.DataFrame:
    """Reconstruye el valor diario del portafolio a partir de las operaciones.

    trades: lista de dicts con timestamp, action, ticker, quantity, price.
    closes: DataFrame de cierres diarios (filas = fechas, columnas = tickers).
    Devuelve columnas Fecha, Valor y Return (%). Es una aproximación: usa el
    cierre de cada día para valorar las posiciones al final de ese día.
    """
    if closes is None or closes.empty:
        return pd.DataFrame(columns=["Fecha", "Valor", "Return (%)"])

    df_t = pd.DataFrame(trades)
    if not df_t.empty:
        df_t["day"] = pd.to_datetime(df_t["timestamp"], errors="coerce", format="ISO8601").dt.tz_localize(None).dt.normalize()
        df_t = df_t.dropna(subset=["day"]).sort_values("day")

    start = pd.to_datetime(start_date).normalize()
    if not df_t.empty:
        start = min(start, df_t["day"].min())
    days = closes.index[closes.index >= start]
    if len(days) == 0:
        return pd.DataFrame(columns=["Fecha", "Valor", "Return (%)"])

    rows = []
    for d in days:
        holdings, last_trade_price, cash = {}, {}, float(initial)
        if not df_t.empty:
            for t in df_t[df_t["day"] <= d].itertuples():
                qty = float(t.quantity)
                amount = qty * float(t.price)
                if t.action == "BUY":
                    holdings[t.ticker] = holdings.get(t.ticker, 0.0) + qty
                    cash -= amount
                elif t.action == "SELL":
                    holdings[t.ticker] = holdings.get(t.ticker, 0.0) - qty
                    cash += amount
                last_trade_price[t.ticker] = float(t.price)
        value = cash
        for ticker, qty in holdings.items():
            if qty <= 1e-9:
                continue
            px = closes.at[d, ticker] if ticker in closes.columns else float("nan")
            if pd.isna(px):
                px = last_trade_price.get(ticker, 0.0)
            value += qty * float(px)
        rows.append({"Fecha": d, "Valor": value, "Return (%)": calculate_return(value, initial)})
    return pd.DataFrame(rows)
