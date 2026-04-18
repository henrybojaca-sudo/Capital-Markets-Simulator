"""
Email sender - sends daily reports to professor at 11:30 PM
Uses SMTP with credentials from Streamlit secrets
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Requires in .streamlit/secrets.toml:
      [email]
      smtp_server = "smtp.gmail.com"
      smtp_port = 587
      sender_email = "your@gmail.com"
      sender_password = "app password"
    """
    try:
        cfg = st.secrets["email"]
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cfg["sender_email"]
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"]) as server:
            server.starttls()
            server.login(cfg["sender_email"], cfg["sender_password"])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def build_daily_report_html(leaderboard_df, portfolios_detail: dict) -> str:
    """
    leaderboard_df: DataFrame from portfolio.get_leaderboard()
    portfolios_detail: {group_num: {"group_info": {...}, "composition_df": DataFrame}}
    """
    from datetime import datetime
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    html = f"""
    <div style="font-family:Arial, sans-serif; max-width:800px;">
      <div style="background:#1a1a2e; color:white; padding:20px; border-radius:6px 6px 0 0;">
        <h2 style="margin:0;">📊 Reporte Diario — Capital Markets Simulator</h2>
        <p style="margin:5px 0 0 0; font-size:12px;">Generado: {fecha}</p>
      </div>

      <div style="padding:20px; border:1px solid #ddd; border-top:none;">
        <h3 style="color:#1a1a2e;">🏆 Leaderboard</h3>
        {_df_to_html(leaderboard_df)}

        <h3 style="color:#1a1a2e; margin-top:30px;">📁 Detalle por Grupo</h3>
    """

    for key, data in portfolios_detail.items():
        info = data["group_info"]
        comp_df = data["composition_df"]
        html += f"""
        <div style="margin-top:20px; border-left:4px solid #1a1a2e; padding-left:15px;">
          <h4 style="margin:5px 0;">Grupo {info['group_number']} — {info['nickname']}</h4>
          <p style="margin:3px 0; font-size:12px;">Capitán: {info['captain']}</p>
          {_df_to_html(comp_df) if not comp_df.empty else '<p style="color:#888;">Sin posiciones.</p>'}
        </div>
        """

    html += """
      </div>
    </div>
    """
    return html


def _df_to_html(df) -> str:
    if df is None or df.empty:
        return ""
    return df.to_html(
        classes="data",
        float_format=lambda x: f"{x:,.2f}",
        border=0,
        justify="center",
    ).replace(
        '<table border="0" class="dataframe data">',
        '<table style="border-collapse:collapse; font-family:Arial; font-size:12px; width:100%;">'
    ).replace(
        '<th>',
        '<th style="background:#1a1a2e; color:white; padding:8px; text-align:left;">'
    ).replace(
        '<td>',
        '<td style="padding:6px 8px; border-bottom:1px solid #eee;">'
    )
