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


# ---------------------------------------------------------------
# Métricas de riesgo (panel del profesor)
# ---------------------------------------------------------------
TRADING_DAYS = 252
_MIN_STD = 1e-6  # por debajo, la variación es ruido de redondeo y las razones se disparan


def value_series_from_snapshots(snaps: pd.DataFrame, group_key: str) -> pd.Series:
    """Serie diaria de valor total de un grupo a partir de las fotos del cierre."""
    if snaps is None or snaps.empty:
        return pd.Series(dtype=float)
    g = snaps[snaps["group_number"] == str(group_key)]
    if g.empty:
        return pd.Series(dtype=float)
    s = g.groupby(g["date"].dt.normalize())["total_value"].last().sort_index()
    return s[s > 0]


def risk_metrics(values: pd.Series, bench: pd.Series, rf_annual: float = 0.0,
                 initial: float = INITIAL_CAPITAL) -> dict:
    """Métricas de riesgo/retorno a partir del valor diario del portafolio.

    values: valor total por fecha (cierre). bench: precio del benchmark por fecha.
    rf_annual: tasa libre de riesgo efectiva anual (ej. 0.09 = 9%).
    Con pocos días las métricas anualizadas son poco estables: es normal.
    """
    nan = float("nan")
    out = {"Días": 0, "Return (%)": nan, "Volatilidad anual (%)": nan, "Sharpe": nan,
           "Beta": nan, "Alpha anual (%)": nan, "Max drawdown (%)": nan,
           "Tracking error (%)": nan, "Information ratio": nan}
    if values is None or len(values) == 0:
        return out
    values = values.sort_index().astype(float)
    out["Días"] = int(len(values))
    out["Return (%)"] = (values.iloc[-1] / initial - 1) * 100

    curve = pd.concat([pd.Series([initial]), values.reset_index(drop=True)])
    out["Max drawdown (%)"] = float(((curve / curve.cummax()) - 1).min() * 100)

    # El capital inicial se ubica en la sesión anterior al primer cierre,
    # para que el primer día también cuente como rendimiento diario.
    if bench is not None and len(bench) > 0:
        prev = bench.index[bench.index < values.index[0]]
        if len(prev):
            values = pd.concat([pd.Series([float(initial)], index=[prev[-1]]), values])

    rp = values.pct_change().dropna()
    rf_d = (1 + rf_annual) ** (1 / TRADING_DAYS) - 1
    if len(rp) >= 2 and rp.std(ddof=1) > _MIN_STD:
        sd = rp.std(ddof=1)
        out["Volatilidad anual (%)"] = sd * TRADING_DAYS ** 0.5 * 100
        out["Sharpe"] = (rp.mean() - rf_d) / sd * TRADING_DAYS ** 0.5

    if bench is not None and len(bench) > 1:
        rb = bench.sort_index().astype(float).pct_change()
        df = pd.concat([rp.rename("p"), rb.rename("b")], axis=1, join="inner").dropna()
        if len(df) >= 2 and df["b"].std(ddof=1) > _MIN_STD:
            beta = df["p"].cov(df["b"]) / df["b"].var(ddof=1)
            out["Beta"] = beta
            out["Alpha anual (%)"] = ((df["p"].mean() - rf_d) - beta * (df["b"].mean() - rf_d)) * TRADING_DAYS * 100
            active = df["p"] - df["b"]
            te = active.std(ddof=1)
            if te > _MIN_STD:
                out["Tracking error (%)"] = te * TRADING_DAYS ** 0.5 * 100
                out["Information ratio"] = active.mean() / te * TRADING_DAYS ** 0.5
    return out
