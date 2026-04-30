"""
Capital Markets Simulator - Main App
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from tickers import TRADEABLE_ASSETS, INITIAL_CAPITAL
from data_loader import get_latest_prices
from storage import (
    register_group, authenticate, get_portfolio, save_portfolio,
    record_trade, get_trades, get_cash, decrease_cash, increase_cash,
    _invalidate_cache,
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

.stApp {
    background: linear-gradient(135deg, #0a0e27 0%, #141832 50%, #1a1245 100%) !important;
    font-family: 'Inter', sans-serif;
}
#MainMenu, footer, header {visibility: hidden;}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif !important;
    color: #f8fafc !important;
    letter-spacing: -0.02em;
}

.stTextInput label, .stNumberInput label, .stSelectbox label, .stSlider label {
    color: #cbd5e1 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    margin-bottom: 4px !important;
}
.stTextInput input, .stNumberInput input {
    background: rgba(10, 14, 39, 0.8) !important;
    border: 1px solid rgba(148, 163, 184, 0.25) !important;
    border-radius: 10px !important;
    color: #f8fafc !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #2dd4bf !important;
    box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.15) !important;
}
.stTextInput input::placeholder, .stNumberInput input::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}
.stSelectbox > div > div {
    background: rgba(10, 14, 39, 0.8) !important;
    border: 1px solid rgba(148, 163, 184, 0.25) !important;
    border-radius: 10px !important;
    color: #f8fafc !important;
}

.stButton > button {
    background: linear-gradient(135deg, #2dd4bf 0%, #0ea5e9 100%) !important;
    color: #0a0e27 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(45, 212, 191, 0.3) !important;
}
.stButton > button:disabled {
    background: rgba(100, 116, 139, 0.3) !important;
    color: #64748b !important;
    cursor: not-allowed !important;
}

.brand {
    display: flex; align-items: center; gap: 12px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem; font-weight: 600;
    color: #2dd4bf; margin-bottom: 1rem;
}
.brand-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #2dd4bf 0%, #0ea5e9 100%);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem !important;
    font-weight: 700;
    line-height: 1.05;
    margin-bottom: 1rem;
    color: #f8fafc;
}
.hero-accent {
    background: linear-gradient(90deg, #2dd4bf 0%, #4ade80 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    color: #94a3b8; font-size: 1rem;
    line-height: 1.6; margin-bottom: 1.5rem;
}

.cat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 12px; max-width: 580px;
}
.cat-card {
    background: rgba(20, 24, 50, 0.6);
    border-radius: 12px;
    padding: 14px 10px;
    text-align: center;
    border-top: 3px solid;
}
.cat-icon { font-size: 22px; margin-bottom: 6px; display: block;}
.cat-name { font-size: 12px; color: #cbd5e1; font-weight: 500;}

.stat-box {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(20, 24, 50, 0.8) 100%);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 14px;
    padding: 18px;
}
.stat-box-cash {
    background: linear-gradient(135deg, rgba(250, 204, 21, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%);
    border: 1px solid rgba(250, 204, 21, 0.3);
}
.stat-label {
    font-size: 11px; color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 6px;
}
.stat-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.1;
}
.pos-ret { color: #4ade80 !important; }
.neg-ret { color: #f87171 !important; }
.cash-value { color: #facc15 !important; }

.stTabs [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
.stTabs [data-baseweb="tab"] {
    background: rgba(20, 24, 50, 0.6) !important;
    border-radius: 10px !important;
    padding: 10px 18px !important;
    color: #94a3b8 !important;
    font-weight: 500;
    border: 1px solid rgba(148, 163, 184, 0.1);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(45, 212, 191, 0.2) 0%, rgba(14, 165, 233, 0.2) 100%) !important;
    color: #2dd4bf !important;
    border-color: rgba(45, 212, 191, 0.3) !important;
}

.group-header {
    background: linear-gradient(135deg, rgba(45, 212, 191, 0.1) 0%, rgba(14, 165, 233, 0.05) 100%);
    border: 1px solid rgba(45, 212, 191, 0.2);
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 20px;
}
.group-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
}
.group-sub { color: #94a3b8; font-size: 0.85rem; margin-top: 2px; }

.rules-box {
    background: rgba(250, 204, 21, 0.08);
    border-left: 3px solid #facc15;
    border-radius: 8px;
    padding: 12px 16px;
    color: #fef3c7;
    font-size: 13px;
    margin: 12px 0;
}
.alert-box-red {
    background: rgba(239, 68, 68, 0.1);
    border-left: 3px solid #ef4444;
    border-radius: 8px;
    padding: 12px 16px;
    color: #fecaca;
    font-size: 13px;
    margin: 12px 0;
}

.form-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.2rem;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 4px;
}
.form-sub {
    color: #94a3b8;
    font-size: 0.85rem;
    margin-bottom: 1.2rem;
}

.cash-badge {
    background: linear-gradient(135deg, rgba(250, 204, 21, 0.15) 0%, rgba(245, 158, 11, 0.08) 100%);
    border: 1px solid rgba(250, 204, 21, 0.3);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.cash-badge-label {
    color: #fde68a;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
}
.cash-badge-value {
    font-family: 'Space Grotesk', sans-serif;
    color: #facc15;
    font-size: 1.1rem;
    font-weight: 700;
}

.footer-text {
    color: #64748b;
    font-size: 12px;
    text-align: center;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "group_info" not in st.session_state:
    st.session_state.group_info = None

# =============================================================
# LANDING / LOGIN
# =============================================================
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

# =============================================================
# AUTHENTICATED
# =============================================================
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

                # Handle "use all" flag BEFORE creating the widget
                if st.session_state.get("_use_all_cash", False):
                    default_amount = int(cash)
                    st.session_state["_use_all_cash"] = False
                else:
                    default_amount = st.session_state.get("buy_amount", 0)
                    if default_amount > int(cash):
                        default_amount = 0

                buy_amount = st.number_input(
                    f"Monto a invertir (máx. ${cash:,.0f})",
                    min_value=0,
                    max_value=int(cash),
                    value=default_amount,
                    step=100_000,
                    key="buy_amount"
                )

                if st.button("💯 Usar todo", key="btn_all_cash"):
                    st.session_state["_use_all_cash"] = True
                    st.rerun()

                buy_qty = buy_amount / buy_price if buy_price > 0 else 0
                if buy_qty > 0:
                    st.caption(f"📦 Cantidad: **{buy_qty:,.4f}** unidades")

                if st.button("Ejecutar Compra →", type="primary", key="btn_buy"):
                    if buy_amount <= 0:
                        st.error("Monto debe ser mayor a 0")
                    elif buy_amount > cash + 0.01:
                        st.error(f"Efectivo insuficiente. Disponible: ${cash:,.0f}")
                    else:
                        _invalidate_cache()
                        fresh_portfolio = get_portfolio(group_num)

                        ok = decrease_cash(group_num, buy_amount)
                        if ok:
                            fresh_portfolio[buy_ticker] = fresh_portfolio.get(buy_ticker, 0) + buy_qty
                            save_portfolio(group_num, fresh_portfolio)
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
                    _invalidate_cache()
                    fresh_portfolio = get_portfolio(group_num)
                    fresh_qty = fresh_portfolio.get(sell_ticker, 0)

                    actual_sell_qty = fresh_qty * sell_pct / 100
                    actual_sell_amount = actual_sell_qty * sell_price if sell_price else 0

                    fresh_portfolio[sell_ticker] = fresh_qty - actual_sell_qty
                    if fresh_portfolio[sell_ticker] < 0.0001:
                        fresh_portfolio[sell_ticker] = 0
                    save_portfolio(group_num, fresh_portfolio)
                    increase_cash(group_num, actual_sell_amount)
                    record_trade(group_num, {
                        "action": "SELL", "ticker": sell_ticker,
                        "quantity": actual_sell_qty, "price": sell_price,
                        "amount": actual_sell_amount,
                    })
                    st.success(f"✅ Vendido: {actual_sell_qty:,.4f} de {sell_ticker}")
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
