"""
Gráficos (Plotly) con estilo unificado para el tema oscuro de la app.

Paleta categórica validada para daltonismo sobre el fondo oscuro (#141832).
El color sigue a la entidad (grupo/serie), nunca a su posición en el ranking.
"""

import pandas as pd
import plotly.graph_objects as go

# Paleta categórica (modo oscuro), en orden fijo
SERIES = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"]
POSITIVE = "#3987e5"   # polo azul del par divergente
NEGATIVE = "#e66767"   # polo rojo del par divergente
MUTED = "#475569"      # series en segundo plano
BENCH = "#cbd5e1"      # COLCAP (referencia neutra, línea punteada)

TEXT_PRIMARY = "#f8fafc"
TEXT_SECONDARY = "#94a3b8"
GRID = "rgba(148, 163, 184, 0.15)"


def _base_layout(fig: go.Figure, height: int = 420, title: str = None) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=20, color=TEXT_PRIMARY)) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=15, color=TEXT_SECONDARY),
        height=height,
        margin=dict(l=10, r=10, t=60 if title else 20, b=10),
        hoverlabel=dict(bgcolor="#1e2433", bordercolor="#334155", font=dict(color=TEXT_PRIMARY, size=15)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(color=TEXT_SECONDARY, size=15)),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=TEXT_SECONDARY))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, tickfont=dict(color=TEXT_SECONDARY))
    return fig


def weights_bar(df: pd.DataFrame, label_col: str, value_col: str, title: str) -> go.Figure:
    """Barras horizontales de peso (%) — una sola serie, un solo color."""
    d = df.copy()
    total = d[value_col].sum()
    d["pct"] = d[value_col] / total * 100 if total > 0 else 0
    d = d.sort_values("pct", ascending=True)
    fig = go.Figure(go.Bar(
        x=d["pct"], y=d[label_col], orientation="h",
        marker=dict(color=SERIES[0], cornerradius=4),
        text=[f"{p:.1f}%" for p in d["pct"]], textposition="outside",
        textfont=dict(color=TEXT_PRIMARY, size=15),
        customdata=d[value_col],
        hovertemplate="<b>%{y}</b><br>Peso: %{x:.2f}%<br>Valor: $%{customdata:,.0f}<extra></extra>",
        cliponaxis=False,
    ))
    _base_layout(fig, height=max(260, 46 * len(d) + 80), title=title)
    fig.update_layout(bargap=0.35, showlegend=False)
    fig.update_xaxes(ticksuffix="%", range=[0, max(d["pct"].max() * 1.18, 10)])
    return fig


def performance_vs_benchmark(history: pd.DataFrame, bench: pd.Series, label: str = "Mi portafolio") -> go.Figure:
    """Return acumulado (%) del portafolio vs COLCAP."""
    fig = go.Figure()
    if bench is not None and not bench.empty:
        fig.add_trace(go.Scatter(
            x=bench.index, y=bench.values, name="COLCAP", mode="lines",
            line=dict(color=BENCH, width=2, dash="dot"),
            hovertemplate="COLCAP: %{y:+.2f}%<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=history["Fecha"], y=history["Return (%)"], name=label, mode="lines+markers",
        line=dict(color=SERIES[0], width=2), marker=dict(size=8, line=dict(color="#141832", width=2)),
        hovertemplate=f"{label}: %{{y:+.2f}}%<extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color=GRID, width=1))
    _base_layout(fig, height=420, title="Evolución vs COLCAP")
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(ticksuffix="%")
    fig.update_xaxes(tickformat="%d %b")
    return fig


def returns_by_group(lb: pd.DataFrame, bench_return: float = None) -> go.Figure:
    """Return por grupo: azul si gana, rojo si pierde; línea del COLCAP como referencia."""
    d = lb.copy()
    d["label"] = d["Grupo"] + " · " + d["Nickname"].astype(str).str.slice(0, 18)
    d = d.sort_values("Return (%)", ascending=True)
    colors = [POSITIVE if r >= 0 else NEGATIVE for r in d["Return (%)"]]
    fig = go.Figure(go.Bar(
        x=d["Return (%)"], y=d["label"], orientation="h",
        marker=dict(color=colors, cornerradius=4),
        text=[f"{r:+.2f}%" for r in d["Return (%)"]], textposition="outside",
        textfont=dict(color=TEXT_PRIMARY, size=15), cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Return: %{x:+.2f}%<extra></extra>",
    ))
    if bench_return is not None:
        fig.add_vline(x=bench_return, line=dict(color=BENCH, width=2, dash="dot"),
                      annotation_text=f"COLCAP {bench_return:+.2f}%",
                      annotation_font=dict(color=TEXT_PRIMARY, size=14),
                      annotation_position="top")
    fig.add_vline(x=0, line=dict(color=GRID, width=1))
    _base_layout(fig, height=max(300, 46 * len(d) + 100), title="Return por grupo")
    fig.update_layout(bargap=0.35, showlegend=False)
    span = max(abs(d["Return (%)"]).max(), abs(bench_return or 0), 1) * 1.3
    fig.update_xaxes(ticksuffix="%", range=[-span, span])
    return fig


def race_chart(histories: dict, bench: pd.Series, highlighted: list) -> go.Figure:
    """Carrera de grupos: los seleccionados en color (en orden de selección), el resto en gris."""
    fig = go.Figure()
    for name, h in histories.items():
        if name in highlighted or h.empty:
            continue
        fig.add_trace(go.Scatter(
            x=h["Fecha"], y=h["Return (%)"], name=name, mode="lines",
            line=dict(color=MUTED, width=1.5), showlegend=False,
            hovertemplate=f"{name}: %{{y:+.2f}}%<extra></extra>",
        ))
    if bench is not None and not bench.empty:
        fig.add_trace(go.Scatter(
            x=bench.index, y=bench.values, name="COLCAP", mode="lines",
            line=dict(color=BENCH, width=2, dash="dot"),
            hovertemplate="COLCAP: %{y:+.2f}%<extra></extra>",
        ))
    for i, name in enumerate(highlighted[: len(SERIES)]):
        h = histories.get(name)
        if h is None or h.empty:
            continue
        fig.add_trace(go.Scatter(
            x=h["Fecha"], y=h["Return (%)"], name=name, mode="lines+markers",
            line=dict(color=SERIES[i], width=2.5), marker=dict(size=8, line=dict(color="#141832", width=2)),
            hovertemplate=f"{name}: %{{y:+.2f}}%<extra></extra>",
        ))
    fig.add_hline(y=0, line=dict(color=GRID, width=1))
    _base_layout(fig, height=480, title="Carrera de grupos vs COLCAP")
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(ticksuffix="%")
    fig.update_xaxes(tickformat="%d %b")
    return fig


def benchmark_return_series(closes: pd.DataFrame, ticker: str, start_date: str) -> pd.Series:
    """Return acumulado (%) del benchmark desde start_date."""
    if closes is None or closes.empty or ticker not in closes.columns:
        return pd.Series(dtype=float)
    s = closes[ticker].dropna()
    s = s[s.index >= pd.to_datetime(start_date).normalize()]
    if s.empty:
        return s
    return (s / s.iloc[0] - 1) * 100
