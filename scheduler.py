"""
Scheduler - Envía email automático a las 11:30 PM cada día
Usa GitHub Actions como trigger (cron). Ver .github/workflows/daily_report.yml

Ejecutar manualmente:
    python scheduler.py

Como funciona en producción:
- GitHub Actions corre este script a las 11:30 PM hora Colombia (4:30 AM UTC)
- El script lee los portafolios de groups.json/portfolios.json del repo
- Calcula valores actuales con yfinance
- Envía reporte al email del profesor

NOTA: Para que GitHub Actions tenga acceso a los datos, los archivos JSON
deben commitearse al repo (la app tiene que hacer push) o usar Google Sheets
como backend compartido.
"""

import os
import sys
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from pathlib import Path

# Add parent dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tickers import TRADEABLE_ASSETS, BENCHMARK_TICKER, INITIAL_CAPITAL
import yfinance as yf


LOCAL_DB = Path(".streamlit_db")
GROUPS_FILE = LOCAL_DB / "groups.json"
PORTFOLIOS_FILE = LOCAL_DB / "portfolios.json"


def load_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def get_prices_batch(tickers):
    prices = {}
    for t in tickers:
        try:
            data = yf.Ticker(t).history(period="5d")
            if not data.empty:
                prices[t] = float(data["Close"].iloc[-1])
        except Exception as e:
            print(f"Error {t}: {e}")
    return prices


def calc_value(portfolio, prices):
    return sum(q * prices.get(t, 0) for t, q in portfolio.items() if q > 0)


def build_html(groups, portfolios, prices):
    from datetime import datetime
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Build leaderboard
    rows = []
    for key, g in groups.items():
        portfolio = portfolios.get(key, {})
        val = calc_value(portfolio, prices)
        ret = (val - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100 if INITIAL_CAPITAL > 0 else 0
        rows.append((g["group_number"], g["nickname"], g["captain"], val, ret, portfolio))

    rows.sort(key=lambda x: -x[4])

    html = f"""
    <div style="font-family:Arial; max-width:800px;">
      <div style="background:#1a1a2e; color:white; padding:20px; border-radius:6px 6px 0 0;">
        <h2 style="margin:0;">📊 Reporte Diario — Capital Markets Simulator</h2>
        <p style="margin:5px 0 0 0; font-size:12px;">Generado: {fecha}</p>
      </div>
      <div style="padding:20px; border:1px solid #ddd; border-top:none;">
        <h3>🏆 Leaderboard</h3>
        <table style="width:100%; border-collapse:collapse; font-size:13px;">
          <tr style="background:#1a1a2e; color:white;">
            <th style="padding:10px;">Pos</th><th>Grupo</th><th>Nickname</th>
            <th>Capitán</th><th>Valor</th><th>Return</th>
          </tr>
    """
    for i, (num, nick, cap, val, ret, _) in enumerate(rows, 1):
        bg = {"1": "#FFD700", "2": "#C0C0C0", "3": "#CD7F32"}.get(str(i), "#fff")
        color = "#4ade80" if ret >= 0 else "#f87171"
        html += f"""
        <tr style="background:{bg};">
          <td style="padding:8px; text-align:center; font-weight:bold;">{i}</td>
          <td style="padding:8px;">Grupo {num}</td>
          <td style="padding:8px;">{nick}</td>
          <td style="padding:8px;">{cap}</td>
          <td style="padding:8px; text-align:right;">${val:,.0f}</td>
          <td style="padding:8px; text-align:right; color:{color}; font-weight:bold;">{ret:+.2f}%</td>
        </tr>
        """
    html += "</table><h3 style='margin-top:30px;'>📁 Detalle por Grupo</h3>"

    for num, nick, cap, val, ret, portfolio in rows:
        html += f"""
        <div style="margin-top:15px; border-left:4px solid #1a1a2e; padding-left:12px;">
          <h4 style="margin:5px 0;">Grupo {num} — {nick}</h4>
          <p style="font-size:11px; margin:3px 0;">Capitán: {cap} | Valor: ${val:,.0f} | Return: {ret:+.2f}%</p>
          <table style="width:100%; border-collapse:collapse; font-size:12px;">
            <tr style="background:#2d2d44; color:white;">
              <th style="padding:6px;">Ticker</th><th>Cantidad</th><th>Precio</th><th>Valor</th><th>Peso</th>
            </tr>
        """
        positions = {t: q for t, q in portfolio.items() if q > 0}
        if not positions:
            html += "<tr><td colspan='5' style='padding:6px; color:#888;'>Sin posiciones.</td></tr>"
        else:
            for t, q in positions.items():
                p = prices.get(t, 0)
                v = q * p
                w = v / val * 100 if val > 0 else 0
                html += f"""
                <tr>
                  <td style="padding:6px; border-bottom:1px solid #eee;">{t}</td>
                  <td style="padding:6px; border-bottom:1px solid #eee; text-align:right;">{q:,.4f}</td>
                  <td style="padding:6px; border-bottom:1px solid #eee; text-align:right;">${p:,.2f}</td>
                  <td style="padding:6px; border-bottom:1px solid #eee; text-align:right;">${v:,.0f}</td>
                  <td style="padding:6px; border-bottom:1px solid #eee; text-align:right;">{w:.2f}%</td>
                </tr>
                """
        html += "</table></div>"

    html += "</div></div>"
    return html


def send_email_smtp(to_email, subject, html_body):
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender = os.environ["SENDER_EMAIL"]
    password = os.environ["SENDER_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)


def main():
    print("🚀 Iniciando reporte diario...")
    groups = load_json(GROUPS_FILE, {})
    portfolios = load_json(PORTFOLIOS_FILE, {})

    if not groups:
        print("⚠️ Sin grupos registrados.")
        return

    tickers = list(TRADEABLE_ASSETS.keys())
    prices = get_prices_batch(tickers)
    print(f"✅ Precios cargados: {len(prices)}/{len(tickers)}")

    html = build_html(groups, portfolios, prices)

    to_email = os.environ.get("PROFESSOR_EMAIL")
    if not to_email:
        print("❌ Variable PROFESSOR_EMAIL no definida.")
        return

    subject = f"📊 Reporte Diario — Capital Markets Simulator — {datetime.now().strftime('%d/%m/%Y')}"
    send_email_smtp(to_email, subject, html)
    print(f"✅ Email enviado a {to_email}")


if __name__ == "__main__":
    main()
