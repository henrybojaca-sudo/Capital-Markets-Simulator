"""
Capital Markets Simulator - Main App
Diseño FinPulse + Control de efectivo disponible
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from tickers import TRADEABLE_ASSETS, INITIAL_CAPITAL
from data_loader import get_latest_prices
from storage import (
    register_group, authenticate, get_portfolio, save_portfolio,
    record_trade, get_trades, get_cash, decrease_cash, increase_cash,
)
from portfolio import (
    calculate_invested_value, calculate_total_value, portfolio_composition,
    calculate_return,
)

st.set_page_config(
    page_title="Capital Markets Simulator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

/* ══ BLOOMBERG TERMINAL THEME ════════════════════ */
.stApp {
    background: #000000 !important;
    font-family: 'IBM Plex Sans', sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }

h1, h2, h3 {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #e0e0e0 !important;
    letter-spacing: -0.01em;
    text-transform: uppercase;
}

/* ── Labels ──────────────────────────────────── */
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stSlider label {
    color: #F26122 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 5px !important;
}

/* ── Inputs ──────────────────────────────────── */
.stTextInput input, .stNumberInput input {
    background: #0d0d0d !important;
    border: 1px solid #1e1e1e !important;
    border-bottom: 2px solid #F26122 !important;
    border-radius: 2px !important;
    color: #e0e0e0 !important;
    padding: 11px 14px !important;
    font-size: 15px !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #F26122 !important;
    box-shadow: 0 0 0 2px rgba(242,97,34,0.18) !important;
}
.stTextInput input::placeholder, .stNumberInput input::placeholder {
    color: #3a3a3a !important; opacity: 1 !important;
}
.stSelectbox > div > div {
    background: #0d0d0d !important;
    border: 1px solid #1e1e1e !important;
    border-bottom: 2px solid #F26122 !important;
    border-radius: 2px !important;
    color: #e0e0e0 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 14px !important;
}

/* ── Buttons ─────────────────────────────────── */
.stButton > button {
    background: #F26122 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 2px !important;
    padding: 13px 22px !important;
    font-weight: 700 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 13px !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    width: 100%;
    transition: background 0.15s, box-shadow 0.15s;
}
.stButton > button:hover {
    background: #ff7a3d !important;
    box-shadow: 0 0 18px rgba(242,97,34,0.4) !important;
}
.stButton > button:disabled {
    background: #1a1a1a !important;
    color: #3a3a3a !important;
    box-shadow: none !important;
}

/* ── Brand ───────────────────────────────────── */
.brand {
    display: flex; align-items: center; gap: 14px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.3rem; font-weight: 700;
    color: #F26122; margin-bottom: 1.5rem;
    text-transform: uppercase; letter-spacing: 0.06em;
}
.brand-icon {
    width: 44px; height: 44px;
    background: #F26122;
    border-radius: 2px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
}

/* ── Hero ────────────────────────────────────── */
.hero-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.8rem !important; font-weight: 700;
    line-height: 1.05; margin-bottom: 1.2rem;
    color: #e0e0e0; text-transform: uppercase;
}
.hero-accent {
    background: linear-gradient(90deg, #F26122 0%, #00B2BB 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    color: #555555; font-size: 1rem;
    line-height: 1.7; margin-bottom: 1.8rem;
}

/* ── Category cards ──────────────────────────── */
.cat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
    gap: 6px; max-width: 540px;
}
.cat-card {
    background: #0d0d0d;
    border: 1px solid #1e1e1e;
    border-top: 2px solid;
    border-radius: 1px; padding: 14px 10px; text-align: center;
}
.cat-icon { font-size: 22px; margin-bottom: 7px; display: block; }
.cat-name {
    font-size: 10px; color: #555555; font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    text-transform: uppercase; letter-spacing: 0.06em;
}

/* ── Stat boxes ──────────────────────────────── */
.stat-box {
    background: #080808;
    border: 1px solid #1a1a1a;
    border-top: 2px solid #2a2a2a;
    border-radius: 2px; padding: 18px 20px;
}
.stat-box-cash {
    border-top-color: #F26122;
    background: #0d0800;
}
.stat-label {
    font-size: 10px; color: #F26122;
    text-transform: uppercase; letter-spacing: 0.12em;
    font-weight: 700; margin-bottom: 10px;
    font-family: 'IBM Plex Mono', monospace;
}
.stat-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: clamp(1.05rem, 2vw, 1.8rem);
    font-weight: 700; color: #e0e0e0;
    line-height: 1.1; font-variant-numeric: tabular-nums;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.pos-ret { color: #00E676 !important; }
.neg-ret { color: #FF1744 !important; }
.cash-value { color: #F26122 !important; }

/* ── Tabs ────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0; background: transparent;
    border-bottom: 1px solid #1a1a1a;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 0 !important;
    padding: 13px 26px !important;
    color: #404040 !important;
    font-weight: 600; font-size: 12px;
    font-family: 'IBM Plex Mono', monospace !important;
    text-transform: uppercase; letter-spacing: 0.08em;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #F26122 !important;
    border-bottom: 2px solid #F26122 !important;
}

/* ── Group header ────────────────────────────── */
.group-header {
    background: #080808;
    border: 1px solid #1a1a1a;
    border-left: 3px solid #F26122;
    border-radius: 2px; padding: 16px 22px; margin-bottom: 22px;
}
.group-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.3rem; font-weight: 700;
    color: #e0e0e0; margin: 0;
    text-transform: uppercase; letter-spacing: 0.03em;
}
.group-sub {
    color: #3a3a3a; font-size: 0.85rem; margin-top: 5px;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Alert boxes ─────────────────────────────── */
.rules-box {
    background: #0d0800;
    border-left: 3px solid #F26122;
    border-radius: 1px; padding: 12px 16px;
    color: #cc8844; font-size: 13px; margin: 12px 0; line-height: 1.6;
    font-family: 'IBM Plex Mono', monospace;
}
.alert-box-red {
    background: #0d0000;
    border-left: 3px solid #FF1744;
    border-radius: 1px; padding: 12px 16px;
    color: #ff4444; font-size: 13px; margin: 12px 0;
    font-family: 'IBM Plex Mono', monospace;
}
.alert-box-green {
    background: #00100a;
    border-left: 3px solid #00E676;
    border-radius: 1px; padding: 12px 16px;
    color: #00cc55; font-size: 13px; margin: 12px 0;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Form ────────────────────────────────────── */
.form-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.15rem; font-weight: 700;
    color: #e0e0e0; margin-bottom: 4px;
    text-transform: uppercase; letter-spacing: 0.04em;
}
.form-sub {
    color: #444444; font-size: 0.88rem; margin-bottom: 1.4rem;
}

/* ── Cash badge ──────────────────────────────── */
.cash-badge {
    background: #0a0600;
    border: 1px solid rgba(242,97,34,0.25);
    border-left: 3px solid #F26122;
    border-radius: 2px; padding: 14px 18px; margin-bottom: 14px;
    display: flex; justify-content: space-between; align-items: center;
}
.cash-badge-label {
    color: #F26122; font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.1em; display: block;
    font-family: 'IBM Plex Mono', monospace;
}
.cash-badge-value {
    font-family: 'IBM Plex Mono', monospace;
    color: #F26122; font-size: 1.4rem; font-weight: 700;
    font-variant-numeric: tabular-nums;
}

/* ── Footer ──────────────────────────────────── */
.footer-text {
    color: #1e1e1e; font-size: 11px; text-align: center;
    margin-top: 3rem; padding-top: 1.5rem;
    border-top: 1px solid #111111;
    font-family: 'IBM Plex Mono', monospace;
    text-transform: uppercase; letter-spacing: 0.08em;
}
</style>
""", unsafe_allow_html=True)

# Session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "group_info" not in st.session_state:
    st.session_state.group_info = None

# ============================================================
# LANDING / LOGIN (unchanged)
# ============================================================
if not st.session_state.authenticated:
    st.markdown("""
    <div class="brand">
        <div class="brand-icon">📈</div>
        <span>Capital Markets</span>
    </div>
    """, unsafe_allow_html=True)

    hero_l, hero_r = st.columns([1.2, 1])

    with hero_l:
        st.markdown("""
        <div style="padding: 10px 0;">
            <div style="font-size: 42px; margin-bottom: 12px;">💼</div>
            <h1 class="hero-title">
                Invierte, compite,<br>
                <span class="hero-accent">gana el mercado</span>
            </h1>
            <p class="hero-sub">
                Simulador con acciones reales de la BVC. Construye tu portafolio,
                compite con tus compañeros y supera al COLCAP.
            </p>
            <div class="cat-grid">
                <div class="cat-card" style="border-top-color:#ef4444;">
                    <span class="cat-icon">🛢️</span><div class="cat-name">Energía</div>
                </div>
                <div class="cat-card" style="border-top-color:#06b6d4;">
                    <span class="cat-icon">🏦</span><div class="cat-name">Financiero</div>
                </div>
                <div class="cat-card" style="border-top-color:#f59e0b;">
                    <span class="cat-icon">⚡</span><div class="cat-name">Utilities</div>
                </div>
                <div class="cat-card" style="border-top-color:#a855f7;">
                    <span class="cat-icon">🏢</span><div class="cat-name">Holdings</div>
                </div>
                <div class="cat-card" style="border-top-color:#10b981;">
                    <span class="cat-icon">💱</span><div class="cat-name">USD/COP</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with hero_r:
        tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Registrar Grupo"])

        with tab_login:
            st.markdown('<div class="form-title">🚀 Bienvenido</div><div class="form-sub">Accede con tu grupo y contraseña</div>', unsafe_allow_html=True)
            group_num = st.number_input("Número de grupo", min_value=1, max_value=50, step=1, key="login_num")
            password = st.text_input("Contraseña", type="password", key="login_pw")
            if st.button("Iniciar Sesión →", type="primary", key="btn_login"):
                info = authenticate(int(group_num), password)
                if info:
                    st.session_state.authenticated = True
                    st.session_state.group_info = info
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

        with tab_register:
            st.markdown('<div class="form-title">✨ Crea tu grupo</div><div class="form-sub">Empieza con 100 millones COP virtuales</div>', unsafe_allow_html=True)
            r_num = st.number_input("Número de grupo", min_value=1, max_value=50, step=1, key="reg_num")
            r_nick = st.text_input("Nickname del grupo", key="reg_nick", placeholder="Ej: Los Toros de Wall Street")
            r_captain = st.text_input("Nombre del capitán", key="reg_cap", placeholder="Ej: María López")
            r_pw = st.text_input("Contraseña (mínimo 4 caracteres)", type="password", key="reg_pw")
            r_pw2 = st.text_input("Confirmar contraseña", type="password", key="reg_pw2")

            if st.button("Registrar Grupo →", type="primary", key="btn_reg"):
                if not r_nick or not r_captain or not r_pw:
                    st.error("Completa todos los campos")
                elif r_pw != r_pw2:
                    st.error("Las contraseñas no coinciden")
                elif len(r_pw) < 4:
                    st.error("Contraseña muy corta (mínimo 4)")
                else:
                    ok = register_group(int(r_num), r_nick.strip(), r_captain.strip(), r_pw)
                    if ok:
                        st.success(f"✅ Grupo {r_num} registrado. Ya puedes iniciar sesión.")
                    else:
                        st.error(f"El grupo {r_num} ya existe")

    st.markdown('<div class="footer-text">20 acciones BVC · USD/COP · Benchmark COLCAP · 100M COP capital inicial</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================
# AUTHENTICATED
# ============================================================
group = st.session_state.group_info
group_num = group["group_number"]

c1, c2 = st.columns([5, 1])
with c1:
    st.markdown(f"""
    <div class="group-header">
        <div class="group-title">📈 Grupo {group_num} — {group['nickname']}</div>
        <div class="group-sub">Capitán: {group['captain']}</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    if st.button("Cerrar Sesión", key="logout"):
        st.session_state.authenticated = False
        st.session_state.group_info = None
        st.rerun()

with st.spinner("Cargando precios del mercado..."):
    tickers_list = list(TRADEABLE_ASSETS.keys())
    prices = get_latest_prices(tickers_list)
    portfolio = get_portfolio(group_num)

invested_value = calculate_invested_value(portfolio, prices)
cash = get_cash(group_num)
total_value = invested_value + cash
total_return = calculate_return(total_value, INITIAL_CAPITAL)

# 5 stat boxes: Inicial, Invertido, Efectivo, Valor Total, Return
s1, s2, s3, s4, s5 = st.columns(5)
with s1:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Capital Inicial</div>
        <div class="stat-value">${INITIAL_CAPITAL/1e6:.0f}M</div>
    </div>
    """, unsafe_allow_html=True)
with s2:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Invertido</div>
        <div class="stat-value">${invested_value/1e6:.2f}M</div>
    </div>
    """, unsafe_allow_html=True)
with s3:
    st.markdown(f"""
    <div class="stat-box stat-box-cash">
        <div class="stat-label" style="color:#fde68a;">💵 Efectivo</div>
        <div class="stat-value cash-value">${cash/1e6:.2f}M</div>
    </div>
    """, unsafe_allow_html=True)
with s4:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Valor Total</div>
        <div class="stat-value">${total_value/1e6:.2f}M</div>
    </div>
    """, unsafe_allow_html=True)
with s5:
    ret_class = "pos-ret" if total_return >= 0 else "neg-ret"
    sign = "+" if total_return >= 0 else ""
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Return</div>
        <div class="stat-value {ret_class}">{sign}{total_return:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

# Alert if cash is significant (should be close to 0 at end of day)
if cash > 1000 and any(q > 0 for q in portfolio.values()):
    st.markdown(f"""
    <div class="rules-box">
        ⚠️ Tienes <b>${cash:,.0f}</b> en efectivo sin invertir. Al cierre del día debes estar 100% invertido.
    </div>
    """, unsafe_allow_html=True)

tab_port, tab_trade, tab_hist = st.tabs(["📊 Mi Portafolio", "💱 Operar", "📜 Historial"])

# ========== PORTFOLIO ==========
with tab_port:
    if not any(q > 0 for q in portfolio.values()):
        st.markdown("""
        <div class="rules-box">
            💡 Aún no tienes posiciones. Ve a <b>Operar</b> para hacer tu primera inversión.
        </div>
        """, unsafe_allow_html=True)
    else:
        comp_df = portfolio_composition(portfolio, prices)
        st.dataframe(
            comp_df.style.format({
                "Cantidad": "{:,.0f}",
                "Precio": "${:,.2f}",
                "Valor (COP)": "${:,.0f}",
                "Peso (%)": "{:.2f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )
        import plotly.express as px
        fig = px.pie(
            comp_df, values="Valor (COP)", names="Ticker",
            hole=0.6,
            color_discrete_sequence=["#2dd4bf", "#0ea5e9", "#a855f7", "#f59e0b",
                                      "#ef4444", "#10b981", "#06b6d4", "#ec4899"],
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#cbd5e1",
            font_family="Inter",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

# ========== TRADE ==========
with tab_trade:
    # Persistent cash badge at top of trade tab
    st.markdown(f"""
    <div class="cash-badge">
        <div>
            <div class="cash-badge-label">💵 Efectivo Disponible</div>
            <div style="color:#94a3b8; font-size:11px;">Solo puedes comprar hasta este monto</div>
        </div>
        <div class="cash-badge-value">${cash:,.0f} COP</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="rules-box">
        ⚠️ Regla: debes mantener el 100% invertido al cierre del día.
    </div>
    """, unsafe_allow_html=True)

    col_buy, col_sell = st.columns(2)

    # ----- BUY -----
    with col_buy:
        st.markdown("### 🟢 Comprar")

        if cash < 100:
            st.markdown("""
            <div class="alert-box-red">
                🚫 No tienes efectivo disponible. Vende algún activo primero.
            </div>
            """, unsafe_allow_html=True)
        else:
            buy_ticker = st.selectbox(
                "Activo a comprar",
                options=list(TRADEABLE_ASSETS.keys()),
                format_func=lambda t: f"{t} — {TRADEABLE_ASSETS[t]['name']}",
                key="buy_ticker",
            )
            buy_price = prices.get(buy_ticker, {}).get("price")

            if buy_price:
                st.caption(f"💰 Precio: **${buy_price:,.2f}** ({prices[buy_ticker]['date']})")

                # Max input = cash disponible
                buy_amount = st.number_input(
                    f"Monto a invertir (máx. ${cash:,.0f})",
                    min_value=0,
                    max_value=int(cash),
                    step=100_000,
                    key="buy_amount"
                )

                # Botón "Usar todo"
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if st.button("💯 Usar todo", key="btn_all_cash"):
                        st.session_state.buy_amount = int(cash)
                        st.rerun()

                buy_qty = round(buy_amount / buy_price, 6) if buy_price > 0 else 0
                if buy_qty > 0:
                    st.caption(f"📦 Cantidad: **{buy_qty:,.4f}** unidades")

                if st.button("Ejecutar Compra →", type="primary", key="btn_buy"):
                    if buy_amount <= 0:
                        st.error("Monto debe ser mayor a 0")
                    elif buy_amount > cash:
                        st.error(f"Efectivo insuficiente. Disponible: ${cash:,.0f}")
                    else:
                        # Execute
                        ok = decrease_cash(group_num, buy_amount)
                        if ok:
                            portfolio[buy_ticker] = portfolio.get(buy_ticker, 0) + buy_qty
                            save_portfolio(group_num, portfolio)
                            record_trade(group_num, {
                                "action": "BUY", "ticker": buy_ticker,
                                "quantity": buy_qty, "price": buy_price,
                                "amount": buy_amount,
                            })
                            st.success(f"✅ Comprado: {buy_qty:,.4f} de {buy_ticker}")
                            st.rerun()
                        else:
                            st.error("Efectivo insuficiente")

    # ----- SELL -----
    with col_sell:
        st.markdown("### 🔴 Vender")
        held = {t: q for t, q in portfolio.items() if q > 0}
        if not held:
            st.info("No tienes posiciones para vender")
        else:
            sell_ticker = st.selectbox(
                "Activo a vender",
                options=list(held.keys()),
                format_func=lambda t: f"{t} — {TRADEABLE_ASSETS[t]['name']}",
                key="sell_ticker",
            )
            sell_price = prices.get(sell_ticker, {}).get("price")
            current_qty = portfolio.get(sell_ticker, 0)
            current_val = current_qty * sell_price if sell_price else 0

            st.caption(f"📦 En cartera: **{current_qty:,.4f}**")
            st.caption(f"💰 Valor: **${current_val:,.0f}**")

            sell_pct = st.slider("% a vender", 0, 100, 100, step=10, key="sell_pct")
            sell_qty = current_qty * sell_pct / 100
            sell_amount = sell_qty * sell_price if sell_price else 0
            st.caption(f"💵 Recibirás: **${sell_amount:,.0f}**")

            if st.button("Ejecutar Venta →", type="primary", key="btn_sell"):
                if sell_pct <= 0:
                    st.error("Selecciona % mayor a 0")
                else:
                    increase_cash(group_num, sell_amount)
                    portfolio[sell_ticker] = current_qty - sell_qty
                    if portfolio[sell_ticker] < 0.0001:
                        portfolio[sell_ticker] = 0
                    save_portfolio(group_num, portfolio)
                    record_trade(group_num, {
                        "action": "SELL", "ticker": sell_ticker,
                        "quantity": sell_qty, "price": sell_price,
                        "amount": sell_amount,
                    })
                    st.success(f"✅ Vendido: {sell_qty:,.4f} de {sell_ticker}")
                    st.info(f"💡 Ahora tienes ${cash + sell_amount:,.0f} para reinvertir")
                    st.rerun()

# ========== HISTORY ==========
with tab_hist:
    trades = get_trades(group_num)
    if not trades:
        st.info("📭 Sin operaciones todavía")
    else:
        df_hist = pd.DataFrame(trades)
        df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
        df_hist = df_hist.sort_values("timestamp", ascending=False)
        st.dataframe(
            df_hist.style.format({
                "quantity": "{:,.4f}",
                "price": "${:,.2f}",
                "amount": "${:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

st.markdown(f"""
<div class="footer-text">
    Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
""", unsafe_allow_html=True)
