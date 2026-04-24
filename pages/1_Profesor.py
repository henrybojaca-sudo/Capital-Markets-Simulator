"""
Página del Profesor — Panel admin con estilo FinPulse
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from tickers import TRADEABLE_ASSETS, BENCHMARK_TICKER, BENCHMARK_NAME, INITIAL_CAPITAL
from data_loader import get_latest_prices
from storage import get_all_groups, get_portfolio, get_all_trades, get_cash
from portfolio import (
    calculate_invested_value, portfolio_composition, calculate_return,
    get_leaderboard,
)
from email_sender import send_email, build_daily_report_html

st.set_page_config(
    page_title="Profesor — Admin",
    page_icon="👨‍🏫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- CSS ---
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

.brand {
    display: flex; align-items: center; gap: 12px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem; font-weight: 600;
    color: #a855f7;
    margin-bottom: 1rem;
}
.brand-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
}

.admin-header {
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(236, 72, 153, 0.08) 100%);
    border: 1px solid rgba(168, 85, 247, 0.3);
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 24px;
}
.admin-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
}
.admin-sub {color: #cbd5e1; font-size: 0.95rem; margin-top: 4px;}

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

.stTextInput input, .stNumberInput input {
    background: rgba(10, 14, 39, 0.8) !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    border-radius: 12px !important;
    color: #f8fafc !important;
    padding: 14px 16px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #a855f7 !important;
    box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.1) !important;
}
.stTextInput label, .stNumberInput label {
    color: #cbd5e1 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(168, 85, 247, 0.3) !important;
}

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
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%) !important;
    color: #a855f7 !important;
    border-color: rgba(168, 85, 247, 0.3) !important;
}

.login-card {
    background: rgba(20, 24, 50, 0.7);
    border: 1px solid rgba(168, 85, 247, 0.2);
    border-radius: 20px;
    padding: 40px;
    max-width: 450px;
    margin: 60px auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}
.login-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #f8fafc;
    text-align: center;
    margin-bottom: 8px;
}
.login-subtitle {
    color: #94a3b8;
    font-size: 0.9rem;
    text-align: center;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# Admin Login
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.markdown("""
    <div class="brand">
        <div class="brand-icon">👨‍🏫</div>
        <span>Panel Profesor</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size: 42px; text-align:center; margin-bottom: 12px;">🔒</div>
    <div class="login-title">Acceso Restringido</div>
    <div class="login-subtitle">Ingresa la contraseña de administrador</div>
    """, unsafe_allow_html=True)

    pw = st.text_input("Contraseña", type="password",
                       placeholder="Contraseña de administrador")
    if st.button("Entrar →", type="primary"):
        admin_pw = st.secrets.get("admin_password", "")
        if not admin_pw:
            st.error("admin_password no configurado en secrets.toml")
        elif pw == admin_pw:
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ============================================================
# DASHBOARD
# ============================================================
c1, c2 = st.columns([5, 1])
with c1:
    st.markdown("""
    <div class="admin-header">
        <div class="admin-title">👨‍🏫 Panel del Profesor</div>
        <div class="admin-sub">Mercados de Capitales · Maestría en Finanzas</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
    if st.button("Cerrar Sesión"):
        st.session_state.admin_authenticated = False
        st.rerun()

# Load data
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
)
bench_price = bench_prices[BENCHMARK_TICKER].get('price')

s1, s2, s3 = st.columns(3)
with s1:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">Grupos Registrados</div>
        <div class="stat-value">{total_groups}</div>
    </div>
    """, unsafe_allow_html=True)
with s2:
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">AUM Total</div>
        <div class="stat-value">${total_aum/1e6:.1f}M</div>
    </div>
    """, unsafe_allow_html=True)
with s3:
    val_str = f"${bench_price:,.0f}" if bench_price else "N/A"
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-label">COLCAP (ICOLCAP)</div>
        <div class="stat-value">{val_str}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

tab_lb, tab_detail, tab_email, tab_trades = st.tabs([
    "🏆 Leaderboard", "📁 Detalle Grupos", "📧 Enviar Reporte", "📜 Operaciones"
])

with tab_lb:
    st.subheader("🏆 Ranking por Total Return")
    lb = get_leaderboard(groups, portfolios, prices)
    if lb.empty:
        st.info("Aún no hay grupos registrados")
    else:
        def highlight_top(row):
            if row.name == 1:
                return ["background-color: rgba(250, 204, 21, 0.2); color: #facc15; font-weight:bold"] * len(row)
            elif row.name == 2:
                return ["background-color: rgba(203, 213, 225, 0.15); color: #cbd5e1; font-weight:600"] * len(row)
            elif row.name == 3:
                return ["background-color: rgba(251, 146, 60, 0.15); color: #fb923c; font-weight:600"] * len(row)
            return [""] * len(row)

        st.dataframe(
            lb.style
              .apply(highlight_top, axis=1)
              .format({
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
                st.caption(f"Capitán: {g['captain']} · Registrado: {g['created_at'][:10]}")
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

with tab_email:
    st.subheader("📧 Enviar Reporte Diario")
    to_email = st.text_input("Email destino", value=st.secrets.get("professor_email", ""))
    st.caption("Incluye leaderboard completo + detalle de cada grupo con posiciones.")

    if st.button("📤 Enviar Reporte", type="primary"):
        if not to_email:
            st.error("Ingresa un email destino")
        else:
            with st.spinner("Enviando..."):
                lb = get_leaderboard(groups, portfolios, prices)
                portfolios_detail = {}
                for key, g in groups.items():
                    portfolios_detail[key] = {
                        "group_info": g,
                        "composition_df": portfolio_composition(portfolios.get(key, {}), prices),
                    }
                html = build_daily_report_html(lb, portfolios_detail)
                subject = f"📊 Reporte Diario — Capital Markets Simulator — {datetime.now().strftime('%d/%m/%Y')}"
                ok = send_email(to_email, subject, html)
                if ok:
                    st.success("✅ Reporte enviado")
                else:
                    st.error("❌ Error enviando. Revisa SMTP en secrets.toml")

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
