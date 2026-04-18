"""
Capital Markets Simulator - Main App
Student-facing interface: login, trade, view portfolio
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
)

# --------- Custom CSS ---------
st.markdown("""
<style>
.stApp { background: #0e1117; }
.stat-box {
    background: #1a1a2e;
    color: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
}
.stat-label { font-size: 12px; color: #aaa; text-transform: uppercase; }
.stat-value { font-size: 26px; font-weight: bold; margin-top: 5px; }
.pos-ret { color: #4ade80; }
.neg-ret { color: #f87171; }
</style>
""", unsafe_allow_html=True)

# --------- Session State ---------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "group_info" not in st.session_state:
    st.session_state.group_info = None

# ============================================================
# LOGIN / REGISTER
# ============================================================
if not st.session_state.authenticated:
    st.title("📈 Capital Markets Simulator")
    st.caption("Maestría en Finanzas — Mercados de Capitales")

    tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Registrar Grupo"])

    with tab_login:
        st.subheader("Iniciar sesión como grupo")
        group_num = st.number_input("Número de grupo", min_value=1, max_value=50, step=1, key="login_num")
        password = st.text_input("Contraseña del grupo", type="password", key="login_pw")
        if st.button("Iniciar Sesión", type="primary"):
            info = authenticate(int(group_num), password)
            if info:
                st.session_state.authenticated = True
                st.session_state.group_info = info
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas.")

    with tab_register:
        st.subheader("Registrar nuevo grupo")
        r_num = st.number_input("Número de grupo", min_value=1, max_value=50, step=1, key="reg_num")
        r_nick = st.text_input("Nickname del grupo", placeholder="Ej: Los Toros de Wall Street")
        r_captain = st.text_input("Nombre del capitán")
        r_pw = st.text_input("Contraseña", type="password")
        r_pw2 = st.text_input("Confirmar contraseña", type="password")

        if st.button("Registrar Grupo", type="primary"):
            if not r_nick or not r_captain or not r_pw:
                st.error("❌ Completa todos los campos.")
            elif r_pw != r_pw2:
                st.error("❌ Las contraseñas no coinciden.")
            elif len(r_pw) < 4:
                st.error("❌ Contraseña muy corta (mínimo 4 caracteres).")
            else:
                ok = register_group(int(r_num), r_nick.strip(), r_captain.strip(), r_pw)
                if ok:
                    st.success(f"✅ Grupo {r_num} registrado. Ahora inicia sesión.")
                else:
                    st.error(f"❌ El grupo {r_num} ya existe.")

    st.stop()

# ============================================================
# MAIN APP (authenticated)
# ============================================================
group = st.session_state.group_info
group_num = group["group_number"]

# Header
c1, c2 = st.columns([4, 1])
with c1:
    st.title(f"📈 Grupo {group_num} — {group['nickname']}")
    st.caption(f"Capitán: {group['captain']}")
with c2:
    if st.button("Cerrar Sesión"):
        st.session_state.authenticated = False
        st.session_state.group_info = None
        st.rerun()

# Load prices
with st.spinner("Cargando precios..."):
    tickers_list = list(TRADEABLE_ASSETS.keys())
    prices = get_latest_prices(tickers_list)
    portfolio = get_portfolio(group_num)

# Calculate metrics
current_value = calculate_portfolio_value(portfolio, prices)
cash_invested = INITIAL_CAPITAL if current_value == 0 else current_value  # simplification
total_return = calculate_return(current_value, INITIAL_CAPITAL) if current_value > 0 else 0

# --------- Stats ---------
s1, s2, s3, s4 = st.columns(4)

with s1:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Capital Inicial</div>
        <div class="stat-value">${INITIAL_CAPITAL:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with s2:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Valor Actual</div>
        <div class="stat-value">${current_value:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with s3:
    ret_class = "pos-ret" if total_return >= 0 else "neg-ret"
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Return Total</div>
        <div class="stat-value {ret_class}">{total_return:+.2f}%</div>
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

st.divider()

# --------- Tabs ---------
tab_port, tab_trade, tab_hist = st.tabs(["📊 Mi Portafolio", "💱 Operar", "📜 Historial"])

# ========== PORTFOLIO TAB ==========
with tab_port:
    st.subheader("Composición del Portafolio")
    
    if not any(q > 0 for q in portfolio.values()):
        st.info("⚠️ Aún no tienes posiciones. Ve a **Operar** para hacer tu primera inversión. Recuerda: debes invertir el 100% del capital cada día.")
    else:
        comp_df = portfolio_composition(portfolio, prices)
        
        # Show as formatted table
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

        # Pie chart
        import plotly.express as px
        fig = px.pie(
            comp_df, values="Valor (COP)", names="Ticker",
            title="Distribución del Portafolio",
            hole=0.4,
        )
        fig.update_layout(paper_bgcolor="#0e1117", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

# ========== TRADE TAB ==========
with tab_trade:
    st.subheader("Realizar Operación")
    st.caption("⚠️ Regla: debes mantener el 100% invertido al cierre del día. Haz al menos un movimiento diario.")

    col_buy, col_sell = st.columns(2)

    # ----- BUY -----
    with col_buy:
        st.markdown("#### 🟢 Comprar")
        buy_ticker = st.selectbox(
            "Activo a comprar",
            options=list(TRADEABLE_ASSETS.keys()),
            format_func=lambda t: f"{t} — {TRADEABLE_ASSETS[t]['name']}",
            key="buy_ticker",
        )
        buy_price = prices.get(buy_ticker, {}).get("price")
        if buy_price:
            st.caption(f"Precio actual: **${buy_price:,.2f}** ({prices[buy_ticker]['date']})")
            buy_amount = st.number_input(
                "Monto a invertir (COP)", min_value=0, step=100_000, key="buy_amount"
            )
            buy_qty = buy_amount / buy_price if buy_price > 0 else 0
            if buy_qty > 0:
                st.caption(f"Cantidad estimada: {buy_qty:,.4f} unidades")

            if st.button("Ejecutar Compra", type="primary", key="btn_buy"):
                if buy_amount <= 0:
                    st.error("Monto debe ser mayor a 0.")
                else:
                    portfolio[buy_ticker] = portfolio.get(buy_ticker, 0) + buy_qty
                    save_portfolio(group_num, portfolio)
                    record_trade(group_num, {
                        "action": "BUY",
                        "ticker": buy_ticker,
                        "quantity": buy_qty,
                        "price": buy_price,
                        "amount": buy_amount,
                    })
                    st.success(f"✅ Compra ejecutada: {buy_qty:,.4f} de {buy_ticker}")
                    st.rerun()
        else:
            st.warning("Precio no disponible para este ticker.")

    # ----- SELL -----
    with col_sell:
        st.markdown("#### 🔴 Vender")
        held = {t: q for t, q in portfolio.items() if q > 0}
        if not held:
            st.info("No tienes posiciones para vender.")
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

            st.caption(f"Cantidad en cartera: **{current_qty:,.4f}**")
            st.caption(f"Valor actual: **${current_val:,.0f}**")

            sell_pct = st.slider("% a vender", 0, 100, 100, step=10, key="sell_pct")
            sell_qty = current_qty * sell_pct / 100
            sell_amount = sell_qty * sell_price if sell_price else 0
            st.caption(f"Recibirás: **${sell_amount:,.0f}**")

            if st.button("Ejecutar Venta", type="primary", key="btn_sell"):
                if sell_pct <= 0:
                    st.error("Selecciona un porcentaje mayor a 0.")
                else:
                    portfolio[sell_ticker] = current_qty - sell_qty
                    if portfolio[sell_ticker] < 0.0001:
                        portfolio[sell_ticker] = 0
                    save_portfolio(group_num, portfolio)
                    record_trade(group_num, {
                        "action": "SELL",
                        "ticker": sell_ticker,
                        "quantity": sell_qty,
                        "price": sell_price,
                        "amount": sell_amount,
                    })
                    st.success(f"✅ Venta ejecutada: {sell_qty:,.4f} de {sell_ticker}")
                    st.info(f"💡 Recuerda reinvertir los ${sell_amount:,.0f} — no puedes dejar efectivo al cierre.")
                    st.rerun()

# ========== HISTORY TAB ==========
with tab_hist:
    st.subheader("Historial de Operaciones")
    trades = get_trades(group_num)
    if not trades:
        st.info("Sin operaciones registradas.")
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

# ---- Footer ----
st.divider()
st.caption(f"Última actualización de precios: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
