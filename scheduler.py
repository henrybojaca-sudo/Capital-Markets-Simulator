"""
Scheduler - Reporte diario por email (11:30 PM hora Colombia)

Lo ejecuta GitHub Actions (.github/workflows/daily_report.yml). Lee los datos
de la misma hoja de Google Sheets que usa la app.

Variables de entorno (GitHub → Settings → Secrets and variables → Actions):
    GCP_SERVICE_ACCOUNT  JSON completo de la cuenta de servicio de Google
    SHEET_NAME           Nombre de la hoja (por defecto "Capital Markets DB")
    SENDER_EMAIL         Correo que envía el reporte
    SENDER_PASSWORD      App Password de Gmail
    PROFESSOR_EMAIL      Correo que recibe el reporte
    SMTP_SERVER / SMTP_PORT  (opcionales, por defecto Gmail)

Cada día hábil también guarda una "foto" del cierre de cada grupo en la
pestaña Snapshots de la hoja (se crea sola). Esa foto se guarda aunque el
correo no esté configurado o falle.

Ejecutar manualmente:
    python scheduler.py            # guarda la foto y envía el correo
    python scheduler.py --dry-run  # solo genera reporte.html (no escribe nada)
"""

import html
import json
import os
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tickers import TRADEABLE_ASSETS, BENCHMARK_TICKER, INITIAL_CAPITAL  # noqa: E402

COLOMBIA = timezone(timedelta(hours=-5))


def _num(value, default=0.0):
    """Convierte valores de la hoja (con posibles separadores) a float."""
    if value in (None, ""):
        return float(default)
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace("$", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(",", "") if s.rfind(".") > s.rfind(",") else s.replace(".", "").replace(",", ".")
    elif s.count(",") > 1 or s.count(".") > 1:
        s = s.replace(",", "").replace(".", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return float(default)


def load_from_sheets():
    import gspread
    from google.oauth2.service_account import Credentials

    info = json.loads(os.environ["GCP_SERVICE_ACCOUNT"])
    creds = Credentials.from_service_account_info(info, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    sheet = gspread.authorize(creds).open(os.environ.get("SHEET_NAME") or "Capital Markets DB")

    groups = {}
    for r in sheet.worksheet("Groups").get_all_records():
        key = str(r.get("group_number", "")).strip()
        if key:
            groups[key] = {"group_number": key, "nickname": r.get("nickname", ""), "captain": r.get("captain", "")}

    portfolios = {}
    for r in sheet.worksheet("Portfolios").get_all_records():
        key, ticker, qty = str(r.get("group_number", "")).strip(), r.get("ticker"), _num(r.get("quantity"))
        if key and ticker and qty > 0:
            portfolios.setdefault(key, {})[ticker] = qty

    cash = {}
    for r in sheet.worksheet("Cash").get_all_records():
        key = str(r.get("group_number", "")).strip()
        if key:
            cash[key] = _num(r.get("cash"), INITIAL_CAPITAL)
    return sheet, groups, portfolios, cash


SNAPSHOT_TAB = "Snapshots"
SNAPSHOT_HEADER = ["date", "group_number", "invested", "cash", "total_value", "return_pct", "cash_pct"]


def save_snapshot(sheet, rows, date_str):
    """Guarda el cierre del día por grupo. Si ya existe ese día, lo reemplaza."""
    try:
        ws = sheet.worksheet(SNAPSHOT_TAB)
    except Exception:
        ws = sheet.add_worksheet(title=SNAPSHOT_TAB, rows=2000, cols=len(SNAPSHOT_HEADER))
        ws.update(values=[SNAPSHOT_HEADER], range_name="A1")

    all_rows = ws.get_all_values()
    old_data = all_rows[1:] if all_rows else []
    kept = [r for r in old_data if r and str(r[0]).strip() != date_str]
    new_rows = [[
        date_str, str(r["group_number"]),
        round(r["invested"], 2), round(r["cash"], 2), round(r["total"], 2),
        round(r["ret"], 6), round(r["cash"] / r["total"] * 100, 6) if r["total"] > 0 else 0,
    ] for r in rows]
    data = kept + new_rows
    width = len(SNAPSHOT_HEADER)
    data = [list(r) + [""] * (width - len(r)) for r in data]
    data += [[""] * width] * max(0, len(old_data) - len(data))
    if data:
        ws.update(values=data, range_name="A2", value_input_option="RAW")
    print(f"📸 Foto del {date_str} guardada para {len(new_rows)} grupos")


def get_prices(tickers):
    """Último cierre válido de cada ticker (una sola descarga en lote)."""
    import yfinance as yf

    raw = yf.download(list(tickers), period="1mo", interval="1d", auto_adjust=True,
                      progress=False, threads=True)
    prices = {}
    if raw is not None and not raw.empty:
        closes = raw["Close"]
        for t in tickers:
            if t in closes.columns:
                s = closes[t].dropna()
                if not s.empty:
                    prices[t] = float(s.iloc[-1])
    return prices


def build_rows(groups, portfolios, cash, prices):
    rows = []
    for key, g in groups.items():
        portfolio = portfolios.get(key, {})
        invested = sum(q * prices.get(t, 0) for t, q in portfolio.items())
        c = cash.get(key, INITIAL_CAPITAL)
        total = invested + c
        ret = (total - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
        rows.append({**g, "invested": invested, "cash": c, "total": total, "ret": ret, "portfolio": portfolio})
    rows.sort(key=lambda r: -r["ret"])
    return rows


def build_html(rows, prices):
    fecha = datetime.now(COLOMBIA).strftime("%d/%m/%Y %H:%M")
    e = lambda v: html.escape(str(v))  # noqa: E731
    bench = prices.get(BENCHMARK_TICKER)
    bench_txt = f" · ICOLCAP: ${bench:,.0f}" if bench else ""

    out = f"""
    <div style="font-family:Arial,sans-serif;max-width:820px;">
      <div style="background:#1a1a2e;color:white;padding:20px;border-radius:6px 6px 0 0;">
        <h2 style="margin:0;">📊 Reporte Diario — Capital Markets Simulator</h2>
        <p style="margin:5px 0 0 0;font-size:12px;">Generado: {fecha} (hora Colombia){bench_txt}</p>
      </div>
      <div style="padding:20px;border:1px solid #ddd;border-top:none;">
        <h3>🏆 Leaderboard</h3>
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <tr style="background:#1a1a2e;color:white;">
            <th style="padding:10px;">Pos</th><th>Grupo</th><th>Nickname</th><th>Capitán</th>
            <th>Efectivo</th><th>Valor total</th><th>Return</th>
          </tr>"""
    for i, r in enumerate(rows, 1):
        bg = {1: "#FFF4C2", 2: "#EEEEEE", 3: "#F6E3D3"}.get(i, "#ffffff")
        color = "#15803d" if r["ret"] >= 0 else "#b91c1c"
        cash_pct = r["cash"] / r["total"] * 100 if r["total"] > 0 else 0
        cash_flag = " ⚠️" if cash_pct > 1 else ""
        out += f"""
          <tr style="background:{bg};">
            <td style="padding:8px;text-align:center;font-weight:bold;">{i}</td>
            <td style="padding:8px;">Grupo {e(r['group_number'])}</td>
            <td style="padding:8px;">{e(r['nickname'])}</td>
            <td style="padding:8px;">{e(r['captain'])}</td>
            <td style="padding:8px;text-align:right;">${r['cash']:,.0f}{cash_flag}</td>
            <td style="padding:8px;text-align:right;">${r['total']:,.0f}</td>
            <td style="padding:8px;text-align:right;color:{color};font-weight:bold;">{r['ret']:+.2f}%</td>
          </tr>"""
    out += "</table><p style='font-size:11px;color:#666;'>⚠️ = más de 1% en efectivo (regla: 100% invertido)</p>"
    out += "<h3 style='margin-top:30px;'>📁 Detalle por Grupo</h3>"

    for r in rows:
        out += f"""
        <div style="margin-top:15px;border-left:4px solid #1a1a2e;padding-left:12px;">
          <h4 style="margin:5px 0;">Grupo {e(r['group_number'])} — {e(r['nickname'])}</h4>
          <p style="font-size:11px;margin:3px 0;">Capitán: {e(r['captain'])} | Valor: ${r['total']:,.0f} | Return: {r['ret']:+.2f}%</p>
          <table style="width:100%;border-collapse:collapse;font-size:12px;">
            <tr style="background:#2d2d44;color:white;">
              <th style="padding:6px;">Ticker</th><th>Cantidad</th><th>Precio</th><th>Valor</th><th>Peso</th>
            </tr>"""
        if not r["portfolio"]:
            out += "<tr><td colspan='5' style='padding:6px;color:#888;'>Sin posiciones.</td></tr>"
        for t, q in sorted(r["portfolio"].items(), key=lambda x: -x[1] * prices.get(x[0], 0)):
            p = prices.get(t, 0)
            v = q * p
            w = v / r["total"] * 100 if r["total"] > 0 else 0
            name = TRADEABLE_ASSETS.get(t, {}).get("name", t)
            out += f"""
            <tr>
              <td style="padding:6px;border-bottom:1px solid #eee;">{e(t)} <span style="color:#888;">{e(name)}</span></td>
              <td style="padding:6px;border-bottom:1px solid #eee;text-align:right;">{q:,.4f}</td>
              <td style="padding:6px;border-bottom:1px solid #eee;text-align:right;">${p:,.2f}</td>
              <td style="padding:6px;border-bottom:1px solid #eee;text-align:right;">${v:,.0f}</td>
              <td style="padding:6px;border-bottom:1px solid #eee;text-align:right;">{w:.2f}%</td>
            </tr>"""
        out += "</table></div>"
    out += "</div></div>"
    return out


def send_email_smtp(to_email, subject, html_body):
    smtp_server = os.environ.get("SMTP_SERVER") or "smtp.gmail.com"
    smtp_port = int(os.environ.get("SMTP_PORT") or 587)
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
    dry_run = "--dry-run" in sys.argv
    print("🚀 Iniciando reporte diario...")
    sheet, groups, portfolios, cash = load_from_sheets()
    if not groups:
        print("⚠️ Sin grupos registrados.")
        return

    tickers = list(TRADEABLE_ASSETS.keys()) + [BENCHMARK_TICKER]
    prices = get_prices(tickers)
    print(f"✅ Precios cargados: {len(prices)}/{len(tickers)}")
    rows = build_rows(groups, portfolios, cash, prices)
    body = build_html(rows, prices)

    if dry_run:
        with open("reporte.html", "w", encoding="utf-8") as f:
            f.write(body)
        print("📝 Reporte guardado en reporte.html (no se escribió ni envió nada)")
        return

    now = datetime.now(COLOMBIA)
    if now.weekday() < 5:  # lunes a viernes
        save_snapshot(sheet, rows, now.strftime("%Y-%m-%d"))
    else:
        print("📅 Fin de semana: no se guarda foto del cierre")

    to_email = os.environ.get("PROFESSOR_EMAIL")
    if not (to_email and os.environ.get("SENDER_EMAIL") and os.environ.get("SENDER_PASSWORD")):
        print("⚠️ Correo no configurado (PROFESSOR_EMAIL / SENDER_EMAIL / SENDER_PASSWORD): no se envía.")
        return

    subject = f"📊 Reporte Diario — Capital Markets Simulator — {now.strftime('%d/%m/%Y')}"
    send_email_smtp(to_email, subject, body)
    print(f"✅ Email enviado a {to_email}")


if __name__ == "__main__":
    main()
