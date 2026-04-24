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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }

/* ══ TEXTO NATIVO DE STREAMLIT ═══════════════════ */
p, .stMarkdown p, [data-testid="stMarkdown"] p { font-size: 16px !important; line-height: 1.6 !important; }
[data-testid="stCaptionContainer"] p, .stCaption p { font-size: 15px !important; color: #9ba3b2 !important; }
label, .stTextInput label, .stNumberInput label,
.stTextInput label p, .stNumberInput label p {
    font-size: 14px !important; font-weight: 600 !important; letter-spacing: 0.04em !important;
}
h1, h2, h3 { font-weight: 700 !important; }

/* ══ INPUTS ══════════════════════════════════════ */
input, textarea, .stTextInput input, .stNumberInput input {
    font-size: 17px !important; padding: 12px 16px !important;
    border-radius: 8px !important;
}

/* ══ BUTTONS ═════════════════════════════════════ */
.stButton > button {
    background: #2196f3 !important; color: #fff !important;
    border: none !important; border-radius: 8px !important;
    padding: 14px 20px !important; font-size: 16px !important;
    font-weight: 700 !important; width: 100%; transition: background 0.15s;
}
.stButton > button:hover { background: #1565c0 !important; }

/* ══ TABS ════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] { border-bottom: 2px solid #2a2e39 !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] {
    font-size: 17px !important; font-weight: 600 !important;
    padding: 14px 28px !important; border: none !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"] p { font-size: 17px !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { border-bottom: 3px solid #2196f3 !important; }

/* ══ ALERTAS NATIVAS ═════════════════════════════ */
[data-testid="stAlert"] p { font-size: 15px !important; }

/* ══ STAT BOXES ══════════════════════════════════ */
.stat-box {
    background: #1e2433; border: 1px solid #2a2e39;
    border-top: 3px solid #2196f3;
    border-radius: 12px; padding: 24px 20px;
}
.stat-label {
    font-size: 12px !important; text-transform: uppercase;
    letter-spacing: 0.09em; font-weight: 700 !important;
    margin-bottom: 10px; opacity: 0.7;
}
.stat-value {
    font-size: 2.2rem !important; font-weight: 800 !important;
    line-height: 1.1; font-variant-numeric: tabular-nums;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* ══ ADMIN HEADER ════════════════════════════════ */
.admin-header {
    background: #1e2433; border: 1px solid #2a2e39;
    border-left: 4px solid #2196f3;
    border-radius: 10px; padding: 22px 26px; margin-bottom: 24px;
}
.admin-title { font-size: 1.8rem !important; font-weight: 700 !important; margin: 0; }
.admin-sub { font-size: 15px !important; margin-top: 6px; opacity: 0.7; }

/* ══ BRAND ═══════════════════════════════════════ */
.brand {
    display: flex; align-items: center; gap: 14px;
    font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem;
}
.brand-icon {
    width: 44px; height: 44px; background: #2196f3;
    border-radius: 10px; display: flex; align-items: center;
    justify-content: center; font-size: 24px;
}

/* ══ LOGIN CARD ══════════════════════════════════ */
.login-card {
    background: #1e2433; border: 1px solid #2a2e39;
    border-top: 3px solid #2196f3;
    border-radius: 12px; padding: 44px;
    max-width: 440px; margin: 60px auto;
    box-shadow: 0 20px 50px rgba(0,0,0,0.5);
}
.login-title { font-size: 1.6rem !important; font-weight: 700 !important; text-align: center; margin-bottom: 8px; }
.login-subtitle { font-size: 15px !important; text-align: center; margin-bottom: 2rem; opacity: 0.65; }
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
