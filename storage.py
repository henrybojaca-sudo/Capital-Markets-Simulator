"""
Storage module - usa Google Sheets como base de datos persistente
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

from tickers import INITIAL_CAPITAL

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

TAB_GROUPS = "Groups"
TAB_PORTFOLIOS = "Portfolios"
TAB_CASH = "Cash"
TAB_TRADES = "Trades"


@st.cache_resource(ttl=3600)
def _get_gsheet_client():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def _get_sheet():
    client = _get_gsheet_client()
    sheet_name = st.secrets.get("sheet_name", "Capital Markets DB")
    return client.open(sheet_name)


def _get_tab(tab_name: str):
    return _get_sheet().worksheet(tab_name)


def register_group(group_number: int, nickname: str, captain: str, password: str) -> bool:
    tab = _get_tab(TAB_GROUPS)
    existing = tab.col_values(1)
    if str(group_number) in existing[1:]:
        return False
    tab.append_row([
        group_number, nickname, captain, password,
        datetime.now().isoformat(),
    ], value_input_option="USER_ENTERED")
    cash_tab = _get_tab(TAB_CASH)
    cash_tab.append_row([group_number, INITIAL_CAPITAL], value_input_option="USER_ENTERED")
    return True


def authenticate(group_number: int, password: str) -> dict | None:
    tab = _get_tab(TAB_GROUPS)
    rows = tab.get_all_records()
    for r in rows:
        if str(r.get("group_number")) == str(group_number) and str(r.get("password")) == str(password):
            return {
                "group_number": int(r["group_number"]),
                "nickname": r["nickname"],
                "captain": r["captain"],
                "password": r["password"],
                "initial_capital": INITIAL_CAPITAL,
                "created_at": r.get("created_at", ""),
            }
    return None


def get_all_groups() -> dict:
    tab = _get_tab(TAB_GROUPS)
    rows = tab.get_all_records()
    result = {}
    for r in rows:
        key = str(r.get("group_number"))
        if not key or key == "":
            continue
        result[key] = {
            "group_number": int(r["group_number"]),
            "nickname": r["nickname"],
            "captain": r["captain"],
            "password": r["password"],
            "initial_capital": INITIAL_CAPITAL,
            "created_at": r.get("created_at", ""),
        }
    return result


def get_portfolio(group_number: int) -> dict:
    tab = _get_tab(TAB_PORTFOLIOS)
    rows = tab.get_all_records(value_render_option="UNFORMATTED_VALUE")
    portfolio = {}
    for r in rows:
        if str(r.get("group_number")) == str(group_number):
            ticker = r.get("ticker")
            qty = _safe_float(r.get("quantity"), 0.0)
            if ticker and qty > 0:
                portfolio[ticker] = portfolio.get(ticker, 0) + qty
    return portfolio


def save_portfolio(group_number: int, portfolio: dict):
    tab = _get_tab(TAB_PORTFOLIOS)
    all_rows = tab.get_all_values()
    rows_to_delete = sorted(
        [i for i, row in enumerate(all_rows[1:], start=2) if row and str(row[0]) == str(group_number)],
        reverse=True,
    )
    # Delete contiguous ranges in one call to avoid partial-delete corruption
    if rows_to_delete:
        # Group into contiguous ranges
        ranges = []
        start = end = rows_to_delete[0]
        for r in rows_to_delete[1:]:
            if r == end - 1:
                end = r
            else:
                ranges.append((start, end))
                start = end = r
        ranges.append((start, end))
        for top, bottom in ranges:
            tab.delete_rows(bottom, top)
    new_rows = [[group_number, ticker, qty] for ticker, qty in portfolio.items() if qty > 0.0001]
    if new_rows:
        tab.append_rows(new_rows, value_input_option="USER_ENTERED")


def _find_cash_row(group_number: int):
    tab = _get_tab(TAB_CASH)
    col = tab.col_values(1)
    for i, val in enumerate(col):
        if i == 0:
            continue
        if str(val) == str(group_number):
            return i + 1
    return None


def _safe_float(value, default=0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        # Strip currency symbols, spaces and thousands separators (comma-style)
        cleaned = str(value).strip().replace(",", "").replace("$", "").replace(" ", "")
        return float(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


def get_cash(group_number: int) -> float:
    tab = _get_tab(TAB_CASH)
    # UNFORMATTED_VALUE returns raw numbers instead of display strings
    rows = tab.get_all_records(value_render_option="UNFORMATTED_VALUE")
    for r in rows:
        if str(r.get("group_number")) == str(group_number):
            return _safe_float(r.get("cash"), float(INITIAL_CAPITAL))
    tab.append_row([group_number, INITIAL_CAPITAL], value_input_option="USER_ENTERED")
    return float(INITIAL_CAPITAL)


def set_cash(group_number: int, amount: float):
    tab = _get_tab(TAB_CASH)
    row = _find_cash_row(group_number)
    amount = max(0.0, float(amount))
    if row is None:
        tab.append_row([group_number, amount], value_input_option="USER_ENTERED")
    else:
        tab.update_cell(row, 2, amount)


def decrease_cash(group_number: int, amount: float) -> bool:
    current = get_cash(group_number)
    if amount > current:
        return False
    set_cash(group_number, current - amount)
    return True


def increase_cash(group_number: int, amount: float):
    current = get_cash(group_number)
    set_cash(group_number, current + amount)


def record_trade(group_number: int, trade: dict):
    tab = _get_tab(TAB_TRADES)
    tab.append_row([
        group_number,
        datetime.now().isoformat(),
        trade.get("action", ""),
        trade.get("ticker", ""),
        float(trade.get("quantity", 0)),
        float(trade.get("price", 0)),
        float(trade.get("amount", 0)),
    ], value_input_option="USER_ENTERED")


def get_trades(group_number: int) -> list:
    tab = _get_tab(TAB_TRADES)
    rows = tab.get_all_records(value_render_option="UNFORMATTED_VALUE")
    result = []
    for r in rows:
        if str(r.get("group_number")) == str(group_number):
            qty = _safe_float(r.get("quantity"), 0.0)
            price = _safe_float(r.get("price"), 0.0)
            stored_amount = r.get("amount")
            amount = _safe_float(stored_amount) if stored_amount not in (None, "") else qty * price
            result.append({
                "timestamp": r.get("timestamp", ""),
                "action": r.get("action", ""),
                "ticker": r.get("ticker", ""),
                "quantity": qty,
                "price": price,
                "amount": amount,
            })
    return result


def get_all_trades() -> dict:
    tab = _get_tab(TAB_TRADES)
    rows = tab.get_all_records(value_render_option="UNFORMATTED_VALUE")
    result = {}
    for r in rows:
        key = str(r.get("group_number"))
        if not key or key == "":
            continue
        if key not in result:
            result[key] = []
        qty = _safe_float(r.get("quantity"), 0.0)
        price = _safe_float(r.get("price"), 0.0)
        stored_amount = r.get("amount")
        amount = _safe_float(stored_amount) if stored_amount not in (None, "") else qty * price
        result[key].append({
            "timestamp": r.get("timestamp", ""),
            "action": r.get("action", ""),
            "ticker": r.get("ticker", ""),
            "quantity": qty,
            "price": price,
            "amount": amount,
        })
    return result
