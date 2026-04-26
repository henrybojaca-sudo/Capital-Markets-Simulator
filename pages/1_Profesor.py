"""
Panel del Profesor con funciones de reset y borrado total
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from tickers import TRADEABLE_ASSETS, BENCHMARK_TICKER, INITIAL_CAPITAL
from data_loader import get_latest_prices
from storage import (
    get_all_groups, get_portfolio, get_all_trades, get_cash,
    reset_group, reset_all_groups, delete_all_data,
)
from portfolio import (
    calculate_invested_value, portfolio_composition, calculate_return,
    get_leaderboard,
)

st.set_page_config(
    page_title="Profesor",
    page_icon="👨‍🏫",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0a0e27 0%, #141832 50%, #1a1245 100%) !important;
}
h1, h2, h3 { color: #f8fafc !important; }
.stTextInput label, .stNumberInput label { color: #cbd5e1 !important; }
.stTextInput input {
    background: rgba(10, 14, 39, 0.8) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(168, 85, 247, 0.3) !important;
    border-radius: 10px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
.reset-warning {
    background: rgba(239, 68, 68, 0.08);
    border-left: 3px solid #ef4444;
    border-radius: 8px;
    padding: 12px 16px;
    color: #fecaca;
    font-size: 13px;
    margin: 12px 0;
}
</style>
""", unsafe_allow_html=True)

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.title("👨‍🏫 Panel del Profesor")
    st.markdown("### 🔒 Acceso Restringido")
    pw = st.text_input("Contraseña de administrador", type="password")
    if st.button("Entrar"):
        admin_pw = st.secrets.get("admin_password", "profesor2026")
        if pw == admin_pw:
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.stop()

st.title("👨‍🏫 Panel del Profesor")
st.caption("Mercados de Capitales · Maestría en Finanzas")

if st.button("Cerrar Sesión"):
    st.session_state.admin_authenticated = False
    st.rerun()

with st.spinner("Cargando datos..."):
    tickers_list = list(TRADEABLE_ASSETS.keys())
    prices = get_latest_prices(tickers_list)
    bench_prices = get_latest_prices([BENCHMARK_TICKER])
    groups = get_all_groups()
    portfolios = {k: get_portfolio(int(k)) for k in groups.keys()}

total_groups = len(groups)
total_aum = sum(
    calculate_invested_value(portfolios.get(k, {}), prices) + get_cash(int(k))
    for k in groups.keys()
) if groups else 0
bench_price = bench_prices.get(BENCHMARK_TICKER, {}).get('price')

c1, c2, c3 = st.columns(3)
c1.metric("Grupos Registrados", total_groups)
c2.metric("AUM Total", f"${total_aum/1e6:.1f}M")
c3.metric("COLCAP", f"${bench_price:,.0f}" if bench_price else "N/A")

st.divider()

tab_lb, tab_detail, tab_trades, tab_admin = st.tabs([
    "🏆 Leaderboard", "📁 Detalle Grupos", "📜 Operaciones", "⚙️ Administración"
])

with tab_lb:
    st.subheader("🏆 Ranking por Total Return")
    lb = get_leaderboard(groups, portfolios, prices)
    if lb.empty:
        st.info("Aún no hay grupos registrados")
    else:
        st.dataframe(
            lb.style.format({
                "Invertido": "${:,.0f}",
                "Efectivo": "${:,.0f}",
                "Valor Total": "${:,.0f}",
                "Return (%)": "{:+.2f}%",
            }),
            use_container_width=True,
        )

with tab_detail:
    if not groups:
        st.info("Sin grupos")
    else:
        for key, g in sorted(groups.items(), key=lambda x: int(x[0])):
            portfolio = portfolios.get(key, {})
            invested_val = calculate_invested_value(portfolio, prices)
            cash_val = get_cash(int(key))
            current_val = invested_val + cash_val
            ret = calculate_return(current_val, g.get("initial_capital", INITIAL_CAPITAL))

            with st.expander(
                f"Grupo {g['group_number']} — {g['nickname']} │ Invertido: ${invested_val:,.0f} │ Cash: ${cash_val:,.0f} │ Total: ${current_val:,.0f} │ Return: {ret:+.2f}%"
            ):
                st.caption(f"Capitán: {g['captain']}")
                comp_df = portfolio_composition(portfolio, prices)
                if comp_df.empty:
                    st.info("Sin posiciones")
                else:
                    st.dataframe(
                        comp_df.style.format({
                            "Cantidad": "{:,.4f}",
                            "Precio": "${:,.2f}",
                            "Valor (COP)": "${:,.0f}",
                            "Peso (%)": "{:.2f}%",
                        }),
                        use_container_width=True,
                        hide_index=True,
                    )

with tab_trades:
    all_trades = get_all_trades()
    if not all_trades:
        st.info("Sin operaciones")
    else:
        rows = []
        for group_num, trades in all_trades.items():
            nick = groups.get(group_num, {}).get("nickname", "?")
            for t in trades:
                rows.append({
                    "Grupo": f"G{group_num} — {nick}",
                    "Fecha": t.get("timestamp", "")[:19].replace("T", " "),
                    "Acción": t["action"],
                    "Ticker": t["ticker"],
                    "Cantidad": t["quantity"],
                    "Precio": t["price"],
                    "Monto": t["amount"],
                })
        df = pd.DataFrame(rows).sort_values("Fecha", ascending=False)
        st.dataframe(
            df.style.format({
                "Cantidad": "{:,.4f}",
                "Precio": "${:,.2f}",
                "Monto": "${:,.0f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

with tab_admin:
    st.subheader("⚙️ Administración de Grupos")

    st.markdown("""
    <div class="reset-warning">
        ⚠️ <b>Resetear grupo:</b> Borra todas las posiciones, operaciones y restaura el cash a $100,000,000.
        El registro del grupo (nickname, capitán, contraseña) se mantiene.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔄 Resetear un grupo específico")
    if not groups:
        st.info("Sin grupos")
    else:
        col_sel, col_btn = st.columns([3, 1])
        with col_sel:
            group_keys = sorted(groups.keys(), key=lambda x: int(x))
            options = {
                f"Grupo {groups[k]['group_number']} — {groups[k]['nickname']}": int(k)
                for k in group_keys
            }
            selected_label = st.selectbox(
                "Selecciona el grupo a resetear",
                options=list(options.keys()),
            )
        with col_btn:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            confirm_single = st.checkbox("Confirmar", key="confirm_single")

        if st.button("🔄 Resetear este grupo", type="primary", disabled=not confirm_single):
            with st.spinner("Reseteando..."):
                reset_group(options[selected_label])
                st.success(f"✅ {selected_label} reseteado correctamente")
                st.rerun()

    st.divider()

    st.markdown("### 💣 Reset total (todos los grupos)")
    st.markdown("""
    <div class="reset-warning">
        🚨 <b>PELIGRO:</b> Esto resetea TODOS los grupos. Usar solo al inicio de una nueva semana de competencia.
    </div>
    """, unsafe_allow_html=True)

    confirm_all = st.checkbox("Confirmo que quiero resetear TODOS los grupos", key="confirm_all")
    if st.button("💣 RESETEAR TODOS LOS GRUPOS", disabled=not confirm_all):
        with st.spinner("Reseteando todos los grupos..."):
            reset_all_groups()
            st.success("✅ Todos los grupos reseteados")
            st.rerun()

    st.divider()

    st.markdown("### 🗑️ Borrado total (nueva clase)")
    st.markdown("""
    <div class="reset-warning">
        🚨 <b>BORRADO PERMANENTE:</b> Elimina TODOS los grupos registrados (nicknames, capitanes, contraseñas),
        todas las posiciones, todo el cash y todas las operaciones.
        <br><b>Usar solo cuando vayas a iniciar con una clase completamente nueva.</b>
    </div>
    """, unsafe_allow_html=True)

    confirm_delete = st.checkbox("Confirmo que quiero ELIMINAR TODOS los datos", key="confirm_delete")
    confirm_delete2 = st.checkbox("Entiendo que esto NO se puede deshacer", key="confirm_delete2")

    if st.button(
        "🗑️ ELIMINAR TODO Y EMPEZAR DE CERO",
        disabled=not (confirm_delete and confirm_delete2),
    ):
        with st.spinner("Eliminando todos los datos..."):
            delete_all_data()
            st.success("✅ Todos los datos eliminados. La app está lista para nuevos grupos.")
            st.rerun()
