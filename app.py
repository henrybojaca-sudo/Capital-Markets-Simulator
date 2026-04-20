"""
Capital Markets Simulator - Main App
Diseño inspirado en FinPulse: gradiente oscuro, acentos turquesa, tarjetas con bordes de color
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from tickers import TRADEABLE_ASSETS, INITIAL_CAPITAL
from data_loader import get_latest_prices
from storage import (
    register_group, authenticate, get_portfolio, save_portfolio,
    record_trade, get_trades,
)
from portfolio import (
    calculate_portfolio_value, portfolio_composition, calculate_return,
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
h1 {font-weight: 700 !important; font-size: 2.5rem !important;}
h2 {font-weight: 600 !important;}

.brand {
    display: flex; align-items: center; gap: 12px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem; font-weight: 600;
    color: #2dd4bf;
    margin-bottom: 1rem;
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
    font-size: 3.2rem !important;
    font-weight: 700;
    line-height: 1.05;
    margin-bottom: 1.2rem;
    color: #f8fafc;
}
.hero-accent {
    background: linear-gradient(90deg, #2dd4bf 0%, #4ade80 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    color: #94a3b8;
    font-size: 1.05rem;
    line-height: 1.6;
    margin-bottom: 2rem;
}

.cat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
    gap: 14px;
    margin-top: 2rem;
    max-width: 620px;
}
.cat-card {
    background: rgba(20, 24, 50, 0.6);
    border-radius: 12px;
    padding: 16px 12px;
    text-align: center;
    border-top: 3px solid;
    transition: transform 0.2s;
    backdrop-filter: blur(10px);
}
.cat-card:hover { transform: translateY(-3px); }
.cat-icon { font-size: 22px; margin-bottom: 8px; display: block;}
.cat-name { font-size: 12px; color: #cbd5e1; font-weight: 500; line-height: 1.3;}

.login-card {
    background: rgba(20, 24, 50, 0.7);
    border: 1px solid rgba(45, 212, 191, 0.15);
    border-radius: 20px;
    padding: 32px;
    backdrop-filter: blur(20px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.login-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem;
    font-weight: 600;
    color: #f8fafc;
    margin-bottom: 6px;
}
.login-subtitle {
    color: #94a3b8;
    font-size: 0.9rem;
    margin-bottom: 1.5rem;
}

.stTextInput input, .stNumberInput input {
    background: rgba(10, 14, 39, 0.8) !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    border-radius: 12px !important;
    color: #f8fafc !important;
    padding: 14px 16px !important;
    font-size: 14px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #2dd4bf !important;
    box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.1) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #2dd4bf 0%, #0ea5e9 100%) !important;
    color: #0a0e27 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(45, 212, 191, 0.3) !important;
}

.stat-box {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(20, 24, 50, 0.8) 100%);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 16px;
    padding: 24px;
}
.stat-label {
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 8px;
}
.stat-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.1;
}
.pos-ret { color: #4ade80 !important; }
.neg-ret { color: #f87171 !important; }

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
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 24px;
}
.group-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
}
.group-sub { color: #94a3b8; font-size: 0.9rem; margin-top: 4px; }

.footer-text {
    color: #64748b;
    font-size: 12px;
    text-align: center;
    margin-top: 2rem;
}

.rules-box {
    background: rgba(250, 204, 21, 0.08);
    border-left: 3px solid #facc15;
    border-radius: 8px;
    padding: 12px 16px;
    color: #fef3c7;
    font-size: 13px;
    margin: 12px 0;
}
</style>
""", unsafe_allow_html=True)

# Session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "group_info" not in st.session_state:
    st.session_state.group_info = None

# ============================================================
# LANDING / LOGIN
# ============================================================
if not st.session_state.authenticated:
    top_l, top_r = st.columns([5, 1])
    with top_l:
        st.markdown("""
        <div class="brand">
            <div class="brand-icon">📈</div>
            <span>Capital Markets</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)

    hero_l, hero_r = st.columns([1.2, 1])

    with hero_l:
        st.markdown("""
        <div style="padding: 20px 0;">
            <div style="font-size: 48px; margin-bottom: 16px;">💼</div>
            <h1 class="hero-title">
                Invierte, compite,<br>
                <span class="hero-accent">gana el mercado</span>
            </h1>
            <p class="hero-sub">
                Simulador de mercado con acciones reales de la BVC. Construye tu
                portafolio, compite con tus compañeros y supera al COLCAP.
            </p>
            <div class="cat-grid">
                <div class="cat-card" style="border-top-color:#ef4444;">
                    <span class="cat-icon">🛢️</span>
                    <div class="cat-name">Energía</div>
                </div>
                <div class="cat-card" style="border-top-color:#06b6d4;">
                    <span class="cat-icon">🏦</span>
                    <div class="cat-name">Financiero</div>
                </div>
                <div class="cat-card" style="border-top-color:#f59e0b;">
                    <span class="cat-icon">⚡</span>
                    <div class="cat-name">Utilities</div>
                </div>
                <div class="cat-card" style="border-top-color:#a855f7;">
                    <span class="cat-icon">🏢</span>
                    <div class="cat-name">Holdings</div>
                </div>
                <div class="cat-card" style="border-top-color:#10b981;">
                    <span class="cat-icon">💱</span>
                    <div class="cat-name">USD/COP</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with hero_r:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Registrar"])

        with tab_login:
            st.markdown("""
            <div class="login-title">🚀 Bienvenido de vuelta</div>
            <div class="login-subtitle">Accede con tu grupo y contraseña</div>
            """, unsafe_allow_html=True)

            group_num = st.number_input(
                "Número de grupo", min_value=1, max_value=50, step=1,
                key="login_num", label_visibility="collapsed",
                placeholder="Número de grupo"
            )
            password = st.text_input(
                "Contraseña", type="password",
                key="login_pw", label_visibility="collapsed",
                placeholder="Contraseña del grupo"
            )
            if st.button("Iniciar Sesión →", type="primary", key="btn_login"):
                info = authenticate(int(group_num), password)
                if info:
                    st.session_state.authenticated = True
                    st.session_state.group_info = info
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

        with tab_register:
            st.markdown("""
            <div class="login-title">✨ Crea tu grupo</div>
            <div class="login-subtitle">Empieza con 100 millones COP virtuales</div>
            """, unsafe_allow_html=True)

            r_num = st.number_input(
                "Número de grupo", min_value=1, max_value=50, step=1,
                key="reg_num", label_visibility="collapsed",
                placeholder="Número de grupo"
            )
            r_nick = st.text_input(
                "Nickname", key="reg_nick", label_visibility="collapsed",
                placeholder="Nickname del grupo"
            )
            r_captain = st.text_input(
                "Capitán", key="reg_cap", label_visibility="collapsed",
                placeholder="Nombre del capitán"
            )
            r_pw = st.text_input(
                "Contraseña", type="password",
                key="reg_pw", label_visibility="collapsed",
                placeholder="Contraseña (mín. 4)"
            )
            r_pw2 = st.text_input(
                "Confirmar", type="password",
                key="reg_pw2", label_visibility="collapsed",
                placeholder="Confirmar contraseña"
            )

            if st.button("Registrar Grupo →", type="primary", key="btn_reg"):
                if not r_nick or not r_captain or not r_pw:
                    st.error("Completa todos los campos")
                elif r_pw != r_pw2:
                    st.error("Las contraseñas no coinciden")
                elif len(r_pw) < 4:
                    st.error("Contraseña muy corta (mín. 4)")
                else:
                    ok = register_group(int(r_num), r_nick.strip(), r_captain.strip(), r_pw)
                    if ok:
                        st.success(f"✅ Grupo {r_num} registrado")
                    else:
                        st.error(f"El grupo {r_num} ya existe")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="footer-text">
        20 acciones BVC · USD/COP · Benchmark COLCAP · 100M COP capital inicial
    </div>
    """, unsafe_allow_html=True)

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

current_value = calculate_portfolio_value(portfolio, prices)
total_return = calculate_return(current_value, INITIAL_CAPITAL) if current_value > 0 else 0

s1, s2, s3, s4 = st.columns(4)
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
        <div class="stat-label">Valor Actual</div>
        <div class="stat-value">${current_value/1e6:.2f}M</div>
    </div>
    """, unsafe_allow_html=True)
with s3:
    ret_class = "pos-ret" if total_return >= 0 else "neg-ret"
    sign = "+" if total_return >= 0 else ""
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Return Total</div>
        <div class="stat-value {ret_class}">{sign}{total_return:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)
with s4:
    num_pos = sum(1 for q in portfolio.values() if q > 0)
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Posiciones</div>
        <div class="stat-value">{num_pos}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

tab_port, tab_trade, tab_hist = st.tabs(["📊 Mi Portafolio", "💱 Operar", "📜 Historial"])

with tab_port:
    if not any(q > 0 for q in portfolio.values()):
        st.markdown("""
        <div class="rules-box">
            💡 Aún no tienes posiciones. Ve a <b>Operar</b> para hacer tu primera inversión.
            Recuerda: debes invertir el 100% del capital cada día.
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
            showlegend=True,
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

with tab_trade:
    st.markdown("""
    <div class="rules-box">
        ⚠️ Regla: debes mantener el 100% invertido al cierre del día.
    </div>
    """, unsafe_allow_html=True)

    col_buy, col_sell = st.columns(2)

    with col_buy:
        st.markdown("### 🟢 Comprar")
        buy_ticker = st.selectbox(
            "Activo a comprar",
            options=list(TRADEABLE_ASSETS.keys()),
            format_func=lambda t: f"{t} — {TRADEABLE_ASSETS[t]['name']}",
            key="buy_ticker",
        )
        buy_price = prices.get(buy_ticker, {}).get("price")
        if buy_price:
            st.caption(f"💰 Precio: **${buy_price:,.2f}** ({prices[buy_ticker]['date']})")
            buy_amount = st.number_input(
                "Monto COP", min_value=0, step=100_000, key="buy_amount"
            )
            buy_qty = buy_amount / buy_price if buy_price > 0 else 0
            if buy_qty > 0:
                st.caption(f"📦 Cantidad: **{buy_qty:,.4f}**")

            if st.button("Ejecutar Compra →", type="primary", key="btn_buy"):
                if buy_amount <= 0:
                    st.error("Monto debe ser > 0")
                else:
                    portfolio[buy_ticker] = portfolio.get(buy_ticker, 0) + buy_qty
                    save_portfolio(group_num, portfolio)
                    record_trade(group_num, {
                        "action": "BUY", "ticker": buy_ticker,
                        "quantity": buy_qty, "price": buy_price, "amount": buy_amount,
                    })
                    st.success(f"✅ {buy_qty:,.4f} de {buy_ticker}")
                    st.rerun()

    with col_sell:
        st.markdown("### 🔴 Vender")
        held = {t: q for t, q in portfolio.items() if q > 0}
        if not held:
            st.info("No tienes posiciones")
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
                    st.error("Selecciona % > 0")
                else:
                    portfolio[sell_ticker] = current_qty - sell_qty
                    if portfolio[sell_ticker] < 0.0001:
                        portfolio[sell_ticker] = 0
                    save_portfolio(group_num, portfolio)
                    record_trade(group_num, {
                        "action": "SELL", "ticker": sell_ticker,
                        "quantity": sell_qty, "price": sell_price, "amount": sell_amount,
                    })
                    st.success(f"✅ Venta: {sell_qty:,.4f} de {sell_ticker}")
                    st.info(f"💡 Reinvierte los ${sell_amount:,.0f}")
                    st.rerun()

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
